from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 应用
    APP_NAME: str = "VoiCal Backend"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./voical.db"
    DATABASE_POOL_SIZE: int = 0
    DATABASE_MAX_OVERFLOW: int = 0

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # JWT
    JWT_SECRET_KEY: str = "super_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # 加密密钥（AES-256）
    FIELD_ENCRYPTION_KEY: str = "1234567890123456789012345678901234567890123456789012345678901234"

    # 钉钉
    DINGTALK_APP_KEY: str = ""
    DINGTALK_APP_SECRET: str = ""

    # 讯飞
    XUNFEI_APPID: str = ""
    XUNFEI_API_KEY: str = ""

    # Anthropic LLM
    ANTHROPIC_API_KEY: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
