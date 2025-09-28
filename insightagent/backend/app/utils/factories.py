"""
测试数据工厂类
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.models.task import Task, TaskLog, RawData, AnalysisResult, TaskStatus, LogLevel


class TaskFactory:
    """任务模型工厂"""
    
    @staticmethod
    def create_task(
        product_name: str = "TestProduct",
        user_id: str = "test_user",
        status: TaskStatus = TaskStatus.QUEUED,
        progress: float = 0.0,
        error_message: Optional[str] = None
    ) -> Task:
        """创建测试任务"""
        return Task(
            id=uuid.uuid4(),
            user_id=user_id,
            product_name=product_name,
            status=status,
            progress=progress,
            error_message=error_message,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @staticmethod
    def create_task_dict(
        product_name: str = "TestProduct",
        user_id: str = "test_user",
        status: str = "QUEUED",
        progress: float = 0.0,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建任务字典数据"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "product_name": product_name,
            "status": status,
            "progress": progress,
            "error_message": error_message,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }


class TaskLogFactory:
    """任务日志工厂"""
    
    @staticmethod
    def create_log(
        task_id: uuid.UUID,
        level: LogLevel = LogLevel.INFO,
        message: str = "Test log message",
        step: Optional[str] = None
    ) -> TaskLog:
        """创建测试日志"""
        return TaskLog(
            id=uuid.uuid4(),
            task_id=task_id,
            timestamp=datetime.now(timezone.utc),
            level=level,
            message=message,
            step=step
        )
    
    @staticmethod
    def create_log_dict(
        task_id: str,
        level: str = "INFO",
        message: str = "Test log message",
        step: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建日志字典数据"""
        return {
            "id": str(uuid.uuid4()),
            "task_id": task_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "step": step
        }


class RawDataFactory:
    """原始数据工厂"""
    
    @staticmethod
    def create_raw_data(
        task_id: uuid.UUID,
        source: str = "reddit",
        data: Optional[Dict[str, Any]] = None
    ) -> RawData:
        """创建测试原始数据"""
        if data is None:
            data = {
                "posts": [
                    {
                        "title": "Great product!",
                        "content": "I love this product",
                        "score": 100,
                        "comments": 50
                    }
                ]
            }
        
        return RawData(
            id=uuid.uuid4(),
            task_id=task_id,
            source=source,
            data=data,
            collected_at=datetime.now(timezone.utc)
        )
    
    @staticmethod
    def create_reddit_data(task_id: uuid.UUID) -> RawData:
        """创建Reddit测试数据"""
        data = {
            "subreddit": "technology",
            "posts": [
                {
                    "id": "abc123",
                    "title": "New feature in Figma is amazing!",
                    "selftext": "The new auto-layout feature saves so much time",
                    "score": 150,
                    "num_comments": 25,
                    "created_utc": 1640995200,
                    "author": "designer123"
                },
                {
                    "id": "def456", 
                    "title": "Figma vs Sketch comparison",
                    "selftext": "After using both, I prefer Figma for collaboration",
                    "score": 89,
                    "num_comments": 12,
                    "created_utc": 1640908800,
                    "author": "ux_expert"
                }
            ]
        }
        return RawDataFactory.create_raw_data(task_id, "reddit", data)


class AnalysisResultFactory:
    """分析结果工厂"""
    
    @staticmethod
    def create_analysis_result(
        task_id: uuid.UUID,
        sentiment_score: float = 0.7,
        sentiment_distribution: Optional[Dict[str, float]] = None,
        top_topics: Optional[list] = None,
        feature_requests: Optional[list] = None,
        key_insights: Optional[list] = None
    ) -> AnalysisResult:
        """创建测试分析结果"""
        if sentiment_distribution is None:
            sentiment_distribution = {
                "positive": 0.6,
                "neutral": 0.3,
                "negative": 0.1
            }
        
        if top_topics is None:
            top_topics = [
                {"topic": "collaboration", "weight": 0.8},
                {"topic": "design tools", "weight": 0.6},
                {"topic": "user interface", "weight": 0.4}
            ]
        
        if feature_requests is None:
            feature_requests = [
                {
                    "feature": "Better mobile app",
                    "frequency": 15,
                    "sentiment": 0.8
                },
                {
                    "feature": "Offline mode",
                    "frequency": 12,
                    "sentiment": 0.7
                }
            ]
        
        if key_insights is None:
            key_insights = [
                "Users love the collaboration features",
                "Mobile experience needs improvement",
                "Strong preference over competitors"
            ]
        
        return AnalysisResult(
            id=uuid.uuid4(),
            task_id=task_id,
            sentiment_score=sentiment_score,
            sentiment_distribution=sentiment_distribution,
            top_topics=top_topics,
            feature_requests=feature_requests,
            key_insights=key_insights,
            created_at=datetime.now(timezone.utc)
        )