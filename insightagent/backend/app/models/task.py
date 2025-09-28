"""
任务相关数据模型
"""
import uuid
import enum
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


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


class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.QUEUED, index=True)
    progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    raw_data = relationship("RawData", back_populates="task", cascade="all, delete-orphan")
    analysis_result = relationship("AnalysisResult", back_populates="task", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, product_name='{self.product_name}', status='{self.status}')>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "id": str(self.id),
            "user_id": self.user_id,
            "product_name": self.product_name,
            "status": self.status.value,
            "progress": self.progress,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 包含分析结果
        if self.analysis_result:
            result["analysis_result"] = self.analysis_result.to_dict()
        
        return result


class TaskLog(Base):
    """任务日志模型"""
    __tablename__ = "task_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(Enum(LogLevel), nullable=False)
    message = Column(Text, nullable=False)
    step = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    task = relationship("Task", back_populates="logs")

    def __repr__(self):
        return f"<TaskLog(id={self.id}, task_id={self.task_id}, level='{self.level}')>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "level": self.level.value,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "step": self.step,
        }


class RawData(Base):
    """原始数据模型"""
    __tablename__ = "raw_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    task = relationship("Task", back_populates="raw_data")

    def __repr__(self):
        return f"<RawData(id={self.id}, task_id={self.task_id}, source='{self.source}')>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "source": self.source,
            "data": self.data,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
        }


class AnalysisResult(Base):
    """分析结果模型"""
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_distribution = Column(JSONB, nullable=True)
    top_topics = Column(JSONB, nullable=True)
    feature_requests = Column(JSONB, nullable=True)
    key_insights = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    task = relationship("Task", back_populates="analysis_result")

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, task_id={self.task_id})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "sentiment_score": self.sentiment_score,
            "sentiment_distribution": self.sentiment_distribution,
            "top_topics": self.top_topics,
            "feature_requests": self.feature_requests,
            "key_insights": self.key_insights,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
