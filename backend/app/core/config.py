"""
Core configuration module
核心配置模块
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = "Voice Calendar API"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/voice_calendar"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    
    # LLM配置
    LLM_MODEL: str = "qwen-2.5-7b"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "http://localhost:11434"  # Ollama
    
    # STT配置
    STT_MODEL: str = "faster-whisper-base"
    STT_LANGUAGE: str = "zh"
    
    # TTS配置
    TTS_MODEL: str = "edge-tts"
    TTS_VOICE: str = "zh-CN-XiaoxiaoNeural"
    
    # 会话配置
    SESSION_EXPIRE_MINUTES: int = 30
    SESSION_MAX_HISTORY: int = 20
    
    # 时区配置
    DEFAULT_TIMEZONE: str = "Asia/Shanghai"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
