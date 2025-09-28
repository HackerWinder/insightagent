"""
WebSocket管理器的单元测试
"""
import pytest
import json
import uuid
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

from app.services.websocket_manager import ConnectionManager, WebSocketNotifier


class TestConnectionManager:
    """ConnectionManager测试类"""
    
    @pytest.fixture
    def connection_manager(self):
        """创建ConnectionManager实例"""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """模拟WebSocket连接"""
        websocket = Mock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.ping = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect(self, connection_manager, mock_websocket):
        """测试建立WebSocket连接"""
        user_id = "test_user"
        task_id = "test_task"
        
        connection_id = await connection_manager.connect(mock_websocket, user_id, task_id)
        
        # 验证连接已建立
        assert connection_id in connection_manager.active_connections
        assert connection_manager.active_connections[connection_id]["user_id"] == user_id
        assert connection_manager.active_connections[connection_id]["task_id"] == task_id
        
        # 验证用户连接映射
        assert user_id in connection_manager.user_connections
        assert connection_id in connection_manager.user_connections[user_id]
        
        # 验证任务连接映射
        assert task_id in connection_manager.task_connections
        assert connection_id in connection_manager.task_connections[task_id]
        
        # 验证WebSocket方法被调用
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_without_task(self, connection_manager, mock_websocket):
        """测试不指定任务的连接"""
        user_id = "test_user"
        
        connection_id = await connection_manager.connect(mock_websocket, user_id)
        
        # 验证连接已建立
        assert connection_id in connection_manager.active_connections
        assert connection_manager.active_connections[connection_id]["task_id"] is None
        
        # 验证用户连接映射
        assert user_id in connection_manager.user_connections
        assert connection_id in connection_manager.user_connections[user_id]
        
        # 验证没有任务连接映射
        assert len(connection_manager.task_connections) == 0
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connection_manager, mock_websocket):
        """测试断开WebSocket连接"""
        user_id = "test_user"
        task_id = "test_task"
        
        # 先建立连接
        connection_id = await connection_manager.connect(mock_websocket, user_id, task_id)
        
        # 断开连接
        await connection_manager.disconnect(connection_id)
        
        # 验证连接已清理
        assert connection_id not in connection_manager.active_connections
        assert user_id not in connection_manager.user_connections
        assert task_id not in connection_manager.task_connections
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        """测试发送个人消息"""
        user_id = "test_user"
        connection_id = await connection_manager.connect(mock_websocket, user_id)
        
        message = {"type": "test", "content": "Hello"}
        await connection_manager.send_personal_message(connection_id, message)
        
        # 验证消息被发送
        mock_websocket.send_text.assert_called()
        sent_message = mock_websocket.send_text.call_args[0][0]
        assert json.loads(sent_message) == message
    
    @pytest.mark.asyncio
    async def test_send_personal_message_invalid_connection(self, connection_manager):
        """测试发送消息到无效连接"""
        fake_connection_id = str(uuid.uuid4())
        message = {"type": "test", "content": "Hello"}
        
        # 不应该抛出异常
        await connection_manager.send_personal_message(fake_connection_id, message)
    
    @pytest.mark.asyncio
    async def test_send_to_user(self, connection_manager):
        """测试发送消息给用户的所有连接"""
        user_id = "test_user"
        
        # 创建多个连接
        mock_websocket1 = Mock()
        mock_websocket1.accept = AsyncMock()
        mock_websocket1.send_text = AsyncMock()
        
        mock_websocket2 = Mock()
        mock_websocket2.accept = AsyncMock()
        mock_websocket2.send_text = AsyncMock()
        
        connection_id1 = await connection_manager.connect(mock_websocket1, user_id)
        connection_id2 = await connection_manager.connect(mock_websocket2, user_id)
        
        message = {"type": "test", "content": "Hello"}
        await connection_manager.send_to_user(user_id, message)
        
        # 验证消息发送到所有连接
        mock_websocket1.send_text.assert_called()
        mock_websocket2.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_send_to_task_subscribers(self, connection_manager):
        """测试发送消息给任务订阅者"""
        task_id = "test_task"
        
        # 创建订阅同一任务的多个连接
        mock_websocket1 = Mock()
        mock_websocket1.accept = AsyncMock()
        mock_websocket1.send_text = AsyncMock()
        
        mock_websocket2 = Mock()
        mock_websocket2.accept = AsyncMock()
        mock_websocket2.send_text = AsyncMock()
        
        connection_id1 = await connection_manager.connect(mock_websocket1, "user1", task_id)
        connection_id2 = await connection_manager.connect(mock_websocket2, "user2", task_id)
        
        message = {"type": "task_update", "content": "Task completed"}
        await connection_manager.send_to_task_subscribers(task_id, message)
        
        # 验证消息发送到所有订阅者
        mock_websocket1.send_text.assert_called()
        mock_websocket2.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_broadcast(self, connection_manager):
        """测试广播消息"""
        # 创建多个连接
        mock_websocket1 = Mock()
        mock_websocket1.accept = AsyncMock()
        mock_websocket1.send_text = AsyncMock()
        
        mock_websocket2 = Mock()
        mock_websocket2.accept = AsyncMock()
        mock_websocket2.send_text = AsyncMock()
        
        await connection_manager.connect(mock_websocket1, "user1")
        await connection_manager.connect(mock_websocket2, "user2")
        
        message = {"type": "broadcast", "content": "System message"}
        await connection_manager.broadcast(message)
        
        # 验证消息广播到所有连接
        mock_websocket1.send_text.assert_called()
        mock_websocket2.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_ping_message(self, connection_manager, mock_websocket):
        """测试处理ping消息"""
        user_id = "test_user"
        connection_id = await connection_manager.connect(mock_websocket, user_id)
        
        ping_message = json.dumps({"type": "ping"})
        await connection_manager.handle_message(connection_id, ping_message)
        
        # 验证发送了pong响应
        mock_websocket.send_text.assert_called()
        # 获取最后一次调用的参数
        last_call_args = mock_websocket.send_text.call_args_list[-1][0][0]
        response = json.loads(last_call_args)
        assert response["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_task_message(self, connection_manager, mock_websocket):
        """测试处理任务订阅消息"""
        user_id = "test_user"
        task_id = "test_task"
        connection_id = await connection_manager.connect(mock_websocket, user_id)
        
        subscribe_message = json.dumps({
            "type": "subscribe_task",
            "task_id": task_id
        })
        await connection_manager.handle_message(connection_id, subscribe_message)
        
        # 验证任务订阅
        assert task_id in connection_manager.task_connections
        assert connection_id in connection_manager.task_connections[task_id]
        
        # 验证发送了订阅确认
        mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_invalid_json_message(self, connection_manager, mock_websocket):
        """测试处理无效JSON消息"""
        user_id = "test_user"
        connection_id = await connection_manager.connect(mock_websocket, user_id)
        
        invalid_message = "invalid json"
        
        # 不应该抛出异常
        await connection_manager.handle_message(connection_id, invalid_message)
    
    @pytest.mark.asyncio
    async def test_subscribe_to_task(self, connection_manager, mock_websocket):
        """测试订阅任务"""
        user_id = "test_user"
        task_id = "test_task"
        connection_id = await connection_manager.connect(mock_websocket, user_id)
        
        await connection_manager.subscribe_to_task(connection_id, task_id)
        
        # 验证订阅成功
        assert task_id in connection_manager.task_connections
        assert connection_id in connection_manager.task_connections[task_id]
        assert connection_manager.active_connections[connection_id]["task_id"] == task_id
        
        # 验证发送了确认消息
        mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_unsubscribe_from_task(self, connection_manager, mock_websocket):
        """测试取消订阅任务"""
        user_id = "test_user"
        task_id = "test_task"
        connection_id = await connection_manager.connect(mock_websocket, user_id, task_id)
        
        await connection_manager.unsubscribe_from_task(connection_id, task_id)
        
        # 验证取消订阅成功
        assert task_id not in connection_manager.task_connections
        assert connection_manager.active_connections[connection_id]["task_id"] is None
        
        # 验证发送了确认消息
        mock_websocket.send_text.assert_called()
    
    def test_get_connection_stats(self, connection_manager):
        """测试获取连接统计"""
        # 手动添加一些连接数据进行测试
        connection_manager.active_connections = {
            "conn1": {"user_id": "user1", "task_id": "task1"},
            "conn2": {"user_id": "user1", "task_id": "task2"},
            "conn3": {"user_id": "user2", "task_id": "task1"}
        }
        connection_manager.user_connections = {
            "user1": ["conn1", "conn2"],
            "user2": ["conn3"]
        }
        connection_manager.task_connections = {
            "task1": ["conn1", "conn3"],
            "task2": ["conn2"]
        }
        
        stats = connection_manager.get_connection_stats()
        
        assert stats["total_connections"] == 3
        assert stats["users_connected"] == 2
        assert stats["tasks_subscribed"] == 2
        assert stats["connections_by_user"]["user1"] == 2
        assert stats["connections_by_user"]["user2"] == 1


class TestWebSocketNotifier:
    """WebSocketNotifier测试类"""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """模拟ConnectionManager"""
        manager = Mock()
        manager.send_to_task_subscribers = AsyncMock()
        manager.send_to_user = AsyncMock()
        manager.broadcast = AsyncMock()
        return manager
    
    @pytest.fixture
    def websocket_notifier(self, mock_connection_manager):
        """创建WebSocketNotifier实例"""
        return WebSocketNotifier(mock_connection_manager)
    
    @pytest.mark.asyncio
    async def test_notify_task_status_change(self, websocket_notifier, mock_connection_manager):
        """测试任务状态变更通知"""
        task_id = "test_task"
        user_id = "test_user"
        status = "RUNNING"
        progress = 0.5
        message = "Task is running"
        
        await websocket_notifier.notify_task_status_change(
            task_id, user_id, status, progress, message
        )
        
        # 验证发送了任务订阅者通知
        mock_connection_manager.send_to_task_subscribers.assert_called_once()
        call_args = mock_connection_manager.send_to_task_subscribers.call_args
        assert call_args[0][0] == task_id
        notification = call_args[0][1]
        assert notification["type"] == "task_status_update"
        assert notification["task_id"] == task_id
        assert notification["status"] == status
        assert notification["progress"] == progress
        assert notification["message"] == message
        
        # 验证发送了用户通知
        mock_connection_manager.send_to_user.assert_called_once()
        user_call_args = mock_connection_manager.send_to_user.call_args
        assert user_call_args[0][0] == user_id
    
    @pytest.mark.asyncio
    async def test_notify_task_log(self, websocket_notifier, mock_connection_manager):
        """测试任务日志通知"""
        task_id = "test_task"
        user_id = "test_user"
        level = "INFO"
        message = "Task log message"
        step = "data_collection"
        
        await websocket_notifier.notify_task_log(
            task_id, user_id, level, message, step
        )
        
        # 验证发送了任务订阅者通知
        mock_connection_manager.send_to_task_subscribers.assert_called_once()
        call_args = mock_connection_manager.send_to_task_subscribers.call_args
        assert call_args[0][0] == task_id
        notification = call_args[0][1]
        assert notification["type"] == "task_log"
        assert notification["task_id"] == task_id
        assert notification["level"] == level
        assert notification["message"] == message
        assert notification["step"] == step
    
    @pytest.mark.asyncio
    async def test_notify_system_message(self, websocket_notifier, mock_connection_manager):
        """测试系统消息通知"""
        message = "System maintenance"
        level = "warning"
        
        await websocket_notifier.notify_system_message(message, level)
        
        # 验证广播了系统消息
        mock_connection_manager.broadcast.assert_called_once()
        call_args = mock_connection_manager.broadcast.call_args
        notification = call_args[0][0]
        assert notification["type"] == "system_message"
        assert notification["level"] == level
        assert notification["message"] == message