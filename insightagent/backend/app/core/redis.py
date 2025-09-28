"""
Redis连接和配置管理
"""
import redis
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis管理器"""
    
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
    
    @property
    def client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        return self._redis_client
    
    def ping(self) -> bool:
        """检查Redis连接"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    def close(self):
        """关闭Redis连接"""
        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None


# 全局Redis管理器实例
redis_manager = RedisManager()


def get_redis_client() -> redis.Redis:
    """获取Redis客户端"""
    return redis_manager.client