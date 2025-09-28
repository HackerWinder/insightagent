"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = "InsightAgent"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # 数据库配置
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://vincent@localhost:5432/insightagent"
    )
    
    # Redis配置
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # OpenAI配置
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # SiliconFlow配置
    siliconflow_api_key: Optional[str] = os.getenv("SILICONFLOW_API_KEY")
    siliconflow_base_url: str = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    siliconflow_model: str = os.getenv("SILICONFLOW_MODEL", "deepseek-ai/deepseek-chat")
    
    # Reddit API配置
    reddit_client_id: Optional[str] = os.getenv("REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = os.getenv("REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = os.getenv("REDDIT_USER_AGENT", "InsightAgent/1.0")
    
    # Product Hunt API配置
    product_hunt_api_key: Optional[str] = os.getenv("PRODUCT_HUNT_API_KEY")
    
    # 任务配置
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
    task_timeout_minutes: int = int(os.getenv("TASK_TIMEOUT_MINUTES", "30"))
    
    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS配置
    allowed_origins: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    
    class Config:
        env_file = "/Users/vincent/个人文件/project/insightagent/backend/.env"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()
