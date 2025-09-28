"""
API v1版本路由
"""
from fastapi import APIRouter

from .endpoints import tasks, health, queue, websocket, tools, agent, reports, monitoring

api_router = APIRouter(prefix="/v1")

# 包含各个端点路由
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(queue.router, prefix="/queue", tags=["Queue"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
api_router.include_router(tools.router, prefix="/tools", tags=["Tools"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])