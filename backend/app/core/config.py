"""
Core configuration module
核心配置模块
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    APP_NAME: str = "Voice Calendar API"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置 - 开发环境使用SQLite
    DATABASE_URL: str = "sqlite+aiosqlite:///./voice_calendar.db"

    # Redis配置 - 开发环境使用内存缓存
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080"
    ]

    # LLM配置 - 双模型路由（技术文档 §3.1.3）
    # 简单规划使用 Haiku，复杂规划使用 Sonnet
    LLM_MODEL: str = "qwen-2.5-7b"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "http://localhost:11434"

    # Agent LLM 配置 - Anthropic Claude 双模型路由（技术文档 §3.1.3）
    AGENT_LLM_PROVIDER: str = "anthropic"  # anthropic / local
    ANTHROPIC_API_KEY: str = ""
    AGENT_LLM_FAST_MODEL: str = "claude-haiku-4-5"  # 简单多意图规划，目标延迟 < 500ms
    AGENT_LLM_STRONG_MODEL: str = "claude-sonnet-4-6"  # 复杂依赖链规划，目标延迟 < 1500ms
    AGENT_LLM_LOCAL_MODEL: str = "qwen2.5-7b-instruct"  # 本地隐私敏感场景

    # 意图关联判断阈值（技术文档 §3.2.1）
    INTENT_EMBEDDING_SIMILARITY_THRESHOLD: float = 0.82
    INTENT_LLM_CONFIDENCE_THRESHOLD: float = 0.7

    # 联网搜索配置（技术文档 §4）
    SEARCH_PROVIDER: str = "tavily"  # tavily / serpapi / bing
    TAVILY_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""
    BING_SEARCH_API_KEY: str = ""
    SEARCH_CACHE_TTL_HOURS: int = 6

    # 工具超时与重试配置（技术文档 §3.3.2）
    TOOL_TIMEOUT_SEARCH_MS: int = 3000
    TOOL_TIMEOUT_CALENDAR_MS: int = 2000
    TOOL_TIMEOUT_MAP_MS: int = 4000
    TOOL_TIMEOUT_LLM_MS: int = 8000
    TOOL_TIMEOUT_REMINDER_MS: int = 1000
    TOOL_RETRY_SEARCH: int = 2
    TOOL_RETRY_CALENDAR: int = 3
    TOOL_RETRY_REMINDER: int = 5

    # STT配置 - 云端: 讯飞/SenseVoice；离线: FunASR/Paraformer + Sherpa-onnx
    STT_MODEL: str = "sensevoice-large"
    STT_LANGUAGE: str = "zh"

    # TTS配置 - 云端: 火山引擎/讯飞；离线: ChatTTS/Sherpa-onnx VITS
    TTS_MODEL: str = "volcano-tts"
    TTS_VOICE: str = "zh_female_shuangkuaisisi_moon_bigtts"

    # 会话配置（设计文档 §9.7 要求 5 分钟过期）
    SESSION_EXPIRE_MINUTES: int = 5
    SESSION_MAX_HISTORY: int = 20

    # 时区配置
    DEFAULT_TIMEZONE: str = "Asia/Shanghai"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
