"""
数据收集工具管理器
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timezone

from app.tools.base import BaseTool, ToolError
from app.tools.reddit import RedditTool
from app.tools.product_hunt import ProductHuntTool

logger = logging.getLogger(__name__)


class ToolManager:
    """数据收集工具管理器"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """初始化所有工具"""
        tool_classes = [
            RedditTool,
            ProductHuntTool
        ]
        
        for tool_class in tool_classes:
            try:
                tool = tool_class()
                self.tools[tool.name] = tool
                logger.info(f"Initialized tool: {tool.name}")
            except Exception as e:
                logger.error(f"Failed to initialize tool {tool_class.__name__}: {e}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取指定的工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具实例或None
        """
        return self.tools.get(tool_name)
    
    def get_available_tools(self) -> List[str]:
        """
        获取可用工具列表
        
        Returns:
            工具名称列表
        """
        return list(self.tools.keys())
    
    def get_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有工具的信息
        
        Returns:
            工具信息字典
        """
        tools_info = {}
        for tool_name, tool in self.tools.items():
            tools_info[tool_name] = tool.get_tool_info()
        return tools_info
    
    async def collect_data_from_tool(
        self, 
        tool_name: str, 
        product_name: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用指定工具收集数据
        
        Args:
            tool_name: 工具名称
            product_name: 产品名称
            **kwargs: 其他参数
            
        Returns:
            收集到的数据
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolError(f"Tool '{tool_name}' not found")
        
        logger.info(f"Starting data collection with {tool_name} for product: {product_name}")
        
        try:
            async with tool:
                data = await tool.collect_data(product_name, **kwargs)
                
                # 添加工具元数据
                data["tool_metadata"] = {
                    "tool_name": tool_name,
                    "tool_description": tool.description,
                    "collection_timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"Successfully collected data from {tool_name}")
                return data
                
        except Exception as e:
            logger.error(f"Failed to collect data from {tool_name}: {e}")
            raise ToolError(f"Data collection failed for {tool_name}: {str(e)}")
    
    async def collect_data_from_all_tools(
        self, 
        product_name: str, 
        tool_configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        使用所有可用工具收集数据
        
        Args:
            product_name: 产品名称
            tool_configs: 每个工具的配置参数
            
        Returns:
            所有工具收集到的数据
        """
        tool_configs = tool_configs or {}
        results = {}
        errors = {}
        
        logger.info(f"Starting data collection from all tools for product: {product_name}")
        
        # 并发执行所有工具
        tasks = []
        for tool_name in self.tools.keys():
            config = tool_configs.get(tool_name, {})
            task = self._collect_with_error_handling(tool_name, product_name, config)
            tasks.append((tool_name, task))
        
        # 等待所有任务完成
        for tool_name, task in tasks:
            try:
                result = await task
                results[tool_name] = result
            except Exception as e:
                errors[tool_name] = str(e)
                logger.error(f"Tool {tool_name} failed: {e}")
        
        # 汇总结果
        summary = {
            "product_name": product_name,
            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
            "tools_used": list(self.tools.keys()),
            "successful_tools": list(results.keys()),
            "failed_tools": list(errors.keys()),
            "success_rate": len(results) / len(self.tools) if self.tools else 0,
            "results": results,
            "errors": errors
        }
        
        logger.info(f"Data collection completed. Success rate: {summary['success_rate']:.2%}")
        
        return summary
    
    async def _collect_with_error_handling(
        self, 
        tool_name: str, 
        product_name: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        带错误处理的数据收集
        """
        try:
            return await self.collect_data_from_tool(tool_name, product_name, **config)
        except Exception as e:
            # 记录错误但不抛出，让上层处理
            logger.error(f"Error in {tool_name}: {e}")
            raise
    
    async def health_check_all_tools(self) -> Dict[str, Any]:
        """
        检查所有工具的健康状态
        
        Returns:
            所有工具的健康状态
        """
        health_results = {}
        
        # 并发检查所有工具
        tasks = []
        for tool_name, tool in self.tools.items():
            task = self._health_check_with_timeout(tool)
            tasks.append((tool_name, task))
        
        for tool_name, task in tasks:
            try:
                health_info = await asyncio.wait_for(task, timeout=10.0)
                health_results[tool_name] = health_info
            except asyncio.TimeoutError:
                health_results[tool_name] = {
                    "tool": tool_name,
                    "status": "timeout",
                    "error": "Health check timed out",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            except Exception as e:
                health_results[tool_name] = {
                    "tool": tool_name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        
        # 计算整体健康状态
        healthy_tools = sum(1 for result in health_results.values() if result.get("status") == "healthy")
        total_tools = len(self.tools)
        
        overall_status = {
            "overall_status": "healthy" if healthy_tools == total_tools else "degraded" if healthy_tools > 0 else "unhealthy",
            "healthy_tools": healthy_tools,
            "total_tools": total_tools,
            "health_rate": healthy_tools / total_tools if total_tools > 0 else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tools": health_results
        }
        
        return overall_status
    
    async def _health_check_with_timeout(self, tool: BaseTool) -> Dict[str, Any]:
        """
        带超时的健康检查
        """
        async with tool:
            return await tool.health_check()
    
    async def get_tool_capabilities(self, tool_name: str) -> Dict[str, Any]:
        """
        获取工具能力信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具能力信息
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolError(f"Tool '{tool_name}' not found")
        
        capabilities = {
            "name": tool.name,
            "description": tool.description,
            "supported_parameters": self._get_tool_parameters(tool),
            "rate_limits": {
                "base_delay": tool._rate_limit_delay,
                "max_retries": tool._max_retries,
                "backoff_factor": tool._backoff_factor
            }
        }
        
        # 工具特定的能力信息
        if isinstance(tool, RedditTool):
            capabilities["data_sources"] = ["reddit_posts", "reddit_comments"]
            capabilities["default_subreddits"] = tool.default_subreddits
        elif isinstance(tool, ProductHuntTool):
            capabilities["data_sources"] = ["product_info", "product_comments", "trending_products"]
            capabilities["api_features"] = ["search", "product_details", "trending"]
        
        return capabilities
    
    def _get_tool_parameters(self, tool: BaseTool) -> Dict[str, str]:
        """
        获取工具支持的参数
        """
        # 这里可以通过反射或文档来获取参数信息
        # 简化实现，返回常见参数
        common_params = {
            "product_name": "Product or company name to search for"
        }
        
        if isinstance(tool, RedditTool):
            common_params.update({
                "subreddits": "List of subreddits to search in",
                "limit": "Number of posts to retrieve per subreddit",
                "time_filter": "Time filter (hour, day, week, month, year, all)"
            })
        elif isinstance(tool, ProductHuntTool):
            common_params.update({
                "search_limit": "Number of search results to retrieve",
                "include_comments": "Whether to include product comments",
                "days_back": "Number of days back to search"
            })
        
        return common_params


# 全局工具管理器实例
tool_manager = ToolManager()