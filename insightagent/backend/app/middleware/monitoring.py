"""
监控中间件
"""
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from app.core.monitoring import metrics_collector, error_handler

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """监控中间件 - 收集请求指标和错误"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并收集指标"""
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 判断是否为错误响应
            is_error = response.status_code >= 400
            
            # 记录请求指标
            metrics_collector.record_request(response_time, is_error)
            
            # 添加响应头
            response.headers["X-Response-Time"] = f"{response_time:.4f}"
            response.headers["X-Request-ID"] = str(id(request))
            
            # 记录请求日志
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {response_time:.4f}s"
            )
            
            return response
            
        except Exception as e:
            # 记录异常
            response_time = time.time() - start_time
            
            # 记录错误指标
            metrics_collector.record_request(response_time, is_error=True)
            
            # 记录错误到监控系统
            await error_handler.log_error(
                error=e,
                context={
                    "method": request.method,
                    "path": str(request.url.path),
                    "query_params": dict(request.query_params),
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "response_time": response_time
                },
                severity="error"
            )
            
            # 重新抛出异常让FastAPI处理
            raise


class TaskTimeoutMiddleware(BaseHTTPMiddleware):
    """任务超时中间件"""
    
    def __init__(self, app, timeout_seconds: int = 300):  # 5分钟默认超时
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求超时"""
        import asyncio
        
        try:
            # 设置超时
            response = await asyncio.wait_for(
                call_next(request), 
                timeout=self.timeout_seconds
            )
            return response
            
        except asyncio.TimeoutError:
            # 记录超时错误
            await error_handler.log_error(
                error=Exception(f"Request timeout after {self.timeout_seconds}s"),
                context={
                    "method": request.method,
                    "path": str(request.url.path),
                    "timeout_seconds": self.timeout_seconds
                },
                severity="warning"
            )
            
            # 返回超时响应
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=408,
                content={
                    "error": "Request timeout",
                    "message": f"Request exceeded {self.timeout_seconds} seconds timeout"
                }
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的速率限制中间件"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # {client_ip: [(timestamp, count), ...]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理速率限制"""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_old_records(current_time)
        
        # 检查当前客户端的请求频率
        if self._is_rate_limited(client_ip, current_time):
            # 记录速率限制事件
            await error_handler.log_error(
                error=Exception(f"Rate limit exceeded for {client_ip}"),
                context={
                    "client_ip": client_ip,
                    "path": str(request.url.path),
                    "rate_limit": self.requests_per_minute
                },
                severity="warning"
            )
            
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {self.requests_per_minute} per minute"
                },
                headers={"Retry-After": "60"}
            )
        
        # 记录请求
        self._record_request(client_ip, current_time)
        
        # 继续处理请求
        return await call_next(request)
    
    def _cleanup_old_records(self, current_time: float):
        """清理过期的请求记录"""
        cutoff_time = current_time - 60  # 1分钟前
        
        for client_ip in list(self.request_counts.keys()):
            self.request_counts[client_ip] = [
                (timestamp, count) for timestamp, count in self.request_counts[client_ip]
                if timestamp > cutoff_time
            ]
            
            # 如果没有记录了，删除这个客户端
            if not self.request_counts[client_ip]:
                del self.request_counts[client_ip]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """检查是否超过速率限制"""
        if client_ip not in self.request_counts:
            return False
        
        # 计算最近1分钟的请求数
        recent_requests = sum(
            count for timestamp, count in self.request_counts[client_ip]
            if timestamp > current_time - 60
        )
        
        return recent_requests >= self.requests_per_minute
    
    def _record_request(self, client_ip: str, current_time: float):
        """记录请求"""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip].append((current_time, 1))