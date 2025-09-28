"""
队列管理器的单元测试
"""
import pytest
import json
import time
import asyncio
from unittest.mock import Mock, patch
import uuid

from app.services.queue_manager import TaskQueue, QueuePriority


class TestTaskQueue:
    """TaskQueue测试类"""
    
    @pytest.fixture
    def mock_redis(self):
        """模拟Redis客户端"""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.lpush.return_value = 1
        mock_redis.brpop.return_value = None
        mock_redis.llen.return_value = 0
        mock_redis.zcard.return_value = 0
        mock_redis.keys.return_value = []
        mock_redis.hgetall.return_value = {}
        mock_redis.delete.return_value = 1
        mock_redis.setex.return_value = True
        mock_redis.hincrby.return_value = 1
        mock_redis.expire.return_value = True
        mock_redis.zadd.return_value = 1
        mock_redis.zrangebyscore.return_value = []
        mock_redis.zrem.return_value = 1
        mock_redis.get.return_value = None
        mock_redis.exists.return_value = True
        mock_redis.lrange.return_value = []
        return mock_redis
    
    @pytest.fixture
    def task_queue(self, mock_redis):
        """创建TaskQueue实例"""
        with patch('app.services.queue_manager.get_redis_client', return_value=mock_redis):
            return TaskQueue()
    
    @pytest.mark.asyncio
    async def test_enqueue_task_normal_priority(self, task_queue, mock_redis):
        """测试正常优先级任务入队"""
        task_id = str(uuid.uuid4())
        task_data = {"product_name": "TestProduct"}
        
        result = await task_queue.enqueue_task(
            task_id=task_id,
            task_data=task_data,
            priority=QueuePriority.NORMAL
        )
        
        assert result is True
        
        # 验证调用了正确的Redis方法
        mock_redis.lpush.assert_called_once()
        call_args = mock_redis.lpush.call_args
        queue_key = call_args[0][0]
        message_json = call_args[0][1]
        
        assert "normal" in queue_key
        
        message = json.loads(message_json)
        assert message["task_id"] == task_id
        assert message["data"] == task_data
        assert message["priority"] == "normal"
        assert message["attempts"] == 0
    
    @pytest.mark.asyncio
    async def test_enqueue_task_with_delay(self, task_queue, mock_redis):
        """测试延迟任务入队"""
        task_id = str(uuid.uuid4())
        task_data = {"product_name": "DelayedTask"}
        
        result = await task_queue.enqueue_task(
            task_id=task_id,
            task_data=task_data,
            priority=QueuePriority.HIGH,
            delay_seconds=60
        )
        
        assert result is True
        
        # 验证调用了延迟队列方法
        mock_redis.zadd.assert_called_once()
        call_args = mock_redis.zadd.call_args
        delayed_key = call_args[0][0]
        
        assert "delayed" in delayed_key
    
    @pytest.mark.asyncio
    async def test_dequeue_task_empty_queue(self, task_queue, mock_redis):
        """测试从空队列取任务"""
        mock_redis.brpop.return_value = None
        
        result = await task_queue.dequeue_task("worker_1", timeout=1)
        
        assert result is None
        
        # 验证调用了正确的队列键
        mock_redis.brpop.assert_called_once()
        call_args = mock_redis.brpop.call_args
        queue_keys = call_args[0][0]
        
        # 验证按优先级顺序排列
        assert len(queue_keys) == 4  # 四个优先级
        assert "urgent" in queue_keys[0]  # 最高优先级在前
    
    @pytest.mark.asyncio
    async def test_dequeue_task_with_message(self, task_queue, mock_redis):
        """测试从队列取出任务"""
        task_id = str(uuid.uuid4())
        message = {
            "task_id": task_id,
            "data": {"product_name": "TestProduct"},
            "priority": "normal",
            "attempts": 0
        }
        
        mock_redis.brpop.return_value = ("queue:normal", json.dumps(message))
        
        result = await task_queue.dequeue_task("worker_1")
        
        assert result is not None
        assert result["task_id"] == task_id
        assert result["data"]["product_name"] == "TestProduct"
        
        # 验证任务被移到处理中队列
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_task(self, task_queue, mock_redis):
        """测试完成任务"""
        task_id = str(uuid.uuid4())
        worker_id = "worker_1"
        
        mock_redis.delete.return_value = 1  # 模拟成功删除
        
        result = await task_queue.complete_task(task_id, worker_id)
        
        assert result is True
        
        # 验证从处理中队列删除任务
        mock_redis.delete.assert_called_once()
        call_args = mock_redis.delete.call_args
        processing_key = call_args[0][0]
        
        assert worker_id in processing_key
        assert task_id in processing_key
    
    @pytest.mark.asyncio
    async def test_fail_task_with_retry(self, task_queue, mock_redis):
        """测试任务失败并重试"""
        task_id = str(uuid.uuid4())
        worker_id = "worker_1"
        error_message = "Test error"
        
        # 模拟处理中的任务数据
        processing_data = {
            "task_id": task_id,
            "data": {"product_name": "TestProduct"},
            "priority": "normal",
            "attempts": 0,
            "max_attempts": 3
        }
        
        mock_redis.get.return_value = json.dumps(processing_data)
        
        result = await task_queue.fail_task(task_id, worker_id, error_message, retry=True)
        
        assert result is True
        
        # 验证从处理中队列删除
        mock_redis.delete.assert_called_once()
        
        # 验证重新入队（通过zadd调用，因为有延迟）
        mock_redis.zadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fail_task_max_attempts(self, task_queue, mock_redis):
        """测试任务达到最大重试次数"""
        task_id = str(uuid.uuid4())
        worker_id = "worker_1"
        error_message = "Test error"
        
        # 模拟已达到最大重试次数的任务
        processing_data = {
            "task_id": task_id,
            "data": {"product_name": "TestProduct"},
            "priority": "normal",
            "attempts": 3,
            "max_attempts": 3
        }
        
        mock_redis.get.return_value = json.dumps(processing_data)
        
        result = await task_queue.fail_task(task_id, worker_id, error_message, retry=True)
        
        assert result is True
        
        # 验证任务被移到失败队列
        mock_redis.lpush.assert_called_once()
        call_args = mock_redis.lpush.call_args
        failed_key = call_args[0][0]
        
        assert "failed" in failed_key
    
    @pytest.mark.asyncio
    async def test_process_delayed_tasks(self, task_queue, mock_redis):
        """测试处理延迟任务"""
        # 模拟到期的延迟任务
        delayed_task = {
            "task_id": str(uuid.uuid4()),
            "data": {"product_name": "DelayedProduct"},
            "priority": "high"
        }
        
        current_time = time.time()
        mock_redis.zrangebyscore.return_value = [
            (json.dumps(delayed_task), current_time - 10)  # 已过期
        ]
        
        await task_queue._process_delayed_tasks()
        
        # 验证任务被移到正常队列
        mock_redis.lpush.assert_called_once()
        mock_redis.zrem.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_queue_stats(self, task_queue, mock_redis):
        """测试获取队列统计"""
        # 模拟各种统计数据
        mock_redis.llen.return_value = 5
        mock_redis.zcard.return_value = 2
        mock_redis.keys.return_value = ["processing:worker1:task1", "processing:worker2:task2"]
        mock_redis.hgetall.return_value = {
            "enqueued": "100",
            "dequeued": "95",
            "completed": "90",
            "failed": "5"
        }
        
        stats = await task_queue.get_queue_stats()
        
        assert "queue_low" in stats
        assert "queue_normal" in stats
        assert "queue_high" in stats
        assert "queue_urgent" in stats
        assert "queue_delayed" in stats
        assert "queue_failed" in stats
        assert "processing" in stats
        assert stats["enqueued"] == 100
        assert stats["completed"] == 90
    
    @pytest.mark.asyncio
    async def test_clear_failed_tasks(self, task_queue, mock_redis):
        """测试清空失败任务"""
        mock_redis.llen.return_value = 10
        
        result = await task_queue.clear_failed_tasks()
        
        assert result == 10
        
        # 验证删除失败队列
        mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_failed_tasks(self, task_queue, mock_redis):
        """测试获取失败任务列表"""
        failed_task = {
            "task_id": str(uuid.uuid4()),
            "data": {"product_name": "FailedProduct"},
            "error": "Test error"
        }
        
        mock_redis.lrange.return_value = [json.dumps(failed_task)]
        
        result = await task_queue.get_failed_tasks(limit=10)
        
        assert len(result) == 1
        assert result[0]["task_id"] == failed_task["task_id"]
        assert result[0]["data"]["product_name"] == "FailedProduct"
    
    def test_priority_weights(self, task_queue):
        """测试优先级权重"""
        assert task_queue.PRIORITY_WEIGHTS[QueuePriority.URGENT] > task_queue.PRIORITY_WEIGHTS[QueuePriority.HIGH]
        assert task_queue.PRIORITY_WEIGHTS[QueuePriority.HIGH] > task_queue.PRIORITY_WEIGHTS[QueuePriority.NORMAL]
        assert task_queue.PRIORITY_WEIGHTS[QueuePriority.NORMAL] > task_queue.PRIORITY_WEIGHTS[QueuePriority.LOW]
    
    def test_queue_key_generation(self, task_queue):
        """测试队列键名生成"""
        normal_key = task_queue._get_queue_key(QueuePriority.NORMAL)
        high_key = task_queue._get_queue_key(QueuePriority.HIGH)
        
        assert "normal" in normal_key
        assert "high" in high_key
        assert task_queue.QUEUE_PREFIX in normal_key
        assert task_queue.QUEUE_PREFIX in high_key
    
    @pytest.mark.asyncio
    async def test_enqueue_task_error_handling(self, task_queue, mock_redis):
        """测试入队错误处理"""
        mock_redis.lpush.side_effect = Exception("Redis error")
        
        result = await task_queue.enqueue_task(
            task_id="test_id",
            task_data={"test": "data"},
            priority=QueuePriority.NORMAL
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_dequeue_task_error_handling(self, task_queue, mock_redis):
        """测试出队错误处理"""
        mock_redis.brpop.side_effect = Exception("Redis error")
        
        result = await task_queue.dequeue_task("worker_1")
        
        assert result is None