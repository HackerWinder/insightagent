"""
WebSocket连接管理服务
"""
import json
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import asyncio

from fastapi import WebSocket, WebSocketDisconnect
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接：{connection_id: {"websocket": WebSocket, "user_id": str, "task_id": str}}
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        # 用户连接映射：{user_id: [connection_ids]}
        self.user_connections: Dict[str, List[str]] = {}
        # 任务连接映射：{task_id: [connection_ids]}
        self.task_connections: Dict[str, List[str]] = {}
        self.redis = get_redis_client()
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        task_id: Optional[str] = None
    ) -> str:
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
            task_id: 任务ID（可选）
            
        Returns:
            连接ID
        """
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        
        # 存储连接信息
        self.active_connections[connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "task_id": task_id,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 更新用户连接映射
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        # 更新任务连接映射
        if task_id:
            if task_id not in self.task_connections:
                self.task_connections[task_id] = []
            self.task_connections[task_id].append(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        
        # 发送连接确认消息
        await self.send_personal_message(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "message": "WebSocket connection established"
        })
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        断开WebSocket连接
        
        Args:
            connection_id: 连接ID
        """
        if connection_id not in self.active_connections:
            return
        
        connection_info = self.active_connections[connection_id]
        user_id = connection_info["user_id"]
        task_id = connection_info.get("task_id")
        
        # 从活跃连接中移除
        del self.active_connections[connection_id]
        
        # 从用户连接映射中移除
        if user_id in self.user_connections:
            self.user_connections[user_id] = [
                cid for cid in self.user_connections[user_id] if cid != connection_id
            ]
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # 从任务连接映射中移除
        if task_id and task_id in self.task_connections:
            self.task_connections[task_id] = [
                cid for cid in self.task_connections[task_id] if cid != connection_id
            ]
            if not self.task_connections[task_id]:
                del self.task_connections[task_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """
        发送个人消息
        
        Args:
            connection_id: 连接ID
            message: 消息内容
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Connection {connection_id} not found")
            return
        
        try:
            websocket = self.active_connections[connection_id]["websocket"]
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            # 连接可能已断开，清理连接
            await self.disconnect(connection_id)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """
        发送消息给用户的所有连接
        
        Args:
            user_id: 用户ID
            message: 消息内容
        """
        if user_id not in self.user_connections:
            logger.debug(f"No active connections for user {user_id}")
            return
        
        # 获取用户的所有连接
        connection_ids = self.user_connections[user_id].copy()
        
        # 并发发送消息
        tasks = []
        for connection_id in connection_ids:
            tasks.append(self.send_personal_message(connection_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_to_task_subscribers(self, task_id: str, message: Dict[str, Any]):
        """
        发送消息给订阅特定任务的所有连接
        
        Args:
            task_id: 任务ID
            message: 消息内容
        """
        if task_id not in self.task_connections:
            logger.debug(f"No active connections for task {task_id}")
            return
        
        # 获取任务的所有连接
        connection_ids = self.task_connections[task_id].copy()
        
        # 并发发送消息
        tasks = []
        for connection_id in connection_ids:
            tasks.append(self.send_personal_message(connection_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        广播消息给所有连接
        
        Args:
            message: 消息内容
        """
        if not self.active_connections:
            return
        
        # 并发发送给所有连接
        tasks = []
        for connection_id in list(self.active_connections.keys()):
            tasks.append(self.send_personal_message(connection_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_message(self, connection_id: str, message: str):
        """
        处理接收到的WebSocket消息
        
        Args:
            connection_id: 连接ID
            message: 消息内容
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                # 心跳检测
                await self.send_personal_message(connection_id, {
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            elif message_type == "subscribe_task":
                # 订阅任务更新
                task_id = data.get("task_id")
                if task_id:
                    await self.subscribe_to_task(connection_id, task_id)
            
            elif message_type == "unsubscribe_task":
                # 取消订阅任务
                task_id = data.get("task_id")
                if task_id:
                    await self.unsubscribe_from_task(connection_id, task_id)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from {connection_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
    
    async def subscribe_to_task(self, connection_id: str, task_id: str):
        """
        订阅任务更新
        
        Args:
            connection_id: 连接ID
            task_id: 任务ID
        """
        if connection_id not in self.active_connections:
            return
        
        # 更新连接信息
        self.active_connections[connection_id]["task_id"] = task_id
        
        # 更新任务连接映射
        if task_id not in self.task_connections:
            self.task_connections[task_id] = []
        
        if connection_id not in self.task_connections[task_id]:
            self.task_connections[task_id].append(connection_id)
        
        # 发送订阅确认
        await self.send_personal_message(connection_id, {
            "type": "task_subscribed",
            "task_id": task_id,
            "message": f"Subscribed to task {task_id}"
        })
        
        logger.info(f"Connection {connection_id} subscribed to task {task_id}")
    
    async def unsubscribe_from_task(self, connection_id: str, task_id: str):
        """
        取消订阅任务
        
        Args:
            connection_id: 连接ID
            task_id: 任务ID
        """
        if connection_id not in self.active_connections:
            return
        
        # 从任务连接映射中移除
        if task_id in self.task_connections:
            self.task_connections[task_id] = [
                cid for cid in self.task_connections[task_id] if cid != connection_id
            ]
            if not self.task_connections[task_id]:
                del self.task_connections[task_id]
        
        # 更新连接信息
        if self.active_connections[connection_id].get("task_id") == task_id:
            self.active_connections[connection_id]["task_id"] = None
        
        # 发送取消订阅确认
        await self.send_personal_message(connection_id, {
            "type": "task_unsubscribed",
            "task_id": task_id,
            "message": f"Unsubscribed from task {task_id}"
        })
        
        logger.info(f"Connection {connection_id} unsubscribed from task {task_id}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息
        
        Returns:
            连接统计信息
        """
        return {
            "total_connections": len(self.active_connections),
            "users_connected": len(self.user_connections),
            "tasks_subscribed": len(self.task_connections),
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            }
        }
    
    async def cleanup_stale_connections(self):
        """清理失效的连接"""
        stale_connections = []
        
        for connection_id, connection_info in self.active_connections.items():
            try:
                websocket = connection_info["websocket"]
                # 尝试发送ping消息检测连接状态
                await websocket.ping()
            except Exception:
                stale_connections.append(connection_id)
        
        # 清理失效连接
        for connection_id in stale_connections:
            await self.disconnect(connection_id)
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")


# 全局连接管理器实例
connection_manager = ConnectionManager()


class WebSocketNotifier:
    """WebSocket通知服务"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def notify_task_status_change(
        self, 
        task_id: str, 
        user_id: str, 
        status: str, 
        progress: float = None,
        message: str = None
    ):
        """
        通知任务状态变更
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            status: 新状态
            progress: 进度（可选）
            message: 消息（可选）
        """
        notification = {
            "type": "task_status_update",
            "task_id": task_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if progress is not None:
            notification["progress"] = progress
        
        if message:
            notification["message"] = message
        
        # 发送给任务订阅者
        await self.connection_manager.send_to_task_subscribers(task_id, notification)
        
        # 发送给用户的所有连接
        await self.connection_manager.send_to_user(user_id, notification)
    
    async def notify_task_log(
        self, 
        task_id: str, 
        user_id: str, 
        level: str, 
        message: str, 
        step: str = None
    ):
        """
        通知任务日志
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            level: 日志级别
            message: 日志消息
            step: 执行步骤（可选）
        """
        notification = {
            "type": "task_log",
            "task_id": task_id,
            "level": level,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if step:
            notification["step"] = step
        
        # 发送给任务订阅者
        await self.connection_manager.send_to_task_subscribers(task_id, notification)
    
    async def notify_system_message(self, message: str, level: str = "info"):
        """
        发送系统消息
        
        Args:
            message: 消息内容
            level: 消息级别
        """
        notification = {
            "type": "system_message",
            "level": level,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 广播给所有连接
        await self.connection_manager.broadcast(notification)


# 全局通知服务实例
websocket_notifier = WebSocketNotifier(connection_manager)