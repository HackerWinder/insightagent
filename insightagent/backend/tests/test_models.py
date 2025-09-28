"""
数据模型的单元测试
"""
import pytest
import uuid
from datetime import datetime, timezone

from app.models.task import Task, TaskLog, RawData, AnalysisResult, TaskStatus, LogLevel
from app.utils.factories import TaskFactory, TaskLogFactory, RawDataFactory, AnalysisResultFactory


class TestTask:
    """任务模型测试"""
    
    def test_create_task(self):
        """测试创建任务"""
        task = TaskFactory.create_task(
            product_name="Figma",
            user_id="user123",
            status=TaskStatus.QUEUED
        )
        
        assert task.product_name == "Figma"
        assert task.user_id == "user123"
        assert task.status == TaskStatus.QUEUED
        assert task.progress == 0.0
        assert task.error_message is None
        assert isinstance(task.id, uuid.UUID)
        assert isinstance(task.created_at, datetime)
    
    def test_task_to_dict(self):
        """测试任务转字典"""
        task = TaskFactory.create_task(product_name="TestProduct")
        task_dict = task.to_dict()
        
        assert "id" in task_dict
        assert task_dict["product_name"] == "TestProduct"
        assert task_dict["status"] == "QUEUED"
        assert task_dict["progress"] == 0.0
        assert "created_at" in task_dict
        assert "updated_at" in task_dict
    
    def test_task_status_enum(self):
        """测试任务状态枚举"""
        assert TaskStatus.QUEUED.value == "QUEUED"
        assert TaskStatus.RUNNING.value == "RUNNING"
        assert TaskStatus.COMPLETED.value == "COMPLETED"
        assert TaskStatus.FAILED.value == "FAILED"
    
    def test_task_repr(self):
        """测试任务字符串表示"""
        task = TaskFactory.create_task(product_name="Figma")
        repr_str = repr(task)
        
        assert "Task" in repr_str
        assert "Figma" in repr_str
        assert "QUEUED" in repr_str


class TestTaskLog:
    """任务日志模型测试"""
    
    def test_create_task_log(self):
        """测试创建任务日志"""
        task_id = uuid.uuid4()
        log = TaskLogFactory.create_log(
            task_id=task_id,
            level=LogLevel.INFO,
            message="Test message",
            step="test_step"
        )
        
        assert log.task_id == task_id
        assert log.level == LogLevel.INFO
        assert log.message == "Test message"
        assert log.step == "test_step"
        assert isinstance(log.timestamp, datetime)
    
    def test_log_to_dict(self):
        """测试日志转字典"""
        task_id = uuid.uuid4()
        log = TaskLogFactory.create_log(task_id=task_id, message="Test log")
        log_dict = log.to_dict()
        
        assert "id" in log_dict
        assert log_dict["task_id"] == str(task_id)
        assert log_dict["level"] == "INFO"
        assert log_dict["message"] == "Test log"
        assert "timestamp" in log_dict
    
    def test_log_level_enum(self):
        """测试日志级别枚举"""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"


class TestRawData:
    """原始数据模型测试"""
    
    def test_create_raw_data(self):
        """测试创建原始数据"""
        task_id = uuid.uuid4()
        test_data = {"posts": [{"title": "Test", "score": 100}]}
        
        raw_data = RawDataFactory.create_raw_data(
            task_id=task_id,
            source="reddit",
            data=test_data
        )
        
        assert raw_data.task_id == task_id
        assert raw_data.source == "reddit"
        assert raw_data.data == test_data
        assert isinstance(raw_data.collected_at, datetime)
    
    def test_raw_data_to_dict(self):
        """测试原始数据转字典"""
        task_id = uuid.uuid4()
        raw_data = RawDataFactory.create_raw_data(task_id=task_id)
        data_dict = raw_data.to_dict()
        
        assert "id" in data_dict
        assert data_dict["task_id"] == str(task_id)
        assert data_dict["source"] == "reddit"
        assert "data" in data_dict
        assert "collected_at" in data_dict
    
    def test_create_reddit_data(self):
        """测试创建Reddit数据"""
        task_id = uuid.uuid4()
        reddit_data = RawDataFactory.create_reddit_data(task_id)
        
        assert reddit_data.source == "reddit"
        assert "subreddit" in reddit_data.data
        assert "posts" in reddit_data.data
        assert len(reddit_data.data["posts"]) > 0


class TestAnalysisResult:
    """分析结果模型测试"""
    
    def test_create_analysis_result(self):
        """测试创建分析结果"""
        task_id = uuid.uuid4()
        result = AnalysisResultFactory.create_analysis_result(
            task_id=task_id,
            sentiment_score=0.8
        )
        
        assert result.task_id == task_id
        assert result.sentiment_score == 0.8
        assert result.sentiment_distribution is not None
        assert result.top_topics is not None
        assert result.feature_requests is not None
        assert result.key_insights is not None
        assert isinstance(result.created_at, datetime)
    
    def test_analysis_result_to_dict(self):
        """测试分析结果转字典"""
        task_id = uuid.uuid4()
        result = AnalysisResultFactory.create_analysis_result(task_id=task_id)
        result_dict = result.to_dict()
        
        assert "id" in result_dict
        assert result_dict["task_id"] == str(task_id)
        assert "sentiment_score" in result_dict
        assert "sentiment_distribution" in result_dict
        assert "top_topics" in result_dict
        assert "feature_requests" in result_dict
        assert "key_insights" in result_dict
        assert "created_at" in result_dict
    
    def test_sentiment_distribution_structure(self):
        """测试情感分布结构"""
        task_id = uuid.uuid4()
        result = AnalysisResultFactory.create_analysis_result(task_id=task_id)
        
        assert "positive" in result.sentiment_distribution
        assert "neutral" in result.sentiment_distribution
        assert "negative" in result.sentiment_distribution
        
        # 验证概率和为1
        total = sum(result.sentiment_distribution.values())
        assert abs(total - 1.0) < 0.01  # 允许浮点误差
    
    def test_feature_requests_structure(self):
        """测试功能需求结构"""
        task_id = uuid.uuid4()
        result = AnalysisResultFactory.create_analysis_result(task_id=task_id)
        
        assert len(result.feature_requests) > 0
        for request in result.feature_requests:
            assert "feature" in request
            assert "frequency" in request
            assert "sentiment" in request