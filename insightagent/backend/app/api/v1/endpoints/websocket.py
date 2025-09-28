"""
WebSocket端点
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import logging

from app.services.websocket_manager import connection_manager
from app.api.deps import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="用户ID"),
    task_id: Optional[str] = Query(None, description="任务ID（可选）")
):
    """
    WebSocket连接端点
    
    Args:
        websocket: WebSocket连接
        user_id: 用户ID
        task_id: 任务ID（可选，用于订阅特定任务）
    """
    connection_id = None
    
    try:
        # 建立连接
        connection_id = await connection_manager.connect(websocket, user_id, task_id)
        
        # 保持连接并处理消息
        while True:
            try:
                # 接收消息
                message = await websocket.receive_text()
                
                # 处理消息
                await connection_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket message handling: {e}")
                # 发送错误消息给客户端
                try:
                    await connection_manager.send_personal_message(connection_id, {
                        "type": "error",
                        "message": "Message processing error"
                    })
                except:
                    # 如果发送错误消息也失败，说明连接已断开
                    break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # 清理连接
        if connection_id:
            await connection_manager.disconnect(connection_id)


@router.get("/stats")
async def get_websocket_stats():
    """获取WebSocket连接统计信息"""
    try:
        stats = connection_manager.get_connection_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Failed to get WebSocket stats: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/cleanup")
async def cleanup_stale_connections():
    """清理失效的WebSocket连接"""
    try:
        await connection_manager.cleanup_stale_connections()
        return {
            "status": "success",
            "message": "Stale connections cleaned up"
        }
    except Exception as e:
        logger.error(f"Failed to cleanup connections: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/broadcast")
async def broadcast_message(
    message: str,
    level: str = "info"
):
    """
    广播系统消息
    
    Args:
        message: 消息内容
        level: 消息级别
    """
    try:
        from app.services.websocket_manager import websocket_notifier
        
        await websocket_notifier.notify_system_message(message, level)
        
        return {
            "status": "success",
            "message": "Message broadcasted"
        }
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        return {
            "status": "error",
            "message": str(e)
        }