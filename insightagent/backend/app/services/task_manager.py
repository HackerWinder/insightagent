"""
任务管理服务
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
import uuid
import logging
from datetime import datetime, timezone

from app.models.task import Task, TaskLog, TaskStatus, LogLevel
from app.schemas.task import TaskCreate, TaskUpdate
from app.core.config import settings
from app.services.queue_manager import task_queue, QueuePriority
from app.services.websocket_manager import websocket_notifier

logger = logging.getLogger(__name__)


class TaskManager:
    """任务管理器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_task(self, task_data: TaskCreate, user_id: str) -> Task:
        """
        创建新的分析任务
        
        Args:
            task_data: 任务创建数据
            user_id: 用户ID
            
        Returns:
            创建的任务对象
        """
        try:
            # 创建任务实例
            db_task = Task(
                user_id=user_id,
                product_name=task_data.product_name,
                status=TaskStatus.QUEUED,
                progress=0.0
            )
            
            # 保存到数据库
            self.db.add(db_task)
            self.db.commit()
            self.db.refresh(db_task)
            
            # 记录任务创建日志
            await self.add_task_log(
                task_id=db_task.id,
                level=LogLevel.INFO,
                message=f"任务已创建: {task_data.product_name}",
                step="task_creation"
            )
            
            # 将任务加入执行队列
            await self._enqueue_task_for_processing(db_task)
            
            logger.info(f"Task created: {db_task.id} for product: {task_data.product_name}")
            
            return db_task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create task: {e}")
            raise
    
    async def get_tasks(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        status: Optional[TaskStatus] = None,
        product_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户的任务列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            status: 任务状态筛选
            product_name: 产品名称筛选
            
        Returns:
            任务列表和分页信息
        """
        try:
            # 构建查询条件
            query = self.db.query(Task).filter(Task.user_id == user_id)
            
            if status:
                query = query.filter(Task.status == status)
            
            if product_name:
                query = query.filter(Task.product_name.ilike(f"%{product_name}%"))
            
            # 计算总数
            total = query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            tasks = query.order_by(desc(Task.created_at)).offset(offset).limit(page_size).all()
            
            return {
                "tasks": tasks,
                "total": total,
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"Failed to get tasks for user {user_id}: {e}")
            raise
    
    async def get_task_by_id(self, task_id: uuid.UUID, user_id: str) -> Optional[Task]:
        """
        根据ID获取任务（包含分析结果）
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            任务对象或None
        """
        try:
            task = self.db.query(Task).options(
                joinedload(Task.analysis_result)
            ).filter(
                and_(Task.id == task_id, Task.user_id == user_id)
            ).first()
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            raise
    
    async def update_task(
        self,
        task_id: uuid.UUID,
        task_update: TaskUpdate,
        user_id: str
    ) -> Optional[Task]:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            task_update: 更新数据
            user_id: 用户ID
            
        Returns:
            更新后的任务对象或None
        """
        try:
            # 查询任务
            task = await self.get_task_by_id(task_id, user_id)
            
            if not task:
                return None
            
            # 更新字段
            if task_update.status is not None:
                task.status = task_update.status
                
            if task_update.progress is not None:
                task.progress = task_update.progress
                
            if task_update.error_message is not None:
                task.error_message = task_update.error_message
            
            # 保存更改
            self.db.commit()
            self.db.refresh(task)
            
            # 记录更新日志
            await self.add_task_log(
                task_id=task_id,
                level=LogLevel.INFO,
                message=f"任务状态更新为: {task.status.value}",
                step="task_update"
            )
            
            logger.info(f"Task {task_id} updated successfully")
            
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update task {task_id}: {e}")
            raise
    
    async def delete_task(self, task_id: uuid.UUID, user_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            task = await self.get_task_by_id(task_id, user_id)
            
            if not task:
                return False
            
            # 删除任务（级联删除相关数据）
            self.db.delete(task)
            self.db.commit()
            
            logger.info(f"Task {task_id} deleted successfully")
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise
    
    async def add_task_log(
        self,
        task_id: uuid.UUID,
        level: LogLevel,
        message: str,
        step: Optional[str] = None
    ) -> TaskLog:
        """
        添加任务日志
        
        Args:
            task_id: 任务ID
            level: 日志级别
            message: 日志消息
            step: 执行步骤
            
        Returns:
            创建的日志对象
        """
        try:
            log = TaskLog(
                task_id=task_id,
                level=level,
                message=message,
                step=step
            )
            
            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)
            
            return log
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add task log: {e}")
            raise
    
    async def get_task_logs(
        self,
        task_id: uuid.UUID,
        user_id: str,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        获取任务日志
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            日志列表和分页信息
        """
        try:
            # 验证任务存在且属于用户
            task = await self.get_task_by_id(task_id, user_id)
            if not task:
                return {"logs": [], "total": 0, "page": page, "page_size": page_size}
            
            # 查询日志
            query = self.db.query(TaskLog).filter(TaskLog.task_id == task_id)
            total = query.count()
            
            offset = (page - 1) * page_size
            logs = query.order_by(desc(TaskLog.created_at)).offset(offset).limit(page_size).all()
            
            return {
                "logs": logs,
                "total": total,
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"Failed to get task logs for {task_id}: {e}")
            raise
    
    async def retry_task(self, task_id: uuid.UUID, user_id: str) -> Optional[Task]:
        """
        重试失败的任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            更新后的任务对象或None
        """
        try:
            task = await self.get_task_by_id(task_id, user_id)
            
            if not task:
                return None
            
            if task.status != TaskStatus.FAILED:
                raise ValueError("Only failed tasks can be retried")
            
            # 重置任务状态
            task.status = TaskStatus.QUEUED
            task.progress = 0.0
            task.error_message = None
            
            self.db.commit()
            self.db.refresh(task)
            
            # 重新加入队列
            await self._enqueue_task_for_processing(task)
            
            # 记录重试日志
            await self.add_task_log(
                task_id=task_id,
                level=LogLevel.INFO,
                message="任务已重新加入执行队列",
                step="task_retry"
            )
            
            logger.info(f"Task {task_id} retried successfully")
            
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to retry task {task_id}: {e}")
            raise
    
    async def get_task_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户任务统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        try:
            # 查询各种状态的任务数量
            total_tasks = self.db.query(Task).filter(Task.user_id == user_id).count()
            completed_tasks = self.db.query(Task).filter(
                and_(Task.user_id == user_id, Task.status == TaskStatus.COMPLETED)
            ).count()
            failed_tasks = self.db.query(Task).filter(
                and_(Task.user_id == user_id, Task.status == TaskStatus.FAILED)
            ).count()
            running_tasks = self.db.query(Task).filter(
                and_(Task.user_id == user_id, Task.status == TaskStatus.RUNNING)
            ).count()
            queued_tasks = self.db.query(Task).filter(
                and_(Task.user_id == user_id, Task.status == TaskStatus.QUEUED)
            ).count()
            
            # 计算成功率
            success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "running_tasks": running_tasks,
                "queued_tasks": queued_tasks,
                "success_rate": round(success_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get task stats for user {user_id}: {e}")
            raise
    
    async def _enqueue_task_for_processing(self, task: Task):
        """
        将任务加入处理队列
        
        Args:
            task: 任务对象
        """
        try:
            task_data = {
                "task_id": str(task.id),
                "user_id": task.user_id,
                "product_name": task.product_name,
                "created_at": task.created_at.isoformat()
            }
            
            # 加入队列
            await task_queue.enqueue_task(
                task_id=str(task.id),
                task_data=task_data,
                priority=QueuePriority.NORMAL
            )
            
            logger.info(f"Task {task.id} enqueued for processing")
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task.id}: {e}")
            raise
