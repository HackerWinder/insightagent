"""
API端点的集成测试
"""
import pytest
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.models.task import TaskStatus


class TestHealthEndpoints:
    """健康检查端点测试"""
    
    def test_root_endpoint(self, client: TestClient):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "InsightAgent" in data["message"]
    
    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_api_health_check(self, client: TestClient):
        """测试API健康检查端点"""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "InsightAgent API"
    
    def test_detailed_health_check(self, client: TestClient):
        """测试详细健康检查"""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "checks" in data
        assert "database" in data["checks"]
    
    def test_readiness_check(self, client: TestClient):
        """测试就绪检查"""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_liveness_check(self, client: TestClient):
        """测试存活检查"""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestTaskEndpoints:
    """任务管理端点测试"""
    
    def test_create_task(self, client: TestClient):
        """测试创建任务"""
        task_data = {
            "product_name": "Figma",
            "user_id": "test_user"
        }
        
        response = client.post("/api/v1/tasks/", json=task_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["product_name"] == "Figma"
        assert data["status"] == "QUEUED"
        assert data["progress"] == 0.0
        assert "id" in data
        assert "created_at" in data
    
    def test_create_task_validation(self, client: TestClient):
        """测试任务创建验证"""
        # 测试空产品名称
        task_data = {
            "product_name": "",
            "user_id": "test_user"
        }
        
        response = client.post("/api/v1/tasks/", json=task_data)
        assert response.status_code == 422
    
    def test_get_tasks_empty(self, client: TestClient):
        """测试获取空任务列表"""
        response = client.get("/api/v1/tasks/")
        assert response.status_code == 200
        
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] == 0
        assert len(data["tasks"]) == 0
    
    def test_get_tasks_with_data(self, client: TestClient):
        """测试获取任务列表（有数据）"""
        # 先创建一个任务
        task_data = {
            "product_name": "TestProduct",
            "user_id": "test_user"
        }
        create_response = client.post("/api/v1/tasks/", json=task_data)
        assert create_response.status_code == 201
        
        # 获取任务列表
        response = client.get("/api/v1/tasks/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 1
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["product_name"] == "TestProduct"
    
    def test_get_task_by_id(self, client: TestClient):
        """测试根据ID获取任务"""
        # 先创建一个任务
        task_data = {
            "product_name": "TestProduct",
            "user_id": "test_user"
        }
        create_response = client.post("/api/v1/tasks/", json=task_data)
        task_id = create_response.json()["id"]
        
        # 根据ID获取任务
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == task_id
        assert data["product_name"] == "TestProduct"
    
    def test_get_task_not_found(self, client: TestClient):
        """测试获取不存在的任务"""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/tasks/{fake_id}")
        assert response.status_code == 404
    
    def test_get_task_invalid_uuid(self, client: TestClient):
        """测试无效UUID格式"""
        response = client.get("/api/v1/tasks/invalid-uuid")
        assert response.status_code == 400
    
    def test_update_task(self, client: TestClient):
        """测试更新任务"""
        # 先创建一个任务
        task_data = {
            "product_name": "TestProduct",
            "user_id": "test_user"
        }
        create_response = client.post("/api/v1/tasks/", json=task_data)
        task_id = create_response.json()["id"]
        
        # 更新任务
        update_data = {
            "status": "RUNNING",
            "progress": 0.5
        }
        response = client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "RUNNING"
        assert data["progress"] == 0.5
    
    def test_delete_task(self, client: TestClient):
        """测试删除任务"""
        # 先创建一个任务
        task_data = {
            "product_name": "TestProduct",
            "user_id": "test_user"
        }
        create_response = client.post("/api/v1/tasks/", json=task_data)
        task_id = create_response.json()["id"]
        
        # 删除任务
        response = client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 204
        
        # 验证任务已删除
        get_response = client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 404
    
    def test_delete_running_task(self, client: TestClient):
        """测试删除运行中的任务（应该失败）"""
        # 先创建一个任务
        task_data = {
            "product_name": "TestProduct",
            "user_id": "test_user"
        }
        create_response = client.post("/api/v1/tasks/", json=task_data)
        task_id = create_response.json()["id"]
        
        # 将任务状态设为运行中
        update_data = {"status": "RUNNING"}
        client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        
        # 尝试删除运行中的任务
        response = client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 400
    
    def test_get_task_logs(self, client: TestClient):
        """测试获取任务日志"""
        # 先创建一个任务
        task_data = {
            "product_name": "TestProduct",
            "user_id": "test_user"
        }
        create_response = client.post("/api/v1/tasks/", json=task_data)
        task_id = create_response.json()["id"]
        
        # 获取任务日志
        response = client.get(f"/api/v1/tasks/{task_id}/logs")
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)
    
    def test_pagination(self, client: TestClient):
        """测试分页功能"""
        # 创建多个任务
        for i in range(15):
            task_data = {
                "product_name": f"Product{i}",
                "user_id": "test_user"
            }
            client.post("/api/v1/tasks/", json=task_data)
        
        # 测试第一页
        response = client.get("/api/v1/tasks/?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["tasks"]) == 10
        assert data["page"] == 1
        
        # 测试第二页
        response = client.get("/api/v1/tasks/?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 5
        assert data["page"] == 2
    
    def test_filter_by_status(self, client: TestClient):
        """测试按状态筛选"""
        # 创建不同状态的任务
        task_data = {
            "product_name": "CompletedTask",
            "user_id": "test_user"
        }
        create_response = client.post("/api/v1/tasks/", json=task_data)
        task_id = create_response.json()["id"]
        
        # 更新任务状态为完成
        update_data = {"status": "COMPLETED"}
        client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        
        # 按状态筛选
        response = client.get("/api/v1/tasks/?status=COMPLETED")
        assert response.status_code == 200
        data = response.json()
        assert all(task["status"] == "COMPLETED" for task in data["tasks"])