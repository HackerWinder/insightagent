"""
队列管理服务
"""
import json
import uuid
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from enum import Enum

from app.core.redis import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class QueuePriority(str, Enum):
    """队列优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskQueue:
    """任务队列管理器"""
    
    # 队列名称前缀
    QUEUE_PREFIX = "insight_agent:queue"
    PROCESSING_PREFIX = "insight_agent:processing"
    FAILED_PREFIX = "insight_agent:failed"
    STATS_PREFIX = "insight_agent:stats"
    
    # 优先级权重
    PRIORITY_WEIGHTS = {
        QueuePriority.LOW: 1,
        QueuePriority.NORMAL: 2,
        QueuePriority.HIGH: 3,
        QueuePriority.URGENT: 4
    }
    
    def __init__(self):
        self.redis = get_redis_client()
    
    def _get_queue_key(self, priority: QueuePriority) -> str:
        """获取队列键名"""
        return f"{self.QUEUE_PREFIX}:{priority.value}"
    
    def _get_processing_key(self, worker_id: str) -> str:
        """获取处理中任务键名"""
        return f"{self.PROCESSING_PREFIX}:{worker_id}"
    
    def _get_failed_key(self) -> str:
        """获取失败任务键名"""
        return f"{self.FAILED_PREFIX}:tasks"
    
    def _get_stats_key(self) -> str:
        """获取统计信息键名"""
        return f"{self.STATS_PREFIX}:counters"
    
    async def enqueue_task(
        self,
        task_id: str,
        task_data: Dict[str, Any],
        priority: QueuePriority = QueuePriority.NORMAL,
        delay_seconds: int = 0
    ) -> bool:
        """
        将任务加入队列
        
        Args:
            task_id: 任务ID
            task_data: 任务数据
            priority: 任务优先级
            delay_seconds: 延迟执行秒数
            
        Returns:
            是否成功加入队列
        """
        try:
            # 构建任务消息
            message = {
                "task_id": task_id,
                "data": task_data,
                "priority": priority.value,
                "enqueued_at": datetime.now(timezone.utc).isoformat(),
                "attempts": 0,
                "max_attempts": 3
            }
            
            # 如果有延迟，使用延迟队列
            if delay_seconds > 0:
                execute_at = time.time() + delay_seconds
                self.redis.zadd(
                    f"{self.QUEUE_PREFIX}:delayed",
                    {json.dumps(message): execute_at}
                )
            else:
                # 直接加入优先级队列
                queue_key = self._get_queue_key(priority)
                self.redis.lpush(queue_key, json.dumps(message))
            
            # 更新统计信息
            self._increment_stat("enqueued")
            
            logger.info(f"Task {task_id} enqueued with priority {priority.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_id}: {e}")
            return False
    
    async def dequeue_task(self, worker_id: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        从队列中取出任务
        
        Args:
            worker_id: 工作进程ID
            timeout: 阻塞超时时间（秒）
            
        Returns:
            任务数据或None
        """
        try:
            # 首先处理延迟队列
            await self._process_delayed_tasks()
            
            # 按优先级顺序检查队列
            queue_keys = []
            for priority in sorted(QueuePriority, key=lambda p: self.PRIORITY_WEIGHTS[p], reverse=True):
                queue_key = self._get_queue_key(priority)
                queue_keys.append(queue_key)
            
            # 使用BRPOP从多个队列中取任务
            result = self.redis.brpop(queue_keys, timeout=timeout)
            
            if not result:
                return None
            
            queue_key, message_json = result
            message = json.loads(message_json)
            
            # 将任务移到处理中队列
            processing_key = self._get_processing_key(worker_id)
            processing_data = {
                **message,
                "worker_id": worker_id,
                "started_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.redis.setex(
                f"{processing_key}:{message['task_id']}",
                timedelta(minutes=settings.task_timeout_minutes),
                json.dumps(processing_data)
            )
            
            # 更新统计信息
            self._increment_stat("dequeued")
            
            logger.info(f"Task {message['task_id']} dequeued by worker {worker_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to dequeue task for worker {worker_id}: {e}")
            return None
    
    async def complete_task(self, task_id: str, worker_id: str) -> bool:
        """
        标记任务完成
        
        Args:
            task_id: 任务ID
            worker_id: 工作进程ID
            
        Returns:
            是否成功标记完成
        """
        try:
            # 从处理中队列移除任务
            processing_key = f"{self._get_processing_key(worker_id)}:{task_id}"
            deleted = self.redis.delete(processing_key)
            
            if deleted:
                # 更新统计信息
                self._increment_stat("completed")
                logger.info(f"Task {task_id} completed by worker {worker_id}")
                return True
            else:
                logger.warning(f"Task {task_id} not found in processing queue")
                return False
                
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
            return False
    
    async def fail_task(
        self,
        task_id: str,
        worker_id: str,
        error_message: str,
        retry: bool = True
    ) -> bool:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            worker_id: 工作进程ID
            error_message: 错误信息
            retry: 是否重试
            
        Returns:
            是否成功处理失败
        """
        try:
            # 从处理中队列获取任务
            processing_key = f"{self._get_processing_key(worker_id)}:{task_id}"
            task_data = self.redis.get(processing_key)
            
            if not task_data:
                logger.warning(f"Task {task_id} not found in processing queue")
                return False
            
            message = json.loads(task_data)
            message["attempts"] += 1
            message["last_error"] = error_message
            message["failed_at"] = datetime.now(timezone.utc).isoformat()
            
            # 删除处理中的任务
            self.redis.delete(processing_key)
            
            # 检查是否需要重试
            if retry and message["attempts"] < message["max_attempts"]:
                # 重新加入队列，使用指数退避延迟
                delay_seconds = min(300, 2 ** message["attempts"] * 10)  # 最大5分钟
                
                await self.enqueue_task(
                    task_id=task_id,
                    task_data=message["data"],
                    priority=QueuePriority(message["priority"]),
                    delay_seconds=delay_seconds
                )
                
                logger.info(f"Task {task_id} requeued for retry (attempt {message['attempts']})")
            else:
                # 移到失败队列
                failed_key = self._get_failed_key()
                self.redis.lpush(failed_key, json.dumps(message))
                
                # 更新统计信息
                self._increment_stat("failed")
                
                logger.error(f"Task {task_id} failed permanently: {error_message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle task failure {task_id}: {e}")
            return False
    
    async def _process_delayed_tasks(self):
        """处理延迟任务"""
        try:
            current_time = time.time()
            delayed_key = f"{self.QUEUE_PREFIX}:delayed"
            
            # 获取到期的延迟任务
            ready_tasks = self.redis.zrangebyscore(
                delayed_key, 0, current_time, withscores=True
            )
            
            for task_json, score in ready_tasks:
                try:
                    message = json.loads(task_json)
                    priority = QueuePriority(message["priority"])
                    
                    # 移到对应优先级队列
                    queue_key = self._get_queue_key(priority)
                    self.redis.lpush(queue_key, task_json)
                    
                    # 从延迟队列移除
                    self.redis.zrem(delayed_key, task_json)
                    
                    logger.info(f"Delayed task {message['task_id']} moved to queue")
                    
                except Exception as e:
                    logger.error(f"Failed to process delayed task: {e}")
                    # 从延迟队列移除有问题的任务
                    self.redis.zrem(delayed_key, task_json)
                    
        except Exception as e:
            logger.error(f"Failed to process delayed tasks: {e}")
    
    def _increment_stat(self, stat_name: str):
        """增加统计计数"""
        try:
            stats_key = self._get_stats_key()
            self.redis.hincrby(stats_key, stat_name, 1)
            
            # 设置过期时间（7天）
            self.redis.expire(stats_key, 7 * 24 * 3600)
            
        except Exception as e:
            logger.error(f"Failed to increment stat {stat_name}: {e}")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        try:
            stats = {}
            
            # 获取各优先级队列长度
            for priority in QueuePriority:
                queue_key = self._get_queue_key(priority)
                length = self.redis.llen(queue_key)
                stats[f"queue_{priority.value}"] = length
            
            # 获取延迟队列长度
            delayed_key = f"{self.QUEUE_PREFIX}:delayed"
            stats["queue_delayed"] = self.redis.zcard(delayed_key)
            
            # 获取失败队列长度
            failed_key = self._get_failed_key()
            stats["queue_failed"] = self.redis.llen(failed_key)
            
            # 获取处理中任务数量
            processing_pattern = f"{self.PROCESSING_PREFIX}:*"
            processing_keys = self.redis.keys(processing_pattern)
            stats["processing"] = len(processing_keys)
            
            # 获取统计计数
            stats_key = self._get_stats_key()
            counters = self.redis.hgetall(stats_key)
            for key, value in counters.items():
                stats[key] = int(value)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
    
    async def clear_failed_tasks(self) -> int:
        """清空失败任务队列"""
        try:
            failed_key = self._get_failed_key()
            count = self.redis.llen(failed_key)
            self.redis.delete(failed_key)
            
            logger.info(f"Cleared {count} failed tasks")
            return count
            
        except Exception as e:
            logger.error(f"Failed to clear failed tasks: {e}")
            return 0
    
    async def get_failed_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取失败的任务列表"""
        try:
            failed_key = self._get_failed_key()
            failed_tasks_json = self.redis.lrange(failed_key, 0, limit - 1)
            
            failed_tasks = []
            for task_json in failed_tasks_json:
                try:
                    task = json.loads(task_json)
                    failed_tasks.append(task)
                except json.JSONDecodeError:
                    continue
            
            return failed_tasks
            
        except Exception as e:
            logger.error(f"Failed to get failed tasks: {e}")
            return []
    
    async def cleanup_expired_processing_tasks(self):
        """清理过期的处理中任务"""
        try:
            processing_pattern = f"{self.PROCESSING_PREFIX}:*"
            processing_keys = self.redis.keys(processing_pattern)
            
            expired_count = 0
            for key in processing_keys:
                # Redis会自动清理过期的键，这里只是统计
                if not self.redis.exists(key):
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired processing tasks")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired processing tasks: {e}")


# 全局队列管理器实例
task_queue = TaskQueue()