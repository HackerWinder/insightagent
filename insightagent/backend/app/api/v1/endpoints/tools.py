"""
数据收集工具相关端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from app.api.deps import get_current_user_id
from app.services.tool_manager import tool_manager

router = APIRouter()


class DataCollectionRequest(BaseModel):
    """数据收集请求模型"""
    product_name: str
    tool_configs: Optional[Dict[str, Dict[str, Any]]] = None


class SingleToolRequest(BaseModel):
    """单个工具数据收集请求模型"""
    product_name: str
    tool_name: str
    config: Optional[Dict[str, Any]] = None


@router.get("/")
async def get_available_tools(
    current_user_id: str = Depends(get_current_user_id)
):
    """获取可用的数据收集工具列表"""
    try:
        tools = tool_manager.get_available_tools()
        tools_info = tool_manager.get_tools_info()
        
        return {
            "status": "success",
            "data": {
                "available_tools": tools,
                "tools_info": tools_info,
                "total_tools": len(tools)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available tools: {str(e)}"
        )


@router.get("/{tool_name}/capabilities")
async def get_tool_capabilities(
    tool_name: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """获取指定工具的能力信息"""
    try:
        capabilities = await tool_manager.get_tool_capabilities(tool_name)
        
        return {
            "status": "success",
            "data": capabilities
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/collect")
async def collect_data_from_all_tools(
    request: DataCollectionRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """使用所有可用工具收集数据"""
    try:
        result = await tool_manager.collect_data_from_all_tools(
            product_name=request.product_name,
            tool_configs=request.tool_configs
        )
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect data: {str(e)}"
        )


@router.post("/collect/{tool_name}")
async def collect_data_from_single_tool(
    tool_name: str,
    request: SingleToolRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """使用指定工具收集数据"""
    try:
        # 验证工具名称匹配
        if request.tool_name != tool_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tool name in path and request body must match"
            )
        
        result = await tool_manager.collect_data_from_tool(
            tool_name=tool_name,
            product_name=request.product_name,
            **(request.config or {})
        )
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        error_status = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=error_status,
            detail=str(e)
        )


@router.get("/health")
async def check_tools_health(
    current_user_id: str = Depends(get_current_user_id)
):
    """检查所有工具的健康状态"""
    try:
        health_status = await tool_manager.health_check_all_tools()
        
        # 根据整体健康状态设置HTTP状态码
        http_status = status.HTTP_200_OK
        if health_status["overall_status"] == "unhealthy":
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health_status["overall_status"] == "degraded":
            http_status = status.HTTP_206_PARTIAL_CONTENT
        
        return {
            "status": "success",
            "data": health_status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check tools health: {str(e)}"
        )


@router.get("/{tool_name}/health")
async def check_single_tool_health(
    tool_name: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """检查指定工具的健康状态"""
    try:
        tool = tool_manager.get_tool(tool_name)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found"
            )
        
        async with tool:
            health_info = await tool.health_check()
        
        # 根据健康状态设置HTTP状态码
        http_status = status.HTTP_200_OK
        if health_info.get("status") != "healthy":
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        
        return {
            "status": "success",
            "data": health_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check tool health: {str(e)}"
        )


@router.get("/reddit/subreddits")
async def get_default_subreddits(
    current_user_id: str = Depends(get_current_user_id)
):
    """获取Reddit工具的默认subreddit列表"""
    try:
        reddit_tool = tool_manager.get_tool("reddit_tool")
        if not reddit_tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reddit tool not available"
            )
        
        return {
            "status": "success",
            "data": {
                "default_subreddits": reddit_tool.default_subreddits,
                "total_subreddits": len(reddit_tool.default_subreddits)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subreddits: {str(e)}"
        )


@router.get("/product-hunt/trending")
async def get_trending_products(
    days: int = Query(7, ge=1, le=30, description="获取多少天内的趋势产品"),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取Product Hunt趋势产品"""
    try:
        ph_tool = tool_manager.get_tool("product_hunt_tool")
        if not ph_tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product Hunt tool not available"
            )
        
        async with ph_tool:
            trending_data = await ph_tool.get_trending_products(days=days)
        
        return {
            "status": "success",
            "data": trending_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trending products: {str(e)}"
        )