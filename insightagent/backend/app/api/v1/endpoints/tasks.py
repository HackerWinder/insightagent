"""
任务管理相关端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.api.deps import get_db_session, get_current_user_id, validate_uuid
from app.schemas.task import (
    TaskCreate, TaskResponse, TaskUpdate, TaskListResponse
)
from app.models.task import Task, TaskStatus
from app.services.task_manager import TaskManager

router = APIRouter()


def get_task_manager(db: Session = Depends(get_db_session)) -> TaskManager:
    """获取任务管理器实例"""
    return TaskManager(db)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """创建新的分析任务"""
    try:
        task = await task_manager.create_task(task_data, current_user_id)
        return task.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    task_status: Optional[TaskStatus] = Query(None, description="按状态筛选"),
    product_name: Optional[str] = Query(None, description="按产品名称筛选")
):
    """获取用户的任务列表"""
    try:
        result = await task_manager.get_tasks(
            user_id=current_user_id,
            page=page,
            page_size=page_size,
            status=task_status,
            product_name=product_name
        )
        
        return TaskListResponse(
            tasks=[task.to_dict() for task in result["tasks"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks: {str(e)}"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取特定任务的详细信息"""
    
    # 验证UUID格式
    validate_uuid(task_id)
    
    try:
        task = await task_manager.get_task_by_id(uuid.UUID(task_id), current_user_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return task.to_dict()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}"
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """更新任务状态"""
    
    # 验证UUID格式
    validate_uuid(task_id)
    
    try:
        task = await task_manager.update_task(
            uuid.UUID(task_id), task_update, current_user_id
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return task.to_dict()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """删除任务"""
    
    # 验证UUID格式
    validate_uuid(task_id)
    
    try:
        success = await task_manager.delete_task(uuid.UUID(task_id), current_user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or cannot be deleted"
            )
        
        return None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id),
    limit: int = Query(100, ge=1, le=1000, description="日志条数限制")
):
    """获取任务执行日志"""
    
    # 验证UUID格式
    validate_uuid(task_id)
    
    try:
        logs = await task_manager.get_task_logs(
            uuid.UUID(task_id), current_user_id, limit
        )
        
        return {"logs": logs}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task logs: {str(e)}"
        )

@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """取消任务"""
    
    # 验证UUID格式
    validate_uuid(task_id)
    
    try:
        success = await task_manager.cancel_task(uuid.UUID(task_id), current_user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task not found or cannot be cancelled"
            )
        
        # 返回更新后的任务
        task = await task_manager.get_task_by_id(uuid.UUID(task_id), current_user_id)
        return task.to_dict()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """重试失败的任务"""
    
    # 验证UUID格式
    validate_uuid(task_id)
    
    try:
        success = await task_manager.retry_task(uuid.UUID(task_id), current_user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task not found or cannot be retried"
            )
        
        # 返回更新后的任务
        task = await task_manager.get_task_by_id(uuid.UUID(task_id), current_user_id)
        return task.to_dict()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry task: {str(e)}"
        )


@router.get("/stats/summary")
async def get_task_stats(
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取用户任务统计信息"""
    
    try:
        stats = await task_manager.get_user_task_stats(current_user_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task stats: {str(e)}"
        )