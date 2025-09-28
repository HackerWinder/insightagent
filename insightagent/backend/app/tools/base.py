"""
数据收集工具基类
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx
import time
import random

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """工具执行错误"""
    pass


class RateLimitError(ToolError):
    """API限制错误"""
    pass


class BaseTool(ABC):
    """数据收集工具基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.client: Optional[httpx.AsyncClient] = None
        self._rate_limit_delay = 1.0  # 基础延迟时间（秒）
        self._max_retries = 3
        self._backoff_factor = 2.0
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    @abstractmethod
    async def collect_data(self, product_name: str, **kwargs) -> Dict[str, Any]:
        """
        收集数据的抽象方法
        
        Args:
            product_name: 产品名称
            **kwargs: 其他参数
            
        Returns:
            收集到的数据
        """
        pass
    
    async def execute_with_retry(
        self, 
        func, 
        *args, 
        max_retries: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        带重试机制的执行函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            max_retries: 最大重试次数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        max_retries = max_retries or self._max_retries
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # 指数退避延迟
                    delay = self._rate_limit_delay * (self._backoff_factor ** (attempt - 1))
                    # 添加随机抖动
                    jitter = random.uniform(0.1, 0.3) * delay
                    total_delay = delay + jitter
                    
                    logger.info(f"Retrying {func.__name__} (attempt {attempt + 1}/{max_retries + 1}) after {total_delay:.2f}s")
                    await asyncio.sleep(total_delay)
                
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Successfully executed {func.__name__} after {attempt} retries")
                
                return result
                
            except RateLimitError as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Rate limit exceeded for {func.__name__} after {max_retries} retries")
                    break
                logger.warning(f"Rate limit hit for {func.__name__}, retrying...")
                
            except Exception as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Failed to execute {func.__name__} after {max_retries} retries: {e}")
                    break
                logger.warning(f"Error in {func.__name__} (attempt {attempt + 1}): {e}")
        
        raise last_exception or ToolError(f"Failed to execute {func.__name__}")
    
    async def make_request(
        self, 
        method: str, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            params: 查询参数
            json_data: JSON数据
            **kwargs: 其他参数
            
        Returns:
            HTTP响应
        """
        if not self.client:
            raise ToolError("HTTP client not initialized. Use async context manager.")
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                **kwargs
            )
            
            # 检查响应状态
            if response.status_code == 429:
                # 从响应头获取重试延迟时间
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    delay = int(retry_after)
                    logger.warning(f"Rate limited, retry after {delay} seconds")
                    raise RateLimitError(f"Rate limited, retry after {delay} seconds")
                else:
                    raise RateLimitError("Rate limited")
            
            response.raise_for_status()
            return response
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limited: {e}")
            raise ToolError(f"HTTP error {e.response.status_code}: {e}")
        except httpx.RequestError as e:
            raise ToolError(f"Request error: {e}")
    
    def validate_product_name(self, product_name: str) -> str:
        """
        验证和清理产品名称
        
        Args:
            product_name: 原始产品名称
            
        Returns:
            清理后的产品名称
        """
        if not product_name or not product_name.strip():
            raise ToolError("Product name cannot be empty")
        
        # 清理产品名称
        cleaned_name = product_name.strip()
        
        # 移除特殊字符（保留字母、数字、空格、连字符）
        import re
        cleaned_name = re.sub(r'[^\w\s\-]', '', cleaned_name)
        
        if not cleaned_name:
            raise ToolError("Product name contains no valid characters")
        
        return cleaned_name
    
    def format_timestamp(self, timestamp: Any) -> str:
        """
        格式化时间戳
        
        Args:
            timestamp: 时间戳（各种格式）
            
        Returns:
            ISO格式的时间字符串
        """
        try:
            if isinstance(timestamp, (int, float)):
                # Unix时间戳
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            elif isinstance(timestamp, str):
                # 字符串时间戳
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, datetime):
                # datetime对象
                dt = timestamp
            else:
                # 默认使用当前时间
                dt = datetime.now(timezone.utc)
            
            return dt.isoformat()
            
        except Exception as e:
            logger.warning(f"Failed to format timestamp {timestamp}: {e}")
            return datetime.now(timezone.utc).isoformat()
    
    def extract_text_content(self, text: str, max_length: int = 1000) -> str:
        """
        提取和清理文本内容
        
        Args:
            text: 原始文本
            max_length: 最大长度
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        import re
        cleaned_text = re.sub(r'\s+', ' ', text.strip())
        
        # 截断过长的文本
        if len(cleaned_text) > max_length:
            cleaned_text = cleaned_text[:max_length] + "..."
        
        return cleaned_text
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        获取工具信息
        
        Returns:
            工具信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "rate_limit_delay": self._rate_limit_delay,
            "max_retries": self._max_retries,
            "backoff_factor": self._backoff_factor
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        try:
            # 子类可以重写此方法进行特定的健康检查
            return {
                "tool": self.name,
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "tool": self.name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }