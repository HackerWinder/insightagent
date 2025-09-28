"""
队列管理相关端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any

from app.api.deps import get_current_user_id
from app.services.queue_manager import task_queue
from app.services.task_manager import TaskManager
from app.api.deps import get_db_session
from sqlalchemy.orm import Session

router = APIRouter()


def get_task_manager(db: Session = Depends(get_db_session)) -> TaskManager:
    """获取任务管理器实例"""
    return TaskManager(db)


@router.get("/stats")
async def get_queue_stats(
    current_user_id: str = Depends(get_current_user_id)
):
    """获取队列统计信息"""
    try:
        stats = await task_queue.get_queue_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue stats: {str(e)}"
        )


@router.get("/failed")
async def get_failed_tasks(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取失败的任务列表"""
    try:
        failed_tasks = await task_queue.get_failed_tasks(limit)
        return {
            "status": "success",
            "data": failed_tasks,
            "count": len(failed_tasks)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get failed tasks: {str(e)}"
        )


@router.delete("/failed")
async def clear_failed_tasks(
    current_user_id: str = Depends(get_current_user_id)
):
    """清空失败任务队列"""
    try:
        cleared_count = await task_queue.clear_failed_tasks()
        return {
            "status": "success",
            "message": f"Cleared {cleared_count} failed tasks",
            "cleared_count": cleared_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear failed tasks: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_expired_tasks(
    current_user_id: str = Depends(get_current_user_id)
):
    """清理过期的处理中任务"""
    try:
        await task_queue.cleanup_expired_processing_tasks()
        return {
            "status": "success",
            "message": "Cleanup completed"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup expired tasks: {str(e)}"
        )


@router.get("/health")
async def queue_health_check():
    """队列健康检查"""
    try:
        from app.core.redis import redis_manager
        
        # 检查Redis连接
        redis_healthy = redis_manager.ping()
        
        if not redis_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis connection failed"
            )
        
        # 获取基本统计信息
        stats = await task_queue.get_queue_stats()
        
        return {
            "status": "healthy",
            "redis_connected": redis_healthy,
            "queue_stats": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Queue health check failed: {str(e)}"
        )