"""
后台工作进程，处理队列中的任务
"""
import asyncio
import logging
import signal
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.database import SessionLocal
from app.services.queue_manager import task_queue
from app.services.task_manager import TaskManager
from app.services.agent_executor import agent_executor_service
from app.models.task import TaskStatus
from app.schemas.task import TaskUpdate

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TaskWorker:
    """任务工作进程"""
    
    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.running = False
        self.current_task = None
        
    async def start(self):
        """启动工作进程"""
        logger.info(f"Starting worker {self.worker_id}")
        self.running = True
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            await self._work_loop()
        except Exception as e:
            logger.error(f"Worker {self.worker_id} crashed: {e}")
        finally:
            await self._cleanup()
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"Worker {self.worker_id} received signal {signum}, shutting down...")
        self.running = False
    
    async def _work_loop(self):
        """主工作循环"""
        while self.running:
            try:
                # 从队列获取任务
                task_message = await task_queue.dequeue_task(self.worker_id, timeout=10)
                
                if not task_message:
                    # 没有任务，继续等待
                    continue
                
                self.current_task = task_message
                logger.info(f"Worker {self.worker_id} processing task {task_message['task_id']}")
                
                # 处理任务
                await self._process_task(task_message)
                
            except Exception as e:
                logger.error(f"Error in work loop: {e}")
                if self.current_task:
                    await self._handle_task_failure(self.current_task, str(e))
                
                # 短暂等待后继续
                await asyncio.sleep(5)
            finally:
                self.current_task = None
    
    async def _process_task(self, task_message: dict):
        """
        处理单个任务
        
        Args:
            task_message: 任务消息
        """
        task_id = task_message["task_id"]
        task_data = task_message["data"]
        
        try:
            # 创建数据库会话
            db = SessionLocal()
            task_manager = TaskManager(db)
            
            try:
                # 更新任务状态为运行中
                await task_manager.update_task(
                    task_id=uuid.UUID(task_id),
                    task_update=TaskUpdate(
                        status=TaskStatus.RUNNING,
                        progress=0.0
                    ),
                    user_id=task_data["user_id"]
                )
                
                # 执行Agent分析
                result = await agent_executor_service.execute_task(
                    task_id=task_id,
                    user_id=task_data["user_id"],
                    product_name=task_data["product_name"],
                    task_manager=task_manager
                )
                
                # 保存分析结果到数据库
                await self._save_analysis_result(task_manager, task_id, result)
                
                # 更新任务状态为完成
                await task_manager.update_task(
                    task_id=uuid.UUID(task_id),
                    task_update=TaskUpdate(
                        status=TaskStatus.COMPLETED,
                        progress=1.0
                    ),
                    user_id=task_data["user_id"]
                )
                
                # 标记任务完成
                await task_queue.complete_task(task_id, self.worker_id)
                
                logger.info(f"Task {task_id} completed successfully")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Task {task_id} processing failed: {e}")
            await self._handle_task_failure(task_message, str(e))
    
    async def _save_analysis_result(self, task_manager: TaskManager, task_id: str, result: dict):
        """
        保存分析结果到数据库
        
        Args:
            task_manager: 任务管理器
            task_id: 任务ID
            result: 分析结果
        """
        try:
            from app.models.task import AnalysisResult
            
            # 提取关键信息
            agent_output = result.get("agent_output", "")
            
            # 简单的结果解析（实际项目中可能需要更复杂的解析逻辑）
            analysis_data = {
                "sentiment_score": 0.0,  # 默认值，实际应从agent_output中解析
                "sentiment_distribution": {"positive": 0.5, "neutral": 0.3, "negative": 0.2},
                "top_topics": [{"topic": "general", "weight": 1.0}],
                "feature_requests": [],
                "key_insights": [agent_output[:500] + "..." if len(agent_output) > 500 else agent_output]
            }
            
            # 创建分析结果记录
            analysis_result = AnalysisResult(
                task_id=uuid.UUID(task_id),
                sentiment_score=analysis_data["sentiment_score"],
                sentiment_distribution=analysis_data["sentiment_distribution"],
                top_topics=analysis_data["top_topics"],
                feature_requests=analysis_data["feature_requests"],
                key_insights=analysis_data["key_insights"]
            )
            
            # 保存到数据库
            task_manager.db.add(analysis_result)
            task_manager.db.commit()
            
            logger.info(f"Analysis result saved for task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to save analysis result for task {task_id}: {e}")
            # 不抛出异常，因为任务本身可能已经成功
    
    async def _handle_task_failure(self, task_message: dict, error_message: str):
        """
        处理任务失败
        
        Args:
            task_message: 任务消息
            error_message: 错误信息
        """
        task_id = task_message["task_id"]
        
        try:
            # 创建数据库会话
            db = SessionLocal()
            task_manager = TaskManager(db)
            
            try:
                # 更新任务状态为失败
                await task_manager.update_task(
                    task_id=uuid.UUID(task_id),
                    task_update=TaskUpdate(
                        status=TaskStatus.FAILED,
                        error_message=error_message
                    ),
                    user_id=task_message["data"]["user_id"]
                )
                
            finally:
                db.close()
            
            # 标记队列中的任务失败
            await task_queue.fail_task(task_id, self.worker_id, error_message)
            
        except Exception as e:
            logger.error(f"Failed to handle task failure for {task_id}: {e}")
    
    async def _cleanup(self):
        """清理资源"""
        logger.info(f"Worker {self.worker_id} cleaning up...")
        
        # 如果有正在处理的任务，标记为失败
        if self.current_task:
            await self._handle_task_failure(
                self.current_task, 
                "Worker shutdown during task processing"
            )
        
        logger.info(f"Worker {self.worker_id} stopped")


async def main():
    """主函数"""
    worker = TaskWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())