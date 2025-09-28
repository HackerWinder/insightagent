"""
TaskManager服务的单元测试
"""
import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.services.task_manager import TaskManager
from app.models.task import Task, TaskLog, TaskStatus, LogLevel
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.factories import TaskFactory


class TestTaskManager:
    """TaskManager测试类"""
    
    @pytest.fixture
    def task_manager(self, db_session: Session):
        """创建TaskManager实例"""
        return TaskManager(db_session)
    
    @pytest.mark.asyncio
    async def test_create_task(self, task_manager: TaskManager, db_session: Session):
        """测试创建任务"""
        task_data = TaskCreate(product_name="Figma", user_id="test_user")
        user_id = "test_user"
        
        task = await task_manager.create_task(task_data, user_id)
        
        assert task.product_name == "Figma"
        assert task.user_id == user_id
        assert task.status == TaskStatus.QUEUED
        assert task.progress == 0.0
        assert task.id is not None
        
        # 验证任务已保存到数据库
        db_task = db_session.query(Task).filter(Task.id == task.id).first()
        assert db_task is not None
        assert db_task.product_name == "Figma"
        
        # 验证创建了日志
        logs = db_session.query(TaskLog).filter(TaskLog.task_id == task.id).all()
        assert len(logs) > 0
        assert logs[0].message.startswith("任务已创建")
    
    @pytest.mark.asyncio
    async def test_get_tasks_empty(self, task_manager: TaskManager):
        """测试获取空任务列表"""
        result = await task_manager.get_tasks("test_user")
        
        assert result["tasks"] == []
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 10
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_data(self, task_manager: TaskManager, db_session: Session):
        """测试获取任务列表（有数据）"""
        # 创建测试任务
        task1 = TaskFactory.create_task(product_name="Product1", user_id="test_user")
        task2 = TaskFactory.create_task(product_name="Product2", user_id="test_user")
        task3 = TaskFactory.create_task(product_name="Product3", user_id="other_user")
        
        db_session.add_all([task1, task2, task3])
        db_session.commit()
        
        # 获取test_user的任务
        result = await task_manager.get_tasks("test_user")
        
        assert result["total"] == 2
        assert len(result["tasks"]) == 2
        
        # 验证只返回当前用户的任务
        task_names = [task.product_name for task in result["tasks"]]
        assert "Product1" in task_names
        assert "Product2" in task_names
        assert "Product3" not in task_names
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_filters(self, task_manager: TaskManager, db_session: Session):
        """测试带筛选条件的任务查询"""
        # 创建不同状态的任务
        task1 = TaskFactory.create_task(
            product_name="CompletedTask", 
            user_id="test_user", 
            status=TaskStatus.COMPLETED
        )
        task2 = TaskFactory.create_task(
            product_name="RunningTask", 
            user_id="test_user", 
            status=TaskStatus.RUNNING
        )
        
        db_session.add_all([task1, task2])
        db_session.commit()
        
        # 按状态筛选
        result = await task_manager.get_tasks("test_user", status=TaskStatus.COMPLETED)
        
        assert result["total"] == 1
        assert result["tasks"][0].product_name == "CompletedTask"
        
        # 按产品名称筛选
        result = await task_manager.get_tasks("test_user", product_name="Running")
        
        assert result["total"] == 1
        assert result["tasks"][0].product_name == "RunningTask"
    
    @pytest.mark.asyncio
    async def test_get_tasks_pagination(self, task_manager: TaskManager, db_session: Session):
        """测试分页功能"""
        # 创建多个任务
        tasks = []
        for i in range(15):
            task = TaskFactory.create_task(
                product_name=f"Product{i}", 
                user_id="test_user"
            )
            tasks.append(task)
        
        db_session.add_all(tasks)
        db_session.commit()
        
        # 测试第一页
        result = await task_manager.get_tasks("test_user", page=1, page_size=10)
        
        assert result["total"] == 15
        assert len(result["tasks"]) == 10
        assert result["page"] == 1
        assert result["total_pages"] == 2
        
        # 测试第二页
        result = await task_manager.get_tasks("test_user", page=2, page_size=10)
        
        assert len(result["tasks"]) == 5
        assert result["page"] == 2
    
    @pytest.mark.asyncio
    async def test_get_task_by_id(self, task_manager: TaskManager, db_session: Session):
        """测试根据ID获取任务"""
        # 创建测试任务
        task = TaskFactory.create_task(product_name="TestProduct", user_id="test_user")
        db_session.add(task)
        db_session.commit()
        
        # 根据ID获取任务
        found_task = await task_manager.get_task_by_id(task.id, "test_user")
        
        assert found_task is not None
        assert found_task.id == task.id
        assert found_task.product_name == "TestProduct"
        
        # 测试不存在的任务
        fake_id = uuid.uuid4()
        not_found = await task_manager.get_task_by_id(fake_id, "test_user")
        assert not_found is None
        
        # 测试其他用户的任务
        other_user_task = await task_manager.get_task_by_id(task.id, "other_user")
        assert other_user_task is None
    
    @pytest.mark.asyncio
    async def test_update_task(self, task_manager: TaskManager, db_session: Session):
        """测试更新任务"""
        # 创建测试任务
        task = TaskFactory.create_task(product_name="TestProduct", user_id="test_user")
        db_session.add(task)
        db_session.commit()
        
        # 更新任务
        update_data = TaskUpdate(status=TaskStatus.RUNNING, progress=0.5)
        updated_task = await task_manager.update_task(task.id, update_data, "test_user")
        
        assert updated_task is not None
        assert updated_task.status == TaskStatus.RUNNING
        assert updated_task.progress == 0.5
        
        # 验证数据库中的任务已更新
        db_task = db_session.query(Task).filter(Task.id == task.id).first()
        assert db_task.status == TaskStatus.RUNNING
        assert db_task.progress == 0.5
        
        # 验证创建了状态变更日志
        logs = db_session.query(TaskLog).filter(TaskLog.task_id == task.id).all()
        status_change_logs = [log for log in logs if "状态从" in log.message]
        assert len(status_change_logs) > 0
    
    @pytest.mark.asyncio
    async def test_delete_task(self, task_manager: TaskManager, db_session: Session):
        """测试删除任务"""
        # 创建已完成的任务
        task = TaskFactory.create_task(
            product_name="CompletedTask", 
            user_id="test_user", 
            status=TaskStatus.COMPLETED
        )
        db_session.add(task)
        db_session.commit()
        
        # 删除任务
        success = await task_manager.delete_task(task.id, "test_user")
        
        assert success is True
        
        # 验证任务已从数据库删除
        db_task = db_session.query(Task).filter(Task.id == task.id).first()
        assert db_task is None
    
    @pytest.mark.asyncio
    async def test_delete_running_task(self, task_manager: TaskManager, db_session: Session):
        """测试删除运行中的任务（应该失败）"""
        # 创建运行中的任务
        task = TaskFactory.create_task(
            product_name="RunningTask", 
            user_id="test_user", 
            status=TaskStatus.RUNNING
        )
        db_session.add(task)
        db_session.commit()
        
        # 尝试删除运行中的任务
        success = await task_manager.delete_task(task.id, "test_user")
        
        assert success is False
        
        # 验证任务仍在数据库中
        db_task = db_session.query(Task).filter(Task.id == task.id).first()
        assert db_task is not None
    
    @pytest.mark.asyncio
    async def test_add_task_log(self, task_manager: TaskManager, db_session: Session):
        """测试添加任务日志"""
        # 创建测试任务
        task = TaskFactory.create_task(product_name="TestProduct", user_id="test_user")
        db_session.add(task)
        db_session.commit()
        
        # 添加日志
        log = await task_manager.add_task_log(
            task_id=task.id,
            level=LogLevel.INFO,
            message="Test log message",
            step="test_step"
        )
        
        assert log.task_id == task.id
        assert log.level == LogLevel.INFO
        assert log.message == "Test log message"
        assert log.step == "test_step"
        
        # 验证日志已保存到数据库
        db_log = db_session.query(TaskLog).filter(TaskLog.id == log.id).first()
        assert db_log is not None
        assert db_log.message == "Test log message"
    
    @pytest.mark.asyncio
    async def test_get_task_logs(self, task_manager: TaskManager, db_session: Session):
        """测试获取任务日志"""
        # 创建测试任务
        task = TaskFactory.create_task(product_name="TestProduct", user_id="test_user")
        db_session.add(task)
        db_session.commit()
        
        # 添加多个日志
        await task_manager.add_task_log(task.id, LogLevel.INFO, "Log 1")
        await task_manager.add_task_log(task.id, LogLevel.WARNING, "Log 2")
        await task_manager.add_task_log(task.id, LogLevel.ERROR, "Log 3")
        
        # 获取所有日志
        logs = await task_manager.get_task_logs(task.id, "test_user")
        
        assert len(logs) == 3
        
        # 验证日志按时间倒序排列
        assert logs[0].message == "Log 3"  # 最新的日志在前
        
        # 测试限制日志数量
        limited_logs = await task_manager.get_task_logs(task.id, "test_user", limit=2)
        assert len(limited_logs) == 2
    
    @pytest.mark.asyncio
    async def test_get_user_task_stats(self, task_manager: TaskManager, db_session: Session):
        """测试获取用户任务统计"""
        # 创建不同状态的任务
        tasks = [
            TaskFactory.create_task(user_id="test_user", status=TaskStatus.QUEUED),
            TaskFactory.create_task(user_id="test_user", status=TaskStatus.RUNNING),
            TaskFactory.create_task(user_id="test_user", status=TaskStatus.COMPLETED),
            TaskFactory.create_task(user_id="test_user", status=TaskStatus.COMPLETED),
            TaskFactory.create_task(user_id="test_user", status=TaskStatus.FAILED),
        ]
        
        db_session.add_all(tasks)
        db_session.commit()
        
        # 获取统计信息
        stats = await task_manager.get_user_task_stats("test_user")
        
        assert stats["total"] == 5
        assert stats["queued"] == 1
        assert stats["running"] == 1
        assert stats["completed"] == 2
        assert stats["failed"] == 1
        assert "last_task_created" in stats
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, task_manager: TaskManager, db_session: Session):
        """测试取消任务"""
        # 创建运行中的任务
        task = TaskFactory.create_task(
            product_name="RunningTask", 
            user_id="test_user", 
            status=TaskStatus.RUNNING
        )
        db_session.add(task)
        db_session.commit()
        
        # 取消任务
        success = await task_manager.cancel_task(task.id, "test_user")
        
        assert success is True
        
        # 验证任务状态已更新
        db_task = db_session.query(Task).filter(Task.id == task.id).first()
        assert db_task.status == TaskStatus.FAILED
        assert "取消" in db_task.error_message
        
        # 验证创建了取消日志
        logs = db_session.query(TaskLog).filter(TaskLog.task_id == task.id).all()
        cancel_logs = [log for log in logs if "取消" in log.message]
        assert len(cancel_logs) > 0
    
    @pytest.mark.asyncio
    async def test_retry_task(self, task_manager: TaskManager, db_session: Session):
        """测试重试任务"""
        # 创建失败的任务
        task = TaskFactory.create_task(
            product_name="FailedTask", 
            user_id="test_user", 
            status=TaskStatus.FAILED,
            error_message="Previous error"
        )
        db_session.add(task)
        db_session.commit()
        
        # 重试任务
        success = await task_manager.retry_task(task.id, "test_user")
        
        assert success is True
        
        # 验证任务状态已重置
        db_task = db_session.query(Task).filter(Task.id == task.id).first()
        assert db_task.status == TaskStatus.QUEUED
        assert db_task.progress == 0.0
        assert db_task.error_message is None
        
        # 验证创建了重试日志
        logs = db_session.query(TaskLog).filter(TaskLog.task_id == task.id).all()
        retry_logs = [log for log in logs if "重新排队" in log.message]
        assert len(retry_logs) > 0