"""
API依赖注入
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db


def get_current_user_id() -> str:
    """
    获取当前用户ID
    TODO: 实现真实的用户认证逻辑
    """
    # 暂时返回默认用户ID，后续可以从JWT token或session中获取
    return "default_user"


def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话依赖
    """
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def validate_uuid(uuid_str: str) -> str:
    """
    验证UUID格式
    """
    import uuid
    try:
        uuid.UUID(uuid_str)
        return uuid_str
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )
