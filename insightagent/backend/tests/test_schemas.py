"""
Pydantic schemas的单元测试
"""
import pytest
import uuid
from datetime import datetime, timezone

from app.schemas.task import (
    TaskCreate, TaskResponse, TaskUpdate, TaskLogCreate, TaskLogResponse,
    RawDataCreate, RawDataResponse, AnalysisResultCreate, AnalysisResultResponse
)
from app.models.task import TaskStatus, LogLevel
from app.utils.factories import TaskFactory


class TestTaskCreate:
    """任务创建schema测试"""
    
    def test_valid_task_create(self):
        """测试有效的任务创建数据"""
        data = {
            "product_name": "Figma",
            "user_id": "user123"
        }
        task_create = TaskCreate(**data)
        
        assert task_create.product_name == "Figma"
        assert task_create.user_id == "user123"
    
    def test_product_name_validation(self):
        """测试产品名称验证"""
        # 测试空字符串
        with pytest.raises(ValueError):
            TaskCreate(product_name="", user_id="user123")
        
        # 测试只有空格
        with pytest.raises(ValueError):
            TaskCreate(product_name="   ", user_id="user123")
        
        # 测试去除空格
        task_create = TaskCreate(product_name="  Figma  ", user_id="user123")
        assert task_create.product_name == "Figma"
    
    def test_product_name_length_validation(self):
        """测试产品名称长度验证"""
        # 测试超长名称
        long_name = "a" * 256
        with pytest.raises(ValueError):
            TaskCreate(product_name=long_name, user_id="user123")


class TestTaskUpdate:
    """任务更新schema测试"""
    
    def test_valid_task_update(self):
        """测试有效的任务更新数据"""
        data = {
            "status": TaskStatus.RUNNING,
            "progress": 0.5,
            "error_message": None
        }
        task_update = TaskUpdate(**data)
        
        assert task_update.status == TaskStatus.RUNNING
        assert task_update.progress == 0.5
        assert task_update.error_message is None
    
    def test_progress_validation(self):
        """测试进度验证"""
        # 测试负数进度
        with pytest.raises(ValueError):
            TaskUpdate(progress=-0.1)
        
        # 测试超过1的进度
        with pytest.raises(ValueError):
            TaskUpdate(progress=1.1)
        
        # 测试边界值
        task_update = TaskUpdate(progress=0.0)
        assert task_update.progress == 0.0
        
        task_update = TaskUpdate(progress=1.0)
        assert task_update.progress == 1.0
    
    def test_optional_fields(self):
        """测试可选字段"""
        task_update = TaskUpdate()
        
        assert task_update.status is None
        assert task_update.progress is None
        assert task_update.error_message is None


class TestTaskResponse:
    """任务响应schema测试"""
    
    def test_task_response_from_model(self):
        """测试从模型创建响应"""
        task = TaskFactory.create_task(product_name="Figma")
        
        # 模拟从ORM模型创建响应
        response_data = {
            "id": task.id,
            "user_id": task.user_id,
            "product_name": task.product_name,
            "status": task.status,
            "progress": task.progress,
            "error_message": task.error_message,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        
        response = TaskResponse(**response_data)
        
        assert response.id == task.id
        assert response.product_name == "Figma"
        assert response.status == TaskStatus.QUEUED


class TestTaskLogCreate:
    """任务日志创建schema测试"""
    
    def test_valid_log_create(self):
        """测试有效的日志创建数据"""
        task_id = uuid.uuid4()
        data = {
            "task_id": task_id,
            "level": LogLevel.INFO,
            "message": "Test message",
            "step": "test_step"
        }
        log_create = TaskLogCreate(**data)
        
        assert log_create.task_id == task_id
        assert log_create.level == LogLevel.INFO
        assert log_create.message == "Test message"
        assert log_create.step == "test_step"
    
    def test_message_validation(self):
        """测试消息验证"""
        task_id = uuid.uuid4()
        
        # 测试空消息
        with pytest.raises(ValueError):
            TaskLogCreate(
                task_id=task_id,
                level=LogLevel.INFO,
                message=""
            )


class TestRawDataCreate:
    """原始数据创建schema测试"""
    
    def test_valid_raw_data_create(self):
        """测试有效的原始数据创建"""
        task_id = uuid.uuid4()
        test_data = {"posts": [{"title": "Test", "score": 100}]}
        
        data = {
            "task_id": task_id,
            "source": "reddit",
            "data": test_data
        }
        raw_data_create = RawDataCreate(**data)
        
        assert raw_data_create.task_id == task_id
        assert raw_data_create.source == "reddit"
        assert raw_data_create.data == test_data
    
    def test_source_validation(self):
        """测试数据源验证"""
        task_id = uuid.uuid4()
        
        # 测试空源
        with pytest.raises(ValueError):
            RawDataCreate(
                task_id=task_id,
                source="",
                data={}
            )
        
        # 测试超长源名称
        long_source = "a" * 101
        with pytest.raises(ValueError):
            RawDataCreate(
                task_id=task_id,
                source=long_source,
                data={}
            )


class TestAnalysisResultCreate:
    """分析结果创建schema测试"""
    
    def test_valid_analysis_result_create(self):
        """测试有效的分析结果创建"""
        task_id = uuid.uuid4()
        data = {
            "task_id": task_id,
            "sentiment_score": 0.7,
            "sentiment_distribution": {"positive": 0.7, "negative": 0.3},
            "top_topics": [{"topic": "design", "weight": 0.8}],
            "feature_requests": [{"feature": "mobile app", "frequency": 10}],
            "key_insights": ["Users love the collaboration features"]
        }
        
        result_create = AnalysisResultCreate(**data)
        
        assert result_create.task_id == task_id
        assert result_create.sentiment_score == 0.7
        assert len(result_create.key_insights) == 1
    
    def test_sentiment_score_validation(self):
        """测试情感评分验证"""
        task_id = uuid.uuid4()
        
        # 测试超出范围的评分
        with pytest.raises(ValueError):
            AnalysisResultCreate(
                task_id=task_id,
                sentiment_score=1.5
            )
        
        with pytest.raises(ValueError):
            AnalysisResultCreate(
                task_id=task_id,
                sentiment_score=-1.5
            )
        
        # 测试边界值
        result = AnalysisResultCreate(task_id=task_id, sentiment_score=-1.0)
        assert result.sentiment_score == -1.0
        
        result = AnalysisResultCreate(task_id=task_id, sentiment_score=1.0)
        assert result.sentiment_score == 1.0
    
    def test_optional_fields(self):
        """测试可选字段"""
        task_id = uuid.uuid4()
        result = AnalysisResultCreate(task_id=task_id)
        
        assert result.sentiment_score is None
        assert result.sentiment_distribution is None
        assert result.top_topics is None
        assert result.feature_requests is None
        assert result.key_insights is None