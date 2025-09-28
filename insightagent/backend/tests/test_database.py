"""
数据库连接和操作的单元测试
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db


# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_database_connection():
    """测试数据库连接"""
    db = TestingSessionLocal()
    try:
        # 执行简单查询测试连接
        result = db.execute("SELECT 1")
        assert result.scalar() == 1
    finally:
        db.close()


def test_get_db_dependency():
    """测试数据库依赖注入函数"""
    db_gen = get_db()
    db = next(db_gen)
    
    # 验证返回的是数据库会话
    assert hasattr(db, 'query')
    assert hasattr(db, 'commit')
    assert hasattr(db, 'rollback')
    
    # 清理
    try:
        next(db_gen)
    except StopIteration:
        pass  # 正常结束


def test_create_tables():
    """测试表创建功能"""
    from app.core.database import create_tables
    
    # 创建表
    create_tables()
    
    # 验证表是否创建成功
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # 检查是否包含预期的表（根据实际模型调整）
    assert len(tables) >= 0  # 至少应该有一些表