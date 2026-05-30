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

    # LLM配置 - 全部使用智谱GLM（技术文档 §3.1.3）
    # 智谱AI开放平台：https://open.bigmodel.cn/
    LLM_MODEL: str = "glm-4-flash"  # NLU语义解析模型
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"

    # Agent LLM 配置 - 智谱GLM
    AGENT_LLM_PROVIDER: str = "zhipu"  # zhipu
    AGENT_LLM_FAST_MODEL: str = "glm-4-flash"    # 快速模型，目标延迟 < 500ms
    AGENT_LLM_STRONG_MODEL: str = "glm-4-plus"   # 强力模型，目标延迟 < 1500ms
    
    # 智谱GLM配置
    ZHIPU_API_KEY: str = ""  # 智谱API密钥
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPU_FAST_MODEL: str = "glm-4-flash"        # 快速模型
    ZHIPU_STRONG_MODEL: str = "glm-4-plus"       # 强力模型

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

    # STT配置 - 科大讯飞语音听写（流式版）
    STT_MODEL: str = "xfyun"
    STT_LANGUAGE: str = "zh"
    XFYUN_APP_ID: str = "1bd4edcc"
    XFYUN_API_KEY: str = "ada0f065b298e19b349200aba86f2128"
    XFYUN_API_SECRET: str = "ZmQ1YTBjYWI5Zjk3NzZhYmFiZDMyMzg1"

    # 科大讯飞 API 配置
    XFYUN_APPID: str = ""
    XFYUN_API_KEY: str = ""
    XFYUN_API_SECRET: str = ""

    # TTS配置 - 云端: 火山引擎/讯飞
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
