"""
Agent执行相关端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel

from app.api.deps import get_current_user_id, get_db_session
from app.services.agent_executor import agent_executor_service
from app.services.task_manager import TaskManager
from sqlalchemy.orm import Session

router = APIRouter()


def get_task_manager(db: Session = Depends(get_db_session)) -> TaskManager:
    """获取任务管理器实例"""
    return TaskManager(db)


class AgentExecutionRequest(BaseModel):
    """Agent执行请求模型"""
    task_id: str
    product_name: str


@router.get("/status")
async def get_agent_status(
    current_user_id: str = Depends(get_current_user_id)
):
    """获取Agent状态信息"""
    try:
        status = agent_executor_service.get_agent_status()
        
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/health")
async def check_agent_health(
    current_user_id: str = Depends(get_current_user_id)
):
    """检查Agent健康状态"""
    try:
        health_info = await agent_executor_service.health_check()
        
        # 根据健康状态设置HTTP状态码
        http_status = status.HTTP_200_OK
        if health_info["status"] == "unhealthy":
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health_info["status"] == "degraded":
            http_status = status.HTTP_206_PARTIAL_CONTENT
        
        return {
            "status": "success",
            "data": health_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check agent health: {str(e)}"
        )


@router.post("/execute")
async def execute_agent_task(
    request: AgentExecutionRequest,
    task_manager: TaskManager = Depends(get_task_manager),
    current_user_id: str = Depends(get_current_user_id)
):
    """执行Agent分析任务"""
    try:
        # 验证任务存在且属于当前用户
        import uuid
        task = await task_manager.get_task_by_id(uuid.UUID(request.task_id), current_user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # 执行Agent任务
        result = await agent_executor_service.execute_task(
            task_id=request.task_id,
            user_id=current_user_id,
            product_name=request.product_name,
            task_manager=task_manager
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute agent task: {str(e)}"
        )


@router.get("/plan/{product_name}")
async def get_execution_plan(
    product_name: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """获取执行计划"""
    try:
        steps = await agent_executor_service.plan_execution_steps(product_name)
        
        return {
            "status": "success",
            "data": {
                "product_name": product_name,
                "steps": steps,
                "total_steps": len(steps),
                "estimated_total_duration": "15-25分钟"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution plan: {str(e)}"
        )


@router.get("/capabilities")
async def get_agent_capabilities(
    current_user_id: str = Depends(get_current_user_id)
):
    """获取Agent能力信息"""
    try:
        from app.services.tool_manager import tool_manager
        
        # 获取Agent状态
        agent_status = agent_executor_service.get_agent_status()
        
        # 获取工具能力
        tools_capabilities = {}
        for tool_name in agent_status.get("tools", []):
            try:
                tool_cap = await tool_manager.get_tool_capabilities(tool_name.replace("_search", "_tool"))
                tools_capabilities[tool_name] = tool_cap
            except Exception as e:
                tools_capabilities[tool_name] = {"error": str(e)}
        
        capabilities = {
            "agent_model": agent_status.get("llm_model"),
            "available_tools": agent_status.get("tools", []),
            "max_iterations": 10,
            "max_execution_time": "30 minutes",
            "supported_analysis": [
                "用户情感分析",
                "产品反馈聚类",
                "功能需求提取",
                "竞争对手分析",
                "市场趋势分析"
            ],
            "output_formats": [
                "结构化报告",
                "JSON数据",
                "可视化图表建议"
            ],
            "tools_capabilities": tools_capabilities
        }
        
        return {
            "status": "success",
            "data": capabilities
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent capabilities: {str(e)}"
        )


@router.post("/test")
async def test_agent_execution(
    current_user_id: str = Depends(get_current_user_id)
):
    """测试Agent执行（使用示例产品）"""
    try:
        # 检查Agent是否可用
        agent_status = agent_executor_service.get_agent_status()
        if not agent_status.get("agent_available"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent not available"
            )
        
        # 使用示例产品进行测试
        test_product = "Figma"
        steps = await agent_executor_service.plan_execution_steps(test_product)
        
        return {
            "status": "success",
            "data": {
                "message": "Agent is ready for execution",
                "test_product": test_product,
                "planned_steps": len(steps),
                "agent_status": agent_status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent test failed: {str(e)}"
        )