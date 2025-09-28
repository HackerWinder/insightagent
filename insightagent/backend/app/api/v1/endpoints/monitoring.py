"""
监控相关端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional

from app.api.deps import get_current_user_id
from app.core.monitoring import metrics_collector, error_handler

router = APIRouter()


@router.get("/health")
async def get_system_health(
    current_user_id: str = Depends(get_current_user_id)
):
    """获取系统健康状态"""
    try:
        health_data = await metrics_collector.get_system_health()
        
        # 根据健康状态设置HTTP状态码
        http_status = status.HTTP_200_OK
        if health_data.get("status") == "critical":
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health_data.get("status") == "warning":
            http_status = status.HTTP_206_PARTIAL_CONTENT
        
        return {
            "status": "success",
            "data": health_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )


@router.get("/metrics/system")
async def get_system_metrics(
    current_user_id: str = Depends(get_current_user_id)
):
    """获取系统指标"""
    try:
        metrics = await metrics_collector.collect_system_metrics()
        
        return {
            "status": "success",
            "data": metrics.__dict__
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )


@router.get("/metrics/application")
async def get_application_metrics(
    current_user_id: str = Depends(get_current_user_id)
):
    """获取应用指标"""
    try:
        metrics = await metrics_collector.collect_application_metrics()
        
        return {
            "status": "success",
            "data": metrics.__dict__
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get application metrics: {str(e)}"
        )


@router.get("/metrics/history")
async def get_metrics_history(
    metric_type: str = Query(..., description="指标类型 (system, application)"),
    hours: int = Query(1, ge=1, le=24, description="历史数据小时数"),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取指标历史数据"""
    try:
        if metric_type not in ["system", "application"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid metric type. Must be 'system' or 'application'"
            )
        
        history = await metrics_collector.get_metrics_history(metric_type, hours)
        
        return {
            "status": "success",
            "data": {
                "metric_type": metric_type,
                "hours": hours,
                "data_points": len(history),
                "history": history
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics history: {str(e)}"
        )


@router.get("/errors/recent")
async def get_recent_errors(
    limit: int = Query(50, ge=1, le=200, description="错误数量限制"),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取最近的错误"""
    try:
        errors = await error_handler.get_recent_errors(limit)
        
        return {
            "status": "success",
            "data": {
                "total_errors": len(errors),
                "limit": limit,
                "errors": errors
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent errors: {str(e)}"
        )


@router.get("/errors/statistics")
async def get_error_statistics(
    hours: int = Query(24, ge=1, le=168, description="统计时间范围（小时）"),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取错误统计"""
    try:
        stats = await error_handler.get_error_statistics(hours)
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get error statistics: {str(e)}"
        )


@router.get("/performance/summary")
async def get_performance_summary(
    current_user_id: str = Depends(get_current_user_id)
):
    """获取性能摘要"""
    try:
        # 获取系统和应用指标
        system_metrics = await metrics_collector.collect_system_metrics()
        app_metrics = await metrics_collector.collect_application_metrics()
        
        # 获取错误统计
        error_stats = await error_handler.get_error_statistics(hours=1)
        
        # 生成性能摘要
        summary = {
            "timestamp": system_metrics.timestamp,
            "system_performance": {
                "cpu_usage": f"{system_metrics.cpu_percent:.1f}%",
                "memory_usage": f"{system_metrics.memory_percent:.1f}%",
                "disk_usage": f"{system_metrics.disk_percent:.1f}%",
                "load_average": system_metrics.load_average[0] if system_metrics.load_average else 0
            },
            "application_performance": {
                "active_tasks": app_metrics.active_tasks,
                "queue_size": app_metrics.queue_size,
                "active_connections": app_metrics.active_connections,
                "avg_response_time": f"{app_metrics.response_time_avg:.3f}s",
                "error_rate": f"{app_metrics.error_rate:.2%}",
                "throughput": f"{app_metrics.throughput:.2f} req/s"
            },
            "error_summary": {
                "total_errors_last_hour": error_stats.get("total_errors", 0),
                "error_rate_per_hour": error_stats.get("error_rate", 0),
                "critical_errors": error_stats.get("severity_distribution", {}).get("critical", 0)
            },
            "health_indicators": {
                "cpu_healthy": system_metrics.cpu_percent < 80,
                "memory_healthy": system_metrics.memory_percent < 85,
                "disk_healthy": system_metrics.disk_percent < 90,
                "error_rate_healthy": app_metrics.error_rate < 0.05,
                "queue_healthy": app_metrics.queue_size < 50
            }
        }
        
        # 计算整体健康评分
        healthy_indicators = sum(summary["health_indicators"].values())
        total_indicators = len(summary["health_indicators"])
        health_score = (healthy_indicators / total_indicators) * 100
        
        summary["overall_health_score"] = f"{health_score:.1f}%"
        
        return {
            "status": "success",
            "data": summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance summary: {str(e)}"
        )


@router.post("/test/error")
async def test_error_logging(
    error_message: str = Query("Test error", description="测试错误消息"),
    severity: str = Query("error", description="错误严重程度"),
    current_user_id: str = Depends(get_current_user_id)
):
    """测试错误日志记录（仅用于开发和测试）"""
    try:
        # 创建测试错误
        test_error = Exception(error_message)
        
        # 记录错误
        await error_handler.log_error(
            error=test_error,
            context={
                "test": True,
                "user_id": current_user_id,
                "endpoint": "/monitoring/test/error"
            },
            severity=severity
        )
        
        return {
            "status": "success",
            "message": f"Test error logged with severity: {severity}",
            "error_message": error_message
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log test error: {str(e)}"
        )