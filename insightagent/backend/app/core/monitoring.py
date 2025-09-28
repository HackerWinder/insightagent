"""
系统监控和性能指标收集
"""
import time
import psutil
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
import asyncio

from app.core.redis import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    load_average: List[float]


@dataclass
class ApplicationMetrics:
    """应用指标数据类"""
    timestamp: str
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    queue_size: int
    active_connections: int
    response_time_avg: float
    error_rate: float
    throughput: float


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.metrics_key_prefix = "insight_agent:metrics"
        self.retention_hours = 24  # 保留24小时的指标数据
        
        # 性能计数器
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.last_reset = time.time()
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # 网络信息
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_recv_mb = network.bytes_recv / (1024 * 1024)
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # 系统负载
            load_average = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]
            
            metrics = SystemMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk.percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                process_count=process_count,
                load_average=load_average
            )
            
            # 存储到Redis
            await self._store_metrics("system", metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise
    
    async def collect_application_metrics(self) -> ApplicationMetrics:
        """收集应用指标"""
        try:
            # 从Redis获取任务统计
            from app.services.queue_manager import task_queue
            queue_stats = await task_queue.get_queue_stats()
            
            # 从WebSocket管理器获取连接统计
            from app.services.websocket_manager import connection_manager
            ws_stats = connection_manager.get_connection_stats()
            
            # 计算性能指标
            current_time = time.time()
            time_window = current_time - self.last_reset
            
            # 计算平均响应时间
            avg_response_time = (
                sum(self.response_times) / len(self.response_times) 
                if self.response_times else 0.0
            )
            
            # 计算错误率
            error_rate = (
                self.error_count / self.request_count 
                if self.request_count > 0 else 0.0
            )
            
            # 计算吞吐量（请求/秒）
            throughput = (
                self.request_count / time_window 
                if time_window > 0 else 0.0
            )
            
            metrics = ApplicationMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                active_tasks=queue_stats.get("processing", 0),
                completed_tasks=queue_stats.get("completed", 0),
                failed_tasks=queue_stats.get("failed", 0),
                queue_size=sum([
                    queue_stats.get("queue_low", 0),
                    queue_stats.get("queue_normal", 0),
                    queue_stats.get("queue_high", 0),
                    queue_stats.get("queue_urgent", 0)
                ]),
                active_connections=ws_stats.get("total_connections", 0),
                response_time_avg=avg_response_time,
                error_rate=error_rate,
                throughput=throughput
            )
            
            # 存储到Redis
            await self._store_metrics("application", metrics)
            
            # 重置计数器（每小时重置一次）
            if time_window > 3600:  # 1小时
                self._reset_counters()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            raise
    
    async def _store_metrics(self, metric_type: str, metrics: Any):
        """存储指标到Redis"""
        try:
            key = f"{self.metrics_key_prefix}:{metric_type}"
            timestamp = int(time.time())
            
            # 使用有序集合存储时间序列数据
            self.redis.zadd(key, {
                str(asdict(metrics)): timestamp
            })
            
            # 清理过期数据
            cutoff_time = timestamp - (self.retention_hours * 3600)
            self.redis.zremrangebyscore(key, 0, cutoff_time)
            
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    def record_request(self, response_time: float, is_error: bool = False):
        """记录请求指标"""
        self.request_count += 1
        self.response_times.append(response_time)
        
        if is_error:
            self.error_count += 1
        
        # 限制响应时间列表大小
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-500:]
    
    def _reset_counters(self):
        """重置性能计数器"""
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.last_reset = time.time()
    
    async def get_metrics_history(
        self, 
        metric_type: str, 
        hours: int = 1
    ) -> List[Dict[str, Any]]:
        """获取指标历史数据"""
        try:
            key = f"{self.metrics_key_prefix}:{metric_type}"
            
            # 计算时间范围
            end_time = int(time.time())
            start_time = end_time - (hours * 3600)
            
            # 从Redis获取数据
            raw_data = self.redis.zrangebyscore(
                key, start_time, end_time, withscores=True
            )
            
            # 解析数据
            metrics_history = []
            for data_str, timestamp in raw_data:
                try:
                    import ast
                    metrics_dict = ast.literal_eval(data_str)
                    metrics_history.append(metrics_dict)
                except Exception as e:
                    logger.warning(f"Failed to parse metrics data: {e}")
                    continue
            
            return metrics_history
            
        except Exception as e:
            logger.error(f"Failed to get metrics history: {e}")
            return []
    
    async def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            # 获取最新的系统指标
            system_metrics = await self.collect_system_metrics()
            app_metrics = await self.collect_application_metrics()
            
            # 评估健康状态
            health_status = "healthy"
            issues = []
            
            # 检查CPU使用率
            if system_metrics.cpu_percent > 80:
                health_status = "warning"
                issues.append(f"High CPU usage: {system_metrics.cpu_percent:.1f}%")
            
            # 检查内存使用率
            if system_metrics.memory_percent > 85:
                health_status = "critical" if system_metrics.memory_percent > 95 else "warning"
                issues.append(f"High memory usage: {system_metrics.memory_percent:.1f}%")
            
            # 检查磁盘使用率
            if system_metrics.disk_percent > 90:
                health_status = "critical" if system_metrics.disk_percent > 95 else "warning"
                issues.append(f"High disk usage: {system_metrics.disk_percent:.1f}%")
            
            # 检查错误率
            if app_metrics.error_rate > 0.1:  # 10%错误率
                health_status = "warning"
                issues.append(f"High error rate: {app_metrics.error_rate:.2%}")
            
            # 检查队列积压
            if app_metrics.queue_size > 100:
                health_status = "warning"
                issues.append(f"Large queue backlog: {app_metrics.queue_size} tasks")
            
            return {
                "status": health_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system_metrics": asdict(system_metrics),
                "application_metrics": asdict(app_metrics),
                "issues": issues,
                "summary": {
                    "cpu_usage": f"{system_metrics.cpu_percent:.1f}%",
                    "memory_usage": f"{system_metrics.memory_percent:.1f}%",
                    "disk_usage": f"{system_metrics.disk_percent:.1f}%",
                    "active_tasks": app_metrics.active_tasks,
                    "queue_size": app_metrics.queue_size,
                    "error_rate": f"{app_metrics.error_rate:.2%}",
                    "throughput": f"{app_metrics.throughput:.2f} req/s"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.error_key_prefix = "insight_agent:errors"
        self.max_errors_stored = 1000
    
    async def log_error(
        self, 
        error: Exception, 
        context: Dict[str, Any] = None,
        severity: str = "error"
    ):
        """记录错误"""
        try:
            error_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "severity": severity,
                "context": context or {},
                "traceback": self._get_traceback_string(error)
            }
            
            # 存储到Redis
            key = f"{self.error_key_prefix}:log"
            self.redis.lpush(key, str(error_data))
            
            # 限制存储的错误数量
            self.redis.ltrim(key, 0, self.max_errors_stored - 1)
            
            # 记录到日志
            if severity == "critical":
                logger.critical(f"Critical error: {error}", exc_info=error)
            elif severity == "error":
                logger.error(f"Error: {error}", exc_info=error)
            else:
                logger.warning(f"Warning: {error}")
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    def _get_traceback_string(self, error: Exception) -> str:
        """获取错误堆栈信息"""
        import traceback
        return traceback.format_exception(type(error), error, error.__traceback__)
    
    async def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        try:
            key = f"{self.error_key_prefix}:log"
            raw_errors = self.redis.lrange(key, 0, limit - 1)
            
            errors = []
            for error_str in raw_errors:
                try:
                    import ast
                    error_data = ast.literal_eval(error_str)
                    errors.append(error_data)
                except Exception as e:
                    logger.warning(f"Failed to parse error data: {e}")
                    continue
            
            return errors
            
        except Exception as e:
            logger.error(f"Failed to get recent errors: {e}")
            return []
    
    async def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误统计"""
        try:
            errors = await self.get_recent_errors(limit=1000)
            
            # 过滤时间范围内的错误
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            recent_errors = []
            
            for error in errors:
                try:
                    error_time = datetime.fromisoformat(error["timestamp"].replace('Z', '+00:00'))
                    if error_time >= cutoff_time:
                        recent_errors.append(error)
                except Exception:
                    continue
            
            # 统计错误类型
            error_types = {}
            severity_counts = {"critical": 0, "error": 0, "warning": 0}
            
            for error in recent_errors:
                error_type = error.get("error_type", "Unknown")
                severity = error.get("severity", "error")
                
                error_types[error_type] = error_types.get(error_type, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            return {
                "total_errors": len(recent_errors),
                "time_range_hours": hours,
                "error_types": error_types,
                "severity_distribution": severity_counts,
                "error_rate": len(recent_errors) / hours if hours > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get error statistics: {e}")
            return {}


# 全局实例
metrics_collector = MetricsCollector()
error_handler = ErrorHandler()