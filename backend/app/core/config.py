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

    # LLM配置 - 国产模型双路由（技术文档 §3.1.3）
    # NLU语义解析：本地Ollama / 云端通义千问
    LLM_MODEL: str = "qwen2.5-7b-instruct"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "http://localhost:11434"  # Ollama本地服务

    # Agent LLM 配置 - 国产模型双路由（技术文档 §3.1.3）
    # 支持：alibaba(通义千问) / zhipu(智谱GLM) / local(本地Ollama)
    AGENT_LLM_PROVIDER: str = "alibaba"  # alibaba / zhipu / local
    
    # 通义千问配置（阿里云百炼平台）
    ALIBABA_API_KEY: str = ""  # 通义千问API密钥
    ALIBABA_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ALIBABA_FAST_MODEL: str = "qwen-turbo"       # 快速模型，目标延迟 < 500ms
    ALIBABA_STRONG_MODEL: str = "qwen-plus"      # 强力模型，目标延迟 < 1500ms
    
    # 智谱GLM配置（智谱AI开放平台）
    ZHIPU_API_KEY: str = ""  # 智谱API密钥
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPU_FAST_MODEL: str = "glm-4-flash"        # 快速模型
    ZHIPU_STRONG_MODEL: str = "glm-4-plus"       # 强力模型
    
    # 本地模型配置（Ollama）
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
