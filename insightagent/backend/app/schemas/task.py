"""
任务相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import enum


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class LogLevel(str, enum.Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class TaskCreate(BaseModel):
    """创建任务的请求模型"""
    product_name: str = Field(..., min_length=1, max_length=255, description="产品名称")

    class Config:
        schema_extra = {
            "example": {
                "product_name": "Figma"
            }
        }


class TaskUpdate(BaseModel):
    """更新任务的请求模型"""
    status: Optional[TaskStatus] = None
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    error_message: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "status": "RUNNING",
                "progress": 0.5,
                "error_message": None
            }
        }


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: UUID
    user_id: str
    product_name: str
    status: TaskStatus
    progress: float
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    analysis_result: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user123",
                "product_name": "Figma",
                "status": "RUNNING",
                "progress": 0.5,
                "error_message": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:30:00Z",
                "analysis_result": {
                    "sentiment_score": 0.7,
                    "sentiment_distribution": {"positive": 0.6, "neutral": 0.3, "negative": 0.1},
                    "key_insights": ["用户对产品整体满意"]
                }
            }
        }


class TaskLogCreate(BaseModel):
    """创建任务日志的请求模型"""
    level: LogLevel
    message: str = Field(..., min_length=1, max_length=1000)
    step: Optional[str] = Field(None, max_length=100)

    class Config:
        schema_extra = {
            "example": {
                "level": "INFO",
                "message": "任务开始执行",
                "step": "data_collection"
            }
        }


class TaskLogResponse(BaseModel):
    """任务日志响应模型"""
    id: UUID
    task_id: UUID
    level: LogLevel
    message: str
    step: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "level": "INFO",
                "message": "任务开始执行",
                "step": "data_collection",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class RawDataCreate(BaseModel):
    """创建原始数据的请求模型"""
    source: str = Field(..., min_length=1, max_length=100)
    data: Dict[str, Any]

    class Config:
        schema_extra = {
            "example": {
                "source": "reddit",
                "data": {
                    "posts": [
                        {
                            "title": "Great product!",
                            "content": "I love this tool"
                        }
                    ]
                }
            }
        }


class RawDataResponse(BaseModel):
    """原始数据响应模型"""
    id: UUID
    task_id: UUID
    source: str
    data: Dict[str, Any]
    collected_at: datetime

    class Config:
        from_attributes = True


class AnalysisResultCreate(BaseModel):
    """创建分析结果的请求模型"""
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    sentiment_distribution: Optional[Dict[str, float]] = None
    top_topics: Optional[List[Dict[str, Any]]] = None
    feature_requests: Optional[List[Dict[str, Any]]] = None
    key_insights: Optional[List[str]] = None


class AnalysisResultResponse(BaseModel):
    """分析结果响应模型"""
    id: UUID
    task_id: UUID
    sentiment_score: Optional[float]
    sentiment_distribution: Optional[Dict[str, float]]
    top_topics: Optional[List[Dict[str, Any]]]
    feature_requests: Optional[List[Dict[str, Any]]]
    key_insights: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int

    class Config:
        schema_extra = {
            "example": {
                "tasks": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "user123",
                        "product_name": "Figma",
                        "status": "COMPLETED",
                        "progress": 1.0,
                        "error_message": None,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T01:00:00Z",
                        "analysis_result": {
                            "sentiment_score": 0.7,
                            "key_insights": ["用户对产品整体满意"]
                        }
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }
