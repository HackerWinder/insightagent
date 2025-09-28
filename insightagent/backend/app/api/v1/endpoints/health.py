"""
健康检查相关端点
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from app.api.deps import get_db_session
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """基础健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "InsightAgent API"
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db_session)):
    """详细健康检查，包括数据库连接"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "InsightAgent API",
        "version": settings.app_version,
        "checks": {}
    }
    
    # 检查数据库连接
    try:
        result = db.execute(text("SELECT 1"))
        result.scalar()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
    
    # 检查Redis连接（如果配置了）
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }
    
    return health_status


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db_session)):
    """就绪检查 - 用于Kubernetes等容器编排"""
    try:
        # 检查数据库连接
        result = db.execute(text("SELECT 1"))
        result.scalar()
        
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}


@router.get("/live")
async def liveness_check():
    """存活检查 - 用于Kubernetes等容器编排"""
    return {"status": "alive"}