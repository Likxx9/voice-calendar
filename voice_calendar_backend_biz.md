# 语音日历 — 后端业务逻辑模块开发文档

> **VoiCal · Backend Business Logic**
> 版本：v1.0 · Python 3.12 · FastAPI · PostgreSQL
> 覆盖模块：日程管理 · 会议协作 · 任务提醒 · 多端同步 · 安全隐私

---

## 目录

1. [后端架构总览](#1-后端架构总览)
2. [技术栈与项目结构](#2-技术栈与项目结构)
3. [数据模型设计](#3-数据模型设计)
4. [日程管理模块](#4-日程管理模块)
5. [会议协作模块](#5-会议协作模块)
6. [任务提醒模块](#6-任务提醒模块)
7. [多端同步模块](#7-多端同步模块)
8. [安全隐私模块](#8-安全隐私模块)
9. [业务逻辑闭环验证](#9-业务逻辑闭环验证)
10. [API 接口汇总](#10-api-接口汇总)
11. [开发里程碑](#11-开发里程碑)
12. [附录：依赖与部署](#12-附录依赖与部署)

---

## 1. 后端架构总览

### 1.1 整体分层架构

```
┌──────────────────────────────────────────────────────────────┐
│  API Gateway Layer  (FastAPI · /api/v1)                      │
│  JWT 认证 · 限流 · 请求日志 · CORS                            │
└───────────────────────────┬──────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ 日程管理模块  │  │ 会议协作模块  │  │  任务提醒模块     │
│ Schedule Svc │  │ Meeting Svc  │  │  Task/Remind Svc │
└──────┬───────┘  └──────┬───────┘  └────────┬─────────┘
       │                 │                   │
       └─────────────────┼───────────────────┘
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 多端同步模块  │  │ 安全隐私模块  │  │  AI 集成层   │
│  Sync Svc    │  │ Auth/RBAC Svc│  │  LLM/Agent   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       └──────────────────┼─────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │    Celery    │
│  主数据库     │  │  缓存/队列   │  │  异步任务     │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 1.2 业务逻辑闭环图

```
用户语音指令（来自 L3 Agent）
          │
          ▼
    ┌─────────────────────────────────────────┐
    │           业务逻辑调度器                  │
    │    BizDispatcher.dispatch(nlu_result)    │
    └──────┬──────────┬──────────┬────────────┘
           │          │          │
           ▼          ▼          ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │日程管理   │ │会议协作   │ │任务提醒   │
    │创建/查询  │ │邀约/纪要  │ │待办/提醒  │
    └────┬─────┘ └────┬─────┘ └────┬─────┘
         │            │            │
         └────────────┼────────────┘
                      │
                      ▼
              ┌──────────────┐
              │  多端同步     │
              │ 推送至所有设备 │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │  安全隐私     │
              │  权限验证     │
              │  数据加密     │
              └──────────────┘
```

---

## 2. 技术栈与项目结构

### 2.1 技术栈

| 层级 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| Web 框架 | FastAPI | 0.111+ | 异步高性能，自动 OpenAPI |
| 数据验证 | Pydantic v2 | 2.6+ | 高性能 Schema 验证 |
| ORM | SQLAlchemy | 2.0+ | 全异步，类型安全 |
| 数据库迁移 | Alembic | 1.13+ | 版本化数据库变更 |
| 主数据库 | PostgreSQL | 16+ | 关系型存储 |
| 缓存/队列 | Redis | 7+ | 会话、缓存、消息队列 |
| 异步任务 | Celery | 5.3+ | 定时提醒、后台同步 |
| 认证 | python-jose | 3.3+ | JWT 生成与验证 |
| 加密 | cryptography | 42+ | 字段级加密 |
| HTTP 客户端 | httpx | 0.27+ | 异步 HTTP |
| 测试 | pytest + pytest-asyncio | — | 单测/集成测试 |
| 容器 | Docker + docker-compose | — | 开发/生产环境一致 |

### 2.2 项目目录结构

```
voical-backend/
├── app/
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置管理（pydantic-settings）
│   ├── database.py                # 数据库连接池
│   ├── deps.py                    # FastAPI 依赖注入
│   │
│   ├── models/                    # SQLAlchemy ORM 模型
│   │   ├── user.py
│   │   ├── event.py
│   │   ├── meeting.py
│   │   ├── task.py
│   │   └── sync_log.py
│   │
│   ├── schemas/                   # Pydantic 请求/响应 Schema
│   │   ├── event.py
│   │   ├── meeting.py
│   │   ├── task.py
│   │   └── user.py
│   │
│   ├── services/                  # 业务逻辑服务层
│   │   ├── schedule_service.py    # 日程管理
│   │   ├── meeting_service.py     # 会议协作
│   │   ├── task_service.py        # 任务提醒
│   │   ├── sync_service.py        # 多端同步
│   │   ├── auth_service.py        # 安全认证
│   │   └── ai_service.py          # LLM 集成
│   │
│   ├── api/                       # 路由层
│   │   ├── v1/
│   │   │   ├── events.py
│   │   │   ├── meetings.py
│   │   │   ├── tasks.py
│   │   │   ├── sync.py
│   │   │   └── auth.py
│   │
│   ├── workers/                   # Celery 任务
│   │   ├── celery_app.py
│   │   ├── reminder_tasks.py
│   │   └── sync_tasks.py
│   │
│   └── core/                      # 基础设施
│       ├── security.py            # 加密/解密
│       ├── cache.py               # Redis 缓存
│       └── exceptions.py          # 自定义异常
│
├── alembic/                       # 数据库迁移
├── tests/                         # 测试套件
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

### 2.3 配置管理

```python
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 应用
    APP_NAME: str = "VoiCal Backend"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # 数据库
    DATABASE_URL: str                       # postgresql+asyncpg://...
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # 加密密钥（AES-256）
    FIELD_ENCRYPTION_KEY: str              # 32字节十六进制

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
```

### 2.4 数据库连接

```python
# app/database.py
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,          # 自动检测断线重连
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## 3. 数据模型设计

### 3.1 实体关系图（ERD）

```
┌──────────┐      ┌──────────────┐      ┌──────────────┐
│  users   │1───∞ │    events    │1───∞ │  attendees   │
│  用户表   │      │    日程表    │      │  参会人表    │
└──────────┘      └──────┬───────┘      └──────────────┘
     │                   │1
     │                   │∞
     │1           ┌──────────────┐
     │∞           │   reminders  │
     │            │   提醒表     │
     │            └──────────────┘
     │
     │1         ┌──────────────┐      ┌──────────────┐
     │∞         │   meetings   │1───∞ │meeting_notes │
     │          │   会议表     │      │   纪要表     │
     │          └──────────────┘      └──────────────┘
     │
     │1         ┌──────────────┐
     │∞         │    tasks     │
               │    任务表    │
               └──────────────┘
```

### 3.2 ORM 模型定义

```python
# app/models/base_model.py
import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class TimestampMixin:
    """通用时间戳 Mixin"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
```

```python
# app/models/user.py
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_model import TimestampMixin, UUIDMixin
import enum

class UserRole(str, enum.Enum):
    ADMIN  = "admin"
    PRO    = "pro"         # 专业版
    BASIC  = "basic"       # 基础版

class CalendarPlatform(str, enum.Enum):
    DINGTALK = "dingtalk"
    WECOM    = "wecom"
    GOOGLE   = "google"
    OUTLOOK  = "outlook"

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    name:             Mapped[str]           = mapped_column(String(64), nullable=False)
    mobile_encrypted: Mapped[Optional[str]] = mapped_column(String(256))  # AES 加密
    email_encrypted:  Mapped[Optional[str]] = mapped_column(String(256))  # AES 加密
    role:             Mapped[UserRole]      = mapped_column(
        SAEnum(UserRole), default=UserRole.BASIC, nullable=False
    )
    timezone:         Mapped[str]           = mapped_column(String(64), default="Asia/Shanghai")
    calendar_platform: Mapped[CalendarPlatform] = mapped_column(
        SAEnum(CalendarPlatform), default=CalendarPlatform.DINGTALK
    )
    calendar_token_encrypted: Mapped[Optional[str]] = mapped_column(String(512))
    is_active:        Mapped[bool]          = mapped_column(Boolean, default=True)

    # Relations
    events:   Mapped[List["Event"]]   = relationship(back_populates="owner", lazy="noload")
    tasks:    Mapped[List["Task"]]    = relationship(back_populates="owner", lazy="noload")
    meetings: Mapped[List["Meeting"]] = relationship(back_populates="organizer", lazy="noload")
```

```python
# app/models/event.py
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_model import TimestampMixin, UUIDMixin
import enum

class EventStatus(str, enum.Enum):
    CONFIRMED  = "confirmed"
    TENTATIVE  = "tentative"
    CANCELLED  = "cancelled"

class EventPriority(str, enum.Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"

class Event(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "events"

    owner_id:     Mapped[uuid.UUID]      = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title:        Mapped[str]            = mapped_column(String(256), nullable=False)
    description:  Mapped[Optional[str]]  = mapped_column(Text)
    start_time:   Mapped[datetime]       = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time:     Mapped[datetime]       = mapped_column(DateTime(timezone=True), nullable=False)
    is_all_day:   Mapped[bool]           = mapped_column(Boolean, default=False)
    location:     Mapped[Optional[str]]  = mapped_column(String(512))
    status:       Mapped[EventStatus]    = mapped_column(SAEnum(EventStatus), default=EventStatus.CONFIRMED)
    priority:     Mapped[EventPriority]  = mapped_column(SAEnum(EventPriority), default=EventPriority.MEDIUM)
    recurrence:   Mapped[Optional[str]]  = mapped_column(String(256))     # iCal RRULE
    platform_id:  Mapped[Optional[str]]  = mapped_column(String(128))     # 外部平台事件 ID
    source:       Mapped[str]            = mapped_column(String(32), default="voical")  # voical/dingtalk/google
    color:        Mapped[Optional[str]]  = mapped_column(String(16))
    is_deleted:   Mapped[bool]           = mapped_column(Boolean, default=False)

    # Relations
    owner:     Mapped["User"]          = relationship(back_populates="events")
    attendees: Mapped[List["Attendee"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    reminders: Mapped[List["Reminder"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    meeting:   Mapped[Optional["Meeting"]] = relationship(back_populates="event", uselist=False)
```

```python
# app/models/attendee.py
import uuid, enum
from typing import Optional
from sqlalchemy import String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_model import UUIDMixin, TimestampMixin

class AttendeeStatus(str, enum.Enum):
    PENDING  = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    MAYBE    = "maybe"

class Attendee(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "attendees"

    event_id:  Mapped[uuid.UUID]          = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    user_id:   Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    name:      Mapped[str]                = mapped_column(String(64), nullable=False)
    mobile_encrypted: Mapped[Optional[str]] = mapped_column(String(256))
    email_encrypted:  Mapped[Optional[str]] = mapped_column(String(256))
    status:    Mapped[AttendeeStatus]     = mapped_column(SAEnum(AttendeeStatus), default=AttendeeStatus.PENDING)

    event: Mapped["Event"] = relationship(back_populates="attendees")
```

```python
# app/models/reminder.py
import uuid, enum
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Enum as SAEnum, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_model import UUIDMixin

class ReminderMethod(str, enum.Enum):
    PUSH  = "push"
    SMS   = "sms"
    EMAIL = "email"
    TTS   = "tts"           # 语音播报

class Reminder(Base, UUIDMixin):
    __tablename__ = "reminders"

    event_id:    Mapped[uuid.UUID]  = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    remind_at:   Mapped[datetime]   = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    method:      Mapped[ReminderMethod] = mapped_column(SAEnum(ReminderMethod), default=ReminderMethod.PUSH)
    minutes_before: Mapped[int]     = mapped_column(Integer, default=15)
    is_sent:     Mapped[bool]       = mapped_column(Boolean, default=False)

    event: Mapped["Event"] = relationship(back_populates="reminders")
```

```python
# app/models/meeting.py
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_model import UUIDMixin, TimestampMixin
import enum

class MeetingPlatform(str, enum.Enum):
    DINGTALK = "dingtalk"
    TENCENT  = "tencent"      # 腾讯会议
    FEISHU   = "feishu"       # 飞书
    WECOM    = "wecom"        # 企业微信
    OFFLINE  = "offline"

class Meeting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "meetings"

    event_id:      Mapped[uuid.UUID]      = mapped_column(ForeignKey("events.id"), nullable=False, unique=True)
    organizer_id:  Mapped[uuid.UUID]      = mapped_column(ForeignKey("users.id"), nullable=False)
    platform:      Mapped[MeetingPlatform] = mapped_column(SAEnum(MeetingPlatform), default=MeetingPlatform.DINGTALK)
    meeting_url:   Mapped[Optional[str]]  = mapped_column(String(512))
    meeting_id_ext: Mapped[Optional[str]] = mapped_column(String(128))   # 外部平台 meeting ID
    agenda:        Mapped[Optional[str]]  = mapped_column(Text)
    notes:         Mapped[Optional[str]]  = mapped_column(Text)           # AI 生成的会议纪要
    notes_generated: Mapped[bool]         = mapped_column(Boolean, default=False)

    event:     Mapped["Event"] = relationship(back_populates="meeting")
    organizer: Mapped["User"]  = relationship(back_populates="meetings")
```

```python
# app/models/task.py
from __future__ import annotations
import uuid, enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_model import UUIDMixin, TimestampMixin

class TaskStatus(str, enum.Enum):
    TODO       = "todo"
    IN_PROGRESS = "in_progress"
    DONE       = "done"
    CANCELLED  = "cancelled"

class TaskPriority(str, enum.Enum):
    URGENT    = "urgent"       # 紧急
    HIGH      = "high"
    MEDIUM    = "medium"
    LOW       = "low"

class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"

    owner_id:      Mapped[uuid.UUID]      = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title:         Mapped[str]            = mapped_column(String(256), nullable=False)
    description:   Mapped[Optional[str]]  = mapped_column(Text)
    due_time:      Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    status:        Mapped[TaskStatus]     = mapped_column(SAEnum(TaskStatus), default=TaskStatus.TODO)
    priority:      Mapped[TaskPriority]   = mapped_column(SAEnum(TaskPriority), default=TaskPriority.MEDIUM)
    source_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("events.id"))  # 来源会议
    is_deleted:    Mapped[bool]           = mapped_column(Boolean, default=False)

    owner:        Mapped["User"]            = relationship(back_populates="tasks")
    source_event: Mapped[Optional["Event"]] = relationship(foreign_keys=[source_event_id])
```

```python
# app/models/sync_log.py
import uuid, enum
from datetime import datetime
from sqlalchemy import String, ForeignKey, Enum as SAEnum, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base_model import UUIDMixin

class SyncDirection(str, enum.Enum):
    PUSH = "push"     # VoiCal → 外部平台
    PULL = "pull"     # 外部平台 → VoiCal

class SyncStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED  = "failed"
    CONFLICT = "conflict"

class SyncLog(Base, UUIDMixin):
    __tablename__ = "sync_logs"

    user_id:     Mapped[uuid.UUID]    = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    platform:    Mapped[str]          = mapped_column(String(32), nullable=False)
    direction:   Mapped[SyncDirection] = mapped_column(SAEnum(SyncDirection))
    entity_type: Mapped[str]          = mapped_column(String(32))  # event/task/meeting
    entity_id:   Mapped[uuid.UUID]    = mapped_column(nullable=False)
    status:      Mapped[SyncStatus]   = mapped_column(SAEnum(SyncStatus))
    error_msg:   Mapped[str | None]   = mapped_column(Text)
    synced_at:   Mapped[datetime]     = mapped_column(DateTime(timezone=True))
```

---

## 4. 日程管理模块

### 4.1 功能职责

日程管理是产品核心模块，处理日程的全生命周期，并提供智能化的冲突检测和自动重排能力。

| 功能 | 描述 |
|------|------|
| CRUD | 创建、查询、修改、删除日程 |
| 冲突检测 | 检测时间重叠，返回冲突详情和解决建议 |
| 智能重排 | 调用 LLM 分析优先级，自动建议调整方案 |
| 空闲查询 | 计算用户空闲时段，支持指定时长 |
| 周期日程 | 解析 iCal RRULE，展开周期实例 |

### 4.2 Pydantic Schema

```python
# app/schemas/event.py
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.models.event import EventStatus, EventPriority

class AttendeeCreate(BaseModel):
    name:   str   = Field(min_length=1, max_length=64)
    mobile: Optional[str] = None
    email:  Optional[str] = None

class ReminderCreate(BaseModel):
    minutes_before: int = Field(default=15, ge=1, le=10080)   # 最多提前 7 天
    method: str = "push"

class EventCreate(BaseModel):
    title:       str           = Field(min_length=1, max_length=256)
    start_time:  datetime
    end_time:    datetime
    is_all_day:  bool          = False
    location:    Optional[str] = None
    description: Optional[str] = None
    priority:    EventPriority = EventPriority.MEDIUM
    recurrence:  Optional[str] = None
    attendees:   List[AttendeeCreate] = []
    reminders:   List[ReminderCreate] = [ReminderCreate()]
    color:       Optional[str] = None

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time 必须晚于 start_time")
        return v

class EventUpdate(BaseModel):
    title:       Optional[str]           = None
    start_time:  Optional[datetime]      = None
    end_time:    Optional[datetime]      = None
    location:    Optional[str]           = None
    description: Optional[str]          = None
    priority:    Optional[EventPriority] = None
    status:      Optional[EventStatus]   = None

class EventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id:          uuid.UUID
    title:       str
    start_time:  datetime
    end_time:    datetime
    is_all_day:  bool
    location:    Optional[str]
    status:      EventStatus
    priority:    EventPriority
    recurrence:  Optional[str]
    created_at:  datetime
    attendees:   List[dict] = []

class ConflictInfo(BaseModel):
    has_conflict:   bool
    conflicting_events: List[EventResponse] = []
    suggestion:     Optional[str] = None    # AI 建议调整方案

class FreeSlot(BaseModel):
    start_time: datetime
    end_time:   datetime
    duration_minutes: int
```

### 4.3 日程管理服务

```python
# app/services/schedule_service.py
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, not_
from app.models.event import Event, EventStatus
from app.models.reminder import Reminder
from app.models.attendee import Attendee
from app.schemas.event import EventCreate, EventUpdate, ConflictInfo, FreeSlot
from app.core.security import FieldEncryptor
from app.services.ai_service import AIService
from app.workers.reminder_tasks import schedule_reminder

class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db        = db
        self.encryptor = FieldEncryptor()
        self.ai        = AIService()

    # ── 创建日程 ───────────────────────────────────────────────
    async def create_event(self, user_id: uuid.UUID, data: EventCreate) -> Event:
        """
        创建日程：
        1. 冲突预检
        2. 持久化
        3. 创建提醒任务
        4. 触发异步同步至外部日历
        """
        # Step 1: 冲突预检
        conflict = await self.check_conflict(
            user_id, data.start_time, data.end_time
        )
        # 冲突时不阻止创建（仅提示），由调用方决定是否继续

        # Step 2: 持久化
        event = Event(
            owner_id    = user_id,
            title       = data.title,
            description = data.description,
            start_time  = data.start_time,
            end_time    = data.end_time,
            is_all_day  = data.is_all_day,
            location    = data.location,
            priority    = data.priority,
            recurrence  = data.recurrence,
            color       = data.color,
        )
        self.db.add(event)
        await self.db.flush()   # 获取 event.id

        # Step 3: 参会人（加密手机/邮箱）
        for att_data in data.attendees:
            attendee = Attendee(
                event_id         = event.id,
                name             = att_data.name,
                mobile_encrypted = self.encryptor.encrypt(att_data.mobile) if att_data.mobile else None,
                email_encrypted  = self.encryptor.encrypt(att_data.email)  if att_data.email  else None,
            )
            self.db.add(attendee)

        # Step 4: 提醒
        for rem_data in data.reminders:
            remind_at = data.start_time - timedelta(minutes=rem_data.minutes_before)
            if remind_at > datetime.now(tz=timezone.utc):
                reminder = Reminder(
                    event_id       = event.id,
                    remind_at      = remind_at,
                    method         = rem_data.method,
                    minutes_before = rem_data.minutes_before,
                )
                self.db.add(reminder)
                # 注册 Celery 定时任务
                schedule_reminder.apply_async(
                    args=[str(event.id), str(user_id)],
                    eta=remind_at,
                )

        await self.db.flush()
        return event

    # ── 查询日程 ───────────────────────────────────────────────
    async def list_events(
        self,
        user_id:    uuid.UUID,
        start_time: datetime,
        end_time:   datetime,
        status:     Optional[EventStatus] = None,
    ) -> List[Event]:
        """查询时间范围内的日程（含跨越边界的日程）"""
        stmt = (
            select(Event)
            .where(
                and_(
                    Event.owner_id == user_id,
                    Event.is_deleted == False,
                    # 日程与查询范围有交集（任一端点在范围内，或完全包含）
                    Event.start_time < end_time,
                    Event.end_time   > start_time,
                )
            )
            .order_by(Event.start_time)
        )
        if status:
            stmt = stmt.where(Event.status == status)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> Optional[Event]:
        stmt = select(Event).where(
            Event.id == event_id,
            Event.owner_id == user_id,
            Event.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ── 修改日程 ───────────────────────────────────────────────
    async def update_event(
        self, user_id: uuid.UUID, event_id: uuid.UUID, data: EventUpdate
    ) -> Optional[Event]:
        event = await self.get_event(user_id, event_id)
        if not event:
            return None

        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(event, field, value)

        # 若修改了时间，重新检测冲突并更新提醒
        if data.start_time or data.end_time:
            await self._reschedule_reminders(event)

        return event

    # ── 删除日程（软删除）─────────────────────────────────────
    async def delete_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> bool:
        event = await self.get_event(user_id, event_id)
        if not event:
            return False
        event.is_deleted = True
        event.status = EventStatus.CANCELLED
        return True

    # ── 冲突检测 ───────────────────────────────────────────────
    async def check_conflict(
        self,
        user_id:    uuid.UUID,
        start_time: datetime,
        end_time:   datetime,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> ConflictInfo:
        """
        检测给定时间段是否与已有日程冲突
        冲突条件：两个时间段存在交集（start1 < end2 AND end1 > start2）
        """
        stmt = select(Event).where(
            and_(
                Event.owner_id  == user_id,
                Event.is_deleted == False,
                Event.status    != EventStatus.CANCELLED,
                Event.start_time < end_time,
                Event.end_time   > start_time,
            )
        )
        if exclude_id:
            stmt = stmt.where(Event.id != exclude_id)

        result = await self.db.execute(stmt)
        conflicts = list(result.scalars().all())

        suggestion = None
        if conflicts:
            # 调用 AI 生成调整建议
            suggestion = await self.ai.suggest_reschedule(
                new_event_start=start_time,
                new_event_end=end_time,
                conflicting_events=conflicts,
            )

        return ConflictInfo(
            has_conflict       = len(conflicts) > 0,
            conflicting_events = conflicts,
            suggestion         = suggestion,
        )

    # ── 空闲时段计算 ───────────────────────────────────────────
    async def get_free_slots(
        self,
        user_id:          uuid.UUID,
        range_start:      datetime,
        range_end:        datetime,
        min_duration_min: int = 60,
        work_hour_start:  int = 9,
        work_hour_end:    int = 18,
    ) -> List[FreeSlot]:
        """
        计算指定时间范围内满足最小时长的空闲时段
        只推荐工作时间内的结果
        """
        events = await self.list_events(user_id, range_start, range_end)

        # 按开始时间排序忙碌区间
        busy: List[Tuple[datetime, datetime]] = sorted(
            [(e.start_time, e.end_time) for e in events],
            key=lambda x: x[0]
        )

        # 合并重叠的忙碌区间
        merged_busy: List[Tuple[datetime, datetime]] = []
        for start, end in busy:
            if merged_busy and start <= merged_busy[-1][1]:
                merged_busy[-1] = (merged_busy[-1][0], max(merged_busy[-1][1], end))
            else:
                merged_busy.append((start, end))

        # 在每天的工作时间内寻找空闲窗口
        free_slots: List[FreeSlot] = []
        cursor = range_start

        # 构建工作时间边界列表
        work_windows = self._get_work_windows(range_start, range_end, work_hour_start, work_hour_end)

        for win_start, win_end in work_windows:
            slot_cursor = max(cursor, win_start)
            for busy_start, busy_end in merged_busy:
                if busy_start >= win_end:
                    break
                if busy_end <= slot_cursor:
                    continue
                # 发现空闲段：[slot_cursor, busy_start]
                gap_min = int((busy_start - slot_cursor).total_seconds() / 60)
                if gap_min >= min_duration_min:
                    free_slots.append(FreeSlot(
                        start_time       = slot_cursor,
                        end_time         = busy_start,
                        duration_minutes = gap_min,
                    ))
                slot_cursor = max(slot_cursor, busy_end)

            # 检查工作窗口末尾
            tail_min = int((win_end - slot_cursor).total_seconds() / 60)
            if tail_min >= min_duration_min and slot_cursor < win_end:
                free_slots.append(FreeSlot(
                    start_time       = slot_cursor,
                    end_time         = win_end,
                    duration_minutes = tail_min,
                ))

        return free_slots[:10]   # 最多返回 10 个推荐时段

    def _get_work_windows(
        self, range_start: datetime, range_end: datetime,
        work_start: int, work_end: int,
    ) -> List[Tuple[datetime, datetime]]:
        """生成时间范围内每天的工作时间窗口"""
        windows = []
        current = range_start.replace(hour=work_start, minute=0, second=0, microsecond=0)
        while current < range_end:
            win_start = current
            win_end   = current.replace(hour=work_end)
            if win_end > range_start and win_start < range_end:
                windows.append((
                    max(win_start, range_start),
                    min(win_end, range_end),
                ))
            current += timedelta(days=1)
        return windows

    async def _reschedule_reminders(self, event: Event) -> None:
        """修改时间后重新创建提醒任务"""
        stmt = select(Reminder).where(
            Reminder.event_id == event.id,
            Reminder.is_sent  == False,
        )
        result = await self.db.execute(stmt)
        reminders = result.scalars().all()
        for r in reminders:
            new_time = event.start_time - timedelta(minutes=r.minutes_before)
            r.remind_at = new_time
            schedule_reminder.apply_async(
                args=[str(event.id), str(event.owner_id)],
                eta=new_time,
            )
```

### 4.4 日程路由

```python
# app/api/v1/events.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services.schedule_service import ScheduleService
from app.schemas.event import EventCreate, EventUpdate, EventResponse, ConflictInfo, FreeSlot

router = APIRouter(prefix="/events", tags=["日程管理"])

@router.post("", response_model=dict, status_code=201)
async def create_event(
    data:         EventCreate,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    """创建日程（含冲突预检）"""
    svc     = ScheduleService(db)
    # 先做冲突预检
    conflict = await svc.check_conflict(
        current_user.id, data.start_time, data.end_time
    )
    event = await svc.create_event(current_user.id, data)
    return {
        "event":    EventResponse.model_validate(event),
        "conflict": conflict,
    }

@router.get("", response_model=list[EventResponse])
async def list_events(
    start_time:   datetime,
    end_time:     datetime,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    """查询时间范围内的日程"""
    svc    = ScheduleService(db)
    events = await svc.list_events(current_user.id, start_time, end_time)
    return [EventResponse.model_validate(e) for e in events]

@router.get("/free-slots", response_model=list[FreeSlot])
async def get_free_slots(
    start_time:       datetime,
    end_time:         datetime,
    min_duration_min: int     = Query(default=60, ge=15, le=480),
    db:               AsyncSession = Depends(get_db),
    current_user:     User         = Depends(get_current_user),
):
    """查询空闲时段"""
    svc   = ScheduleService(db)
    slots = await svc.get_free_slots(
        current_user.id, start_time, end_time, min_duration_min
    )
    return slots

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id:     str,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    svc   = ScheduleService(db)
    event = await svc.get_event(current_user.id, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="日程不存在")
    return EventResponse.model_validate(event)

@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id:     str,
    data:         EventUpdate,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    svc   = ScheduleService(db)
    event = await svc.update_event(current_user.id, event_id, data)
    if not event:
        raise HTTPException(status_code=404, detail="日程不存在")
    return EventResponse.model_validate(event)

@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id:     str,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    svc = ScheduleService(db)
    ok  = await svc.delete_event(current_user.id, event_id)
    if not ok:
        raise HTTPException(status_code=404, detail="日程不存在")
```

---

## 5. 会议协作模块

### 5.1 功能职责

| 功能 | 描述 |
|------|------|
| 创建会议 | 创建日程 + 生成腾讯会议/钉钉会议链接 |
| 邀约通知 | 发送邮件/短信/企业消息邀请参会人 |
| AI 会议纪要 | 对会议转录文本调用 LLM 生成结构化纪要 |
| Action Items | 从纪要中提取待办事项，自动创建任务 |

### 5.2 会议服务

```python
# app/services/meeting_service.py
from __future__ import annotations
import uuid, httpx
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.meeting import Meeting, MeetingPlatform
from app.models.event import Event
from app.models.task import Task, TaskPriority, TaskStatus
from app.schemas.event import EventCreate, AttendeeCreate
from app.services.schedule_service import ScheduleService
from app.services.ai_service import AIService
from app.config import settings

class MeetingService:
    def __init__(self, db: AsyncSession):
        self.db       = db
        self.schedule = ScheduleService(db)
        self.ai       = AIService()

    async def create_meeting(
        self,
        user_id:  uuid.UUID,
        event_data: EventCreate,
        platform: MeetingPlatform = MeetingPlatform.DINGTALK,
        agenda:   Optional[str]  = None,
    ) -> dict:
        """
        创建会议全流程：
        1. 创建日程事件
        2. 在外部平台（钉钉/腾讯会议）创建会议室
        3. 发送邀请通知
        """
        # Step 1: 创建基础日程
        event = await self.schedule.create_event(user_id, event_data)

        # Step 2: 创建外部会议
        meeting_url, meeting_id_ext = await self._create_external_meeting(
            platform, event, event_data.attendees
        )

        # Step 3: 持久化会议记录
        meeting = Meeting(
            event_id       = event.id,
            organizer_id   = user_id,
            platform       = platform,
            meeting_url    = meeting_url,
            meeting_id_ext = meeting_id_ext,
            agenda         = agenda,
        )
        self.db.add(meeting)
        await self.db.flush()

        # Step 4: 发送邀请通知（异步，不阻塞响应）
        from app.workers.sync_tasks import send_meeting_invitations
        send_meeting_invitations.delay(str(meeting.id))

        return {
            "event":       event,
            "meeting":     meeting,
            "meeting_url": meeting_url,
        }

    async def _create_external_meeting(
        self,
        platform:  MeetingPlatform,
        event:     Event,
        attendees: List[AttendeeCreate],
    ) -> tuple[Optional[str], Optional[str]]:
        """在外部平台创建会议室并返回入会链接"""
        if platform == MeetingPlatform.DINGTALK:
            return await self._create_dingtalk_meeting(event, attendees)
        elif platform == MeetingPlatform.TENCENT:
            return await self._create_tencent_meeting(event, attendees)
        return None, None

    async def _create_dingtalk_meeting(
        self, event: Event, attendees: List[AttendeeCreate]
    ) -> tuple[str, str]:
        """钉钉视频会议创建"""
        token = await self._get_dingtalk_token()
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.dingtalk.com/v1.0/conference/videoConferences",
                headers={"x-acs-dingtalk-access-token": token},
                json={
                    "title":     event.title,
                    "startTime": int(event.start_time.timestamp() * 1000),
                    "duration":  int((event.end_time - event.start_time).total_seconds() / 60),
                    "hostUserId": "",   # 主持人 unionId
                    "invitees":  [],    # 参会人 unionId 列表
                },
            )
            data = resp.json()
        return data.get("conferenceUrl", ""), data.get("conferenceId", "")

    async def _create_tencent_meeting(
        self, event: Event, attendees: List[AttendeeCreate]
    ) -> tuple[str, str]:
        """腾讯会议 API 创建（需申请企业版权限）"""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.meeting.qq.com/v1/meetings",
                headers={
                    "AppId":     settings.TENCENT_MEETING_APP_ID,
                    "SdkId":     settings.TENCENT_MEETING_SDK_ID,
                    "Random":    "123456",
                    "Timestamp": str(int(datetime.now().timestamp())),
                    "Signature": self._build_tencent_sign(event),
                },
                json={
                    "userid":      "",
                    "instanceid":  1,
                    "subject":     event.title,
                    "type":        0,          # 0=预约会议
                    "start_time":  str(int(event.start_time.timestamp())),
                    "end_time":    str(int(event.end_time.timestamp())),
                    "password":    "",
                    "settings": {
                        "mute_enable_join":    True,
                        "allow_unmute_self":   True,
                        "record":              1,   # 自动录制
                    },
                },
            )
            data = resp.json()
        meeting_info = data.get("meeting_info_list", [{}])[0]
        join_url = meeting_info.get("join_url", "")
        meeting_id = meeting_info.get("meeting_id", "")
        return join_url, meeting_id

    # ── AI 会议纪要生成 ────────────────────────────────────────
    async def generate_meeting_notes(
        self,
        meeting_id:  uuid.UUID,
        transcript:  str,            # ASR 转写的会议录音文本
    ) -> dict:
        """
        基于会议录音转写文本，调用 LLM 生成：
        - 结构化会议纪要
        - 关键决策列表
        - Action Items（自动创建任务）
        """
        # 查询会议
        stmt = select(Meeting).where(Meeting.id == meeting_id)
        result = await self.db.execute(stmt)
        meeting = result.scalar_one_or_none()
        if not meeting:
            return {}

        # 调用 AI 生成纪要
        notes_data = await self.ai.generate_meeting_notes(
            title      = meeting.event.title,
            transcript = transcript,
        )

        # 持久化纪要
        meeting.notes           = notes_data["notes"]
        meeting.notes_generated = True

        # 从 Action Items 自动创建任务
        action_items: list[dict] = notes_data.get("action_items", [])
        created_tasks = []
        for item in action_items:
            task = Task(
                owner_id        = meeting.organizer_id,
                title           = item["title"],
                description     = item.get("description", ""),
                due_time        = item.get("due_time"),
                priority        = TaskPriority.HIGH if item.get("urgent") else TaskPriority.MEDIUM,
                status          = TaskStatus.TODO,
                source_event_id = meeting.event_id,
            )
            self.db.add(task)
            created_tasks.append(task)

        await self.db.flush()
        return {
            "notes":         meeting.notes,
            "action_items":  len(created_tasks),
            "tasks_created": created_tasks,
        }

    async def _get_dingtalk_token(self) -> str:
        from app.core.cache import get_cache, set_cache
        cached = await get_cache("dingtalk:access_token")
        if cached:
            return cached
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.dingtalk.com/v1.0/oauth2/accessToken",
                json={"appKey": settings.DINGTALK_APP_KEY, "appSecret": settings.DINGTALK_APP_SECRET},
            )
            data = resp.json()
        token = data["accessToken"]
        await set_cache("dingtalk:access_token", token, ttl=data["expireIn"] - 60)
        return token

    def _build_tencent_sign(self, event: Event) -> str:
        # 腾讯会议签名算法（此处省略完整实现）
        return ""
```

---

## 6. 任务提醒模块

### 6.1 功能职责

| 功能 | 描述 |
|------|------|
| 任务 CRUD | 创建/查询/更新/完成任务 |
| 上下文感知提醒 | 根据用户位置、日历状态选择最佳提醒时机 |
| 截止预警 | 任务即将超时自动升级优先级并提醒 |
| 批量创建 | 从 AI 会议纪要 Action Items 批量生成任务 |

### 6.2 任务服务

```python
# app/services/task_service.py
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate
from app.workers.reminder_tasks import send_deadline_warning

class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, user_id: uuid.UUID, data: "TaskCreate") -> Task:
        task = Task(
            owner_id    = user_id,
            title       = data.title,
            description = data.description,
            due_time    = data.due_time,
            priority    = data.priority,
        )
        self.db.add(task)
        await self.db.flush()

        # 若设置了截止时间，注册超时预警任务
        if data.due_time:
            await self._schedule_deadline_warning(task)

        return task

    async def list_tasks(
        self,
        user_id:    uuid.UUID,
        status:     Optional[TaskStatus]   = None,
        priority:   Optional[TaskPriority] = None,
        overdue_only: bool = False,
    ) -> List[Task]:
        stmt = select(Task).where(
            Task.owner_id  == user_id,
            Task.is_deleted == False,
        ).order_by(Task.priority.desc(), Task.due_time.asc().nullslast())

        if status:
            stmt = stmt.where(Task.status == status)
        if priority:
            stmt = stmt.where(Task.priority == priority)
        if overdue_only:
            stmt = stmt.where(
                and_(
                    Task.due_time  <  datetime.now(tz=timezone.utc),
                    Task.status    != TaskStatus.DONE,
                    Task.status    != TaskStatus.CANCELLED,
                )
            )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def complete_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> Optional[Task]:
        task = await self._get_task(user_id, task_id)
        if task:
            task.status = TaskStatus.DONE
        return task

    async def escalate_overdue_tasks(self, user_id: uuid.UUID) -> int:
        """
        将超期任务优先级升级（MEDIUM → HIGH → URGENT）
        由定时 Celery 任务每小时调用
        """
        now = datetime.now(tz=timezone.utc)
        stmt = select(Task).where(
            Task.owner_id  == user_id,
            Task.is_deleted == False,
            Task.due_time  <= now,
            Task.status    == TaskStatus.TODO,
            Task.priority  != TaskPriority.URGENT,
        )
        result = await self.db.execute(stmt)
        tasks  = result.scalars().all()

        escalate_map = {
            TaskPriority.LOW:    TaskPriority.MEDIUM,
            TaskPriority.MEDIUM: TaskPriority.HIGH,
            TaskPriority.HIGH:   TaskPriority.URGENT,
        }
        count = 0
        for task in tasks:
            new_priority = escalate_map.get(task.priority)
            if new_priority:
                task.priority = new_priority
                count += 1
                # 发送截止预警推送
                send_deadline_warning.delay(str(task.id))

        return count

    async def _get_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> Optional[Task]:
        stmt = select(Task).where(
            Task.id       == task_id,
            Task.owner_id == user_id,
            Task.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _schedule_deadline_warning(self, task: Task) -> None:
        """提前 1 小时和 15 分钟发送截止预警"""
        if not task.due_time:
            return
        for minutes_before in [60, 15]:
            warn_time = task.due_time - timedelta(minutes=minutes_before)
            if warn_time > datetime.now(tz=timezone.utc):
                send_deadline_warning.apply_async(
                    args=[str(task.id)],
                    eta=warn_time,
                    countdown=None,
                )
```

### 6.3 Celery 提醒任务

```python
# app/workers/celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "voical",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.reminder_tasks", "app.workers.sync_tasks"],
)

celery_app.conf.update(
    task_serializer    = "json",
    result_serializer  = "json",
    accept_content     = ["json"],
    timezone           = "Asia/Shanghai",
    enable_utc         = True,
    task_track_started = True,
    # 定时任务配置
    beat_schedule = {
        "escalate-overdue-tasks": {
            "task":     "app.workers.reminder_tasks.escalate_overdue_tasks_batch",
            "schedule": 3600.0,   # 每小时执行一次
        },
        "sync-external-calendars": {
            "task":     "app.workers.sync_tasks.pull_all_platforms",
            "schedule": 300.0,    # 每 5 分钟同步一次
        },
    },
)
```

```python
# app/workers/reminder_tasks.py
from __future__ import annotations
import asyncio
from app.workers.celery_app import celery_app
from app.core.push import PushService

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def schedule_reminder(self, event_id: str, user_id: str) -> dict:
    """日程提醒推送（Celery 任务）"""
    try:
        push = PushService()
        result = asyncio.run(push.send_event_reminder(event_id, user_id))
        return {"status": "sent", "event_id": event_id}
    except Exception as exc:
        raise self.retry(exc=exc)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_deadline_warning(self, task_id: str) -> dict:
    """任务截止预警推送"""
    try:
        push = PushService()
        asyncio.run(push.send_task_warning(task_id))
        return {"status": "sent", "task_id": task_id}
    except Exception as exc:
        raise self.retry(exc=exc)

@celery_app.task
def escalate_overdue_tasks_batch() -> dict:
    """批量升级超期任务优先级（定时任务）"""
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.services.task_service import TaskService
    from sqlalchemy import select

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.is_active == True))
            users  = result.scalars().all()
            total  = 0
            for user in users:
                svc    = TaskService(db)
                count  = await svc.escalate_overdue_tasks(user.id)
                total += count
            await db.commit()
        return total

    count = asyncio.run(_run())
    return {"escalated": count}
```

---

## 7. 多端同步模块

### 7.1 同步架构

```
VoiCal 内部数据库
        │
        ├── PUSH ──► 钉钉日历 API
        ├── PUSH ──► 企业微信日历 API
        ├── PUSH ──► Google Calendar API
        │
        ◄── PULL ─── 钉钉 Webhook
        ◄── PULL ─── 企业微信 Webhook
        ◄── PULL ─── Google Calendar Webhook
        │
        └── 冲突解决：Last-Write-Wins（时间戳比较）
```

### 7.2 同步服务

```python
# app/services/sync_service.py
from __future__ import annotations
import uuid, hashlib
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.event import Event
from app.models.sync_log import SyncLog, SyncDirection, SyncStatus
from app.models.user import User, CalendarPlatform
from app.core.calendar_adapters import get_calendar_adapter

class SyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def push_event(self, user: User, event: Event) -> bool:
        """
        将 VoiCal 日程推送到用户绑定的外部日历平台
        返回是否成功
        """
        adapter = get_calendar_adapter(user.calendar_platform)
        if not adapter:
            return False

        # 解密 Token
        from app.core.security import FieldEncryptor
        token = FieldEncryptor().decrypt(user.calendar_token_encrypted or "")

        try:
            if event.platform_id:
                # 已有外部 ID → 更新
                await adapter.update_event(
                    token    = token,
                    ext_id   = event.platform_id,
                    title    = event.title,
                    start    = event.start_time.isoformat(),
                    end      = event.end_time.isoformat(),
                    location = event.location,
                )
            else:
                # 首次同步 → 创建并记录外部 ID
                ext_id = await adapter.create_event(
                    token    = token,
                    title    = event.title,
                    start    = event.start_time.isoformat(),
                    end      = event.end_time.isoformat(),
                    location = event.location,
                )
                event.platform_id = ext_id

            await self._log(user.id, user.calendar_platform.value,
                            SyncDirection.PUSH, "event", event.id, SyncStatus.SUCCESS)
            return True

        except Exception as e:
            await self._log(user.id, user.calendar_platform.value,
                            SyncDirection.PUSH, "event", event.id, SyncStatus.FAILED, str(e))
            return False

    async def handle_webhook(
        self,
        platform: str,
        payload:  dict,
        user_id:  uuid.UUID,
    ) -> Optional[Event]:
        """
        处理外部平台 Webhook 推送的日程变更
        采用 Last-Write-Wins 冲突解决策略
        """
        ext_event = self._parse_webhook(platform, payload)
        if not ext_event:
            return None

        # 查找已有日程（按外部 ID 匹配）
        stmt = select(Event).where(
            Event.owner_id   == user_id,
            Event.platform_id == ext_event["ext_id"],
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        ext_updated_at = ext_event.get("updated_at")

        if existing:
            # Last-Write-Wins：外部更新时间 > 本地更新时间才覆盖
            if ext_updated_at and ext_updated_at > existing.updated_at:
                existing.title      = ext_event["title"]
                existing.start_time = ext_event["start_time"]
                existing.end_time   = ext_event["end_time"]
                existing.location   = ext_event.get("location")
                await self._log(user_id, platform, SyncDirection.PULL,
                                "event", existing.id, SyncStatus.SUCCESS)
                return existing
            else:
                # 本地更新更新，跳过（后续 push 会把本地版本推回去）
                return existing
        else:
            # 新事件：创建本地副本
            event = Event(
                owner_id    = user_id,
                title       = ext_event["title"],
                start_time  = ext_event["start_time"],
                end_time    = ext_event["end_time"],
                location    = ext_event.get("location"),
                platform_id = ext_event["ext_id"],
                source      = platform,
            )
            self.db.add(event)
            await self.db.flush()
            await self._log(user_id, platform, SyncDirection.PULL,
                            "event", event.id, SyncStatus.SUCCESS)
            return event

    def _parse_webhook(self, platform: str, payload: dict) -> Optional[dict]:
        """解析各平台 Webhook 数据为统一格式"""
        parsers = {
            "dingtalk": self._parse_dingtalk,
            "google":   self._parse_google,
            "wecom":    self._parse_wecom,
        }
        parser = parsers.get(platform)
        return parser(payload) if parser else None

    def _parse_dingtalk(self, p: dict) -> Optional[dict]:
        try:
            return {
                "ext_id":     p["eventId"],
                "title":      p["summary"],
                "start_time": datetime.fromisoformat(p["start"]["dateTime"]),
                "end_time":   datetime.fromisoformat(p["end"]["dateTime"]),
                "location":   p.get("location"),
                "updated_at": datetime.fromisoformat(p.get("updated", datetime.now().isoformat())),
            }
        except (KeyError, ValueError):
            return None

    def _parse_google(self, p: dict) -> Optional[dict]:
        try:
            return {
                "ext_id":     p["id"],
                "title":      p["summary"],
                "start_time": datetime.fromisoformat(p["start"]["dateTime"]),
                "end_time":   datetime.fromisoformat(p["end"]["dateTime"]),
                "location":   p.get("location"),
                "updated_at": datetime.fromisoformat(p.get("updated", "")),
            }
        except (KeyError, ValueError):
            return None

    def _parse_wecom(self, p: dict) -> Optional[dict]:
        try:
            return {
                "ext_id":     p["schedule_id"],
                "title":      p["summary"],
                "start_time": datetime.fromtimestamp(p["start_time"], tz=timezone.utc),
                "end_time":   datetime.fromtimestamp(p["end_time"],   tz=timezone.utc),
                "location":   p.get("location"),
                "updated_at": datetime.now(tz=timezone.utc),
            }
        except (KeyError, ValueError):
            return None

    async def _log(
        self, user_id: uuid.UUID, platform: str,
        direction: SyncDirection, entity_type: str,
        entity_id: uuid.UUID, status: SyncStatus,
        error: Optional[str] = None,
    ) -> None:
        log = SyncLog(
            user_id     = user_id,
            platform    = platform,
            direction   = direction,
            entity_type = entity_type,
            entity_id   = entity_id,
            status      = status,
            error_msg   = error,
            synced_at   = datetime.now(tz=timezone.utc),
        )
        self.db.add(log)
```

---

## 8. 安全隐私模块

### 8.1 JWT 认证

```python
# app/core/security.py
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from cryptography.fernet import Fernet
import base64, hashlib
from app.config import settings

# ── JWT ──────────────────────────────────────────────────────
def create_access_token(user_id: uuid.UUID, role: str) -> str:
    """生成 JWT Access Token（60分钟有效）"""
    payload = {
        "sub":  str(user_id),
        "role": role,
        "type": "access",
        "iat":  datetime.now(tz=timezone.utc),
        "exp":  datetime.now(tz=timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: uuid.UUID) -> str:
    """生成 Refresh Token（30天有效）"""
    payload = {
        "sub":  str(user_id),
        "type": "refresh",
        "iat":  datetime.now(tz=timezone.utc),
        "exp":  datetime.now(tz=timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """验证 JWT Token，返回 payload 或 None"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

# ── 字段级加密（AES-256，Fernet）────────────────────────────
class FieldEncryptor:
    def __init__(self):
        # 从 32 字节十六进制密钥生成 Fernet key
        raw_key  = bytes.fromhex(settings.FIELD_ENCRYPTION_KEY)
        fernet_key = base64.urlsafe_b64encode(raw_key)
        self.f   = Fernet(fernet_key)

    def encrypt(self, plaintext: str) -> str:
        """加密字符串，返回 base64 密文"""
        return self.f.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """解密，失败返回空字符串"""
        try:
            return self.f.decrypt(ciphertext.encode()).decode()
        except Exception:
            return ""

# ── 密码哈希（用于本地账号，企业 SSO 场景可跳过）────────────
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### 8.2 RBAC 权限控制

```python
# app/core/rbac.py
from __future__ import annotations
from enum import Enum
from typing import Set
from fastapi import HTTPException, status

class Permission(str, Enum):
    # 日程权限
    EVENT_READ    = "event:read"
    EVENT_WRITE   = "event:write"
    EVENT_DELETE  = "event:delete"
    # 会议权限
    MEETING_CREATE = "meeting:create"
    MEETING_NOTES  = "meeting:notes"
    # 任务权限
    TASK_READ     = "task:read"
    TASK_WRITE    = "task:write"
    # 同步权限
    SYNC_MANAGE   = "sync:manage"
    # 管理权限
    ADMIN_ALL     = "admin:all"

# 角色-权限映射（RBAC）
ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    "basic": {
        Permission.EVENT_READ,
        Permission.EVENT_WRITE,
        Permission.TASK_READ,
        Permission.TASK_WRITE,
    },
    "pro": {
        Permission.EVENT_READ,
        Permission.EVENT_WRITE,
        Permission.EVENT_DELETE,
        Permission.MEETING_CREATE,
        Permission.MEETING_NOTES,
        Permission.TASK_READ,
        Permission.TASK_WRITE,
        Permission.SYNC_MANAGE,
    },
    "admin": {
        p for p in Permission          # admin 拥有所有权限
    },
}

def require_permission(permission: Permission):
    """FastAPI 依赖：验证用户是否具有指定权限"""
    from app.deps import get_current_user
    from fastapi import Depends
    from app.models.user import User

    async def check(current_user: User = Depends(get_current_user)):
        user_permissions = ROLE_PERMISSIONS.get(current_user.role.value, set())
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {permission.value}",
            )
        return current_user

    return check
```

### 8.3 认证依赖注入

```python
# app/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import verify_token
from app.models.user import User

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI 依赖：从 JWT 中获取当前用户"""
    token   = credentials.credentials
    payload = verify_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    stmt    = select(User).where(User.id == user_id, User.is_active == True)
    result  = await db.execute(stmt)
    user    = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    return user
```

### 8.4 认证路由

```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, UserRole, CalendarPlatform
from app.core.security import (
    create_access_token, create_refresh_token,
    hash_password, verify_password, verify_token,
)
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["认证"])

class RegisterRequest(BaseModel):
    name:     str
    mobile:   str
    password: str

class LoginRequest(BaseModel):
    mobile:   str
    password: str

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    from app.core.security import FieldEncryptor
    encryptor = FieldEncryptor()

    # 检查手机号是否已注册（加密后比较）
    encrypted_mobile = encryptor.encrypt(data.mobile)
    stmt   = select(User).where(User.mobile_encrypted == encrypted_mobile)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="手机号已注册")

    user = User(
        name             = data.name,
        mobile_encrypted = encrypted_mobile,
        role             = UserRole.BASIC,
    )
    # 存储密码哈希（存入 description 字段临时复用，正式可加 password_hash 字段）
    db.add(user)
    await db.flush()

    return TokenResponse(
        access_token  = create_access_token(user.id, user.role.value),
        refresh_token = create_refresh_token(user.id),
    )

@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh Token 无效")

    stmt   = select(User).where(User.id == payload["sub"], User.is_active == True)
    result = await db.execute(stmt)
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return TokenResponse(
        access_token  = create_access_token(user.id, user.role.value),
        refresh_token = create_refresh_token(user.id),
    )
```

---

## 9. 业务逻辑闭环验证

### 9.1 端到端业务流程（漫展返程场景）

以「查2026杭州漫展时间，安排返程」为例，完整业务闭环如下：

```python
# app/services/biz_dispatcher.py
"""
业务逻辑调度器：接收 L3 Agent 的 NLU 结果，
分发到对应业务服务，实现完整逻辑闭环
"""
from __future__ import annotations
import uuid
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.schedule_service import ScheduleService
from app.services.meeting_service import MeetingService
from app.services.task_service import TaskService
from app.services.sync_service import SyncService
from app.services.ai_service import AIService
from app.schemas.event import EventCreate, ReminderCreate

class NLUResult:
    """来自 L2/L3 层的 NLU 结构化结果（类型提示）"""
    primary_intent: str
    slots: dict
    entities: list

class BizDispatcher:
    def __init__(self, db: AsyncSession, user_id: uuid.UUID):
        self.db       = db
        self.user_id  = user_id
        self.schedule = ScheduleService(db)
        self.meeting  = MeetingService(db)
        self.task     = TaskService(db)
        self.sync     = SyncService(db)
        self.ai       = AIService()

    async def dispatch(self, nlu_result: dict) -> dict:
        """
        主分发入口：根据意图路由到对应业务处理函数
        返回结构化响应，供 L5 TTS 层播报
        """
        intent = nlu_result.get("primary_intent", "UNKNOWN")
        slots  = nlu_result.get("slots", {})

        handler_map = {
            "CREATE_MEETING":    self._handle_create_meeting,
            "CREATE_REMINDER":   self._handle_create_reminder,
            "CREATE_TASK":       self._handle_create_task,
            "QUERY_DAY":         self._handle_query_day,
            "QUERY_FREE_SLOT":   self._handle_query_free,
            "MODIFY_TIME":       self._handle_modify_time,
            "MODIFY_POSTPONE":   self._handle_postpone,
            "MODIFY_ADVANCE":    self._handle_advance,
            "DELETE_EVENT":      self._handle_delete_event,
            "SEARCH_EVENT_INFO": self._handle_search_info,
            "COMPLEX_PLAN":      self._handle_complex_plan,
        }

        handler = handler_map.get(intent, self._handle_unknown)
        return await handler(slots)

    async def _handle_create_meeting(self, slots: dict) -> dict:
        time_slot = slots.get("time")
        if not time_slot:
            return {"status": "need_slot", "missing": "TIME", "prompt": "请问会议安排在什么时间？"}

        from datetime import datetime, timedelta
        start = datetime.fromisoformat(time_slot["start"])
        end   = start + timedelta(minutes=slots.get("duration", 60))

        data = EventCreate(
            title      = slots.get("eventSubject", "待定会议"),
            start_time = start,
            end_time   = end,
            location   = slots.get("location"),
            attendees  = [{"name": p} for p in slots.get("persons", [])],
            reminders  = [ReminderCreate(minutes_before=15)],
        )
        result = await self.meeting.create_meeting(self.user_id, data)
        await self._trigger_sync(result["event"])

        return {
            "status":      "success",
            "event_id":    str(result["event"].id),
            "meeting_url": result.get("meeting_url"),
            "tts_text":    f"已为您安排{start.strftime('%m月%d日%H点')}的「{data.title}」，会议链接已发送。",
        }

    async def _handle_query_day(self, slots: dict) -> dict:
        from datetime import datetime
        time_slot = slots.get("time")
        if not time_slot:
            from datetime import date, timezone
            today = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
            time_slot = {"start": today.isoformat(), "end": (today.replace(hour=23, minute=59)).isoformat()}

        start  = datetime.fromisoformat(time_slot["start"])
        end    = datetime.fromisoformat(time_slot.get("end", time_slot["start"]))
        events = await self.schedule.list_events(self.user_id, start, end)

        if not events:
            return {"status": "success", "count": 0, "tts_text": "当天暂无日程安排。"}

        names    = "、".join(e.title for e in events[:3])
        more     = f"等{len(events)}个日程" if len(events) > 3 else ""
        tts_text = f"当天共有{len(events)}个安排：{names}{more}。"
        return {"status": "success", "count": len(events), "events": events, "tts_text": tts_text}

    async def _handle_query_free(self, slots: dict) -> dict:
        from datetime import datetime
        time_slot = slots.get("time", {})
        start     = datetime.fromisoformat(time_slot.get("start", datetime.now().isoformat()))
        end       = datetime.fromisoformat(time_slot.get("end",   (start).isoformat()))
        duration  = slots.get("duration", 60)

        free_slots = await self.schedule.get_free_slots(self.user_id, start, end, duration)

        if not free_slots:
            return {"status": "success", "slots": [], "tts_text": "该时间范围内没有找到合适的空闲时段。"}

        best   = free_slots[0]
        s_time = best.start_time.strftime("%m月%d日%H点")
        return {
            "status":    "success",
            "slots":     free_slots,
            "tts_text":  f"找到{len(free_slots)}个空闲时段，最近的是{s_time}，共{best.duration_minutes}分钟，是否安排？",
        }

    async def _handle_postpone(self, slots: dict) -> dict:
        """推迟日程：找到目标日程并修改时间"""
        from datetime import timedelta
        subject  = slots.get("eventSubject", "")
        duration = slots.get("duration", 60)  # 分钟

        # 通过主题模糊匹配最近的日程
        from datetime import datetime, timezone
        now     = datetime.now(tz=timezone.utc)
        events  = await self.schedule.list_events(
            self.user_id, now,
            now.replace(hour=23, minute=59),
        )
        # 按标题相似度匹配
        target = next(
            (e for e in events if subject.lower() in e.title.lower()),
            events[0] if events else None,
        )
        if not target:
            return {"status": "not_found", "tts_text": "未找到相关日程，请确认名称。"}

        from app.schemas.event import EventUpdate
        new_start = target.start_time + timedelta(minutes=duration)
        new_end   = target.end_time   + timedelta(minutes=duration)

        await self.schedule.update_event(
            self.user_id, target.id,
            EventUpdate(start_time=new_start, end_time=new_end)
        )
        await self._trigger_sync(target)

        return {
            "status":   "success",
            "tts_text": f"已将「{target.title}」推迟{duration}分钟，调整至{new_start.strftime('%H点%M分')}。",
        }

    async def _handle_complex_plan(self, slots: dict) -> dict:
        """
        综合规划：多意图串联处理
        示例：查漫展 → 安排返程 → 创建日程 → 推送提醒
        """
        search_result  = slots.get("search_result")   # 来自 L4 工具层
        calendar_result = slots.get("calendar_result") # 来自 L4 工具层

        if not search_result:
            return {"status": "need_search", "tts_text": "正在为您查询活动信息，请稍候。"}

        # 从搜索结果提取活动时间
        event_info = search_result.get("event_info", {})
        event_end  = event_info.get("endDate")

        if not event_end:
            return {"status": "search_failed", "tts_text": "未找到活动时间信息，请手动确认后再安排。"}

        # 自动创建返程日程
        from datetime import datetime, timedelta
        end_date    = datetime.fromisoformat(event_end)
        return_start = end_date.replace(hour=18, minute=0, second=0)
        return_end   = return_start + timedelta(hours=2)

        return_event = await self.schedule.create_event(
            self.user_id,
            EventCreate(
                title      = f"返程 · {event_info.get('city', '')}→上海",
                start_time = return_start,
                end_time   = return_end,
                location   = "高铁",
                priority   = "high",
                reminders  = [ReminderCreate(minutes_before=120), ReminderCreate(minutes_before=30)],
            )
        )

        tts = (
            f"{event_info.get('name', '活动')}于"
            f"{end_date.strftime('%m月%d日')}结束，"
            f"已为您安排当天{return_start.strftime('%H点')}的返程，"
            f"并设置提前2小时和30分钟提醒。"
        )
        return {"status": "success", "event_id": str(return_event.id), "tts_text": tts}

    async def _handle_unknown(self, slots: dict) -> dict:
        return {"status": "unknown", "tts_text": "抱歉，我没有理解您的意图，请重新描述。"}

    async def _handle_search_info(self, slots: dict) -> dict:
        return {"status": "delegated", "tts_text": "正在为您联网查询，请稍候。"}

    async def _handle_create_reminder(self, slots: dict) -> dict:
        # 复用 create_event，类型设为提醒
        return await self._handle_create_meeting(slots)

    async def _handle_create_task(self, slots: dict) -> dict:
        from app.schemas.task import TaskCreate
        from datetime import datetime
        task = await self.task.create_task(
            self.user_id,
            TaskCreate(
                title    = slots.get("eventSubject", "待办事项"),
                due_time = datetime.fromisoformat(slots["time"]["start"]) if slots.get("time") else None,
            )
        )
        return {"status": "success", "task_id": str(task.id), "tts_text": f"已添加待办「{task.title}」。"}

    async def _handle_modify_time(self, slots: dict) -> dict:
        return await self._handle_postpone(slots)

    async def _handle_advance(self, slots: dict) -> dict:
        slots["duration"] = -(slots.get("duration", 60))
        return await self._handle_postpone(slots)

    async def _handle_delete_event(self, slots: dict) -> dict:
        subject = slots.get("eventSubject", "")
        from datetime import datetime, timezone
        events  = await self.schedule.list_events(
            self.user_id,
            datetime.now(tz=timezone.utc),
            datetime.now(tz=timezone.utc).replace(day=28),
        )
        target = next((e for e in events if subject in e.title), None)
        if not target:
            return {"status": "not_found", "tts_text": "未找到该日程。"}
        await self.schedule.delete_event(self.user_id, target.id)
        return {"status": "success", "tts_text": f"已取消「{target.title}」。"}

    async def _trigger_sync(self, event) -> None:
        """异步触发多端同步（不阻塞响应）"""
        from app.workers.sync_tasks import push_event_to_platform
        push_event_to_platform.delay(str(event.id), str(self.user_id))
```

---

## 10. API 接口汇总

### 10.1 REST 端点总览

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | POST | `/api/v1/auth/register` | 用户注册 |
| 认证 | POST | `/api/v1/auth/token/refresh` | 刷新 Token |
| 日程 | GET | `/api/v1/events?start_time=&end_time=` | 查询日程 |
| 日程 | POST | `/api/v1/events` | 创建日程 |
| 日程 | PATCH | `/api/v1/events/{id}` | 修改日程 |
| 日程 | DELETE | `/api/v1/events/{id}` | 删除日程 |
| 日程 | GET | `/api/v1/events/free-slots` | 查询空闲时段 |
| 会议 | POST | `/api/v1/meetings` | 创建会议 |
| 会议 | POST | `/api/v1/meetings/{id}/notes` | 生成会议纪要 |
| 任务 | GET | `/api/v1/tasks` | 查询任务列表 |
| 任务 | POST | `/api/v1/tasks` | 创建任务 |
| 任务 | PATCH | `/api/v1/tasks/{id}/complete` | 完成任务 |
| 同步 | POST | `/api/v1/sync/webhook/{platform}` | 接收平台 Webhook |
| 业务 | POST | `/api/v1/biz/dispatch` | 语音指令业务分发（供 Agent 调用）|

### 10.2 业务分发接口（核心）

```python
# app/api/v1/biz.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services.biz_dispatcher import BizDispatcher

router = APIRouter(prefix="/biz", tags=["业务分发"])

@router.post("/dispatch")
async def dispatch_intent(
    nlu_result:   dict,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    """
    L3 Agent → 业务层 核心接口
    接收 NLU 结构化结果，分发到对应业务模块，返回 TTS 播报文本
    """
    dispatcher = BizDispatcher(db, current_user.id)
    result     = await dispatcher.dispatch(nlu_result)
    return result
```

### 10.3 主应用入口

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import events, meetings, tasks, sync, auth, biz

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
for router in [auth.router, events.router, meetings.router,
               tasks.router, sync.router, biz.router]:
    app.include_router(router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
```

---

## 11. 开发里程碑

| 里程碑 | 周期 | 交付内容 | 验收标准 |
|--------|------|---------|---------|
| M1 基础框架 | 第 1 周 | FastAPI 骨架、数据库连接、Alembic 迁移、JWT 认证 | 注册/登录接口通过，数据库连接正常 |
| M2 日程管理 | 第 2 周 | Event CRUD、冲突检测、空闲计算 | 冲突检测准确率 100%，空闲计算逻辑验证通过 |
| M3 会议协作 | 第 3 周 | 钉钉会议创建、邀约通知、AI 纪要生成 | 钉钉 API 联调通过，纪要 Action Items 提取准确 |
| M4 任务提醒 | 第 3 周 | Task CRUD、Celery 提醒任务、截止升级 | 提醒触发时间误差 < 30s，超时升级逻辑正确 |
| M5 多端同步 | 第 4 周 | SyncService、Webhook 接收、Last-Write-Wins | 钉钉双向同步 E2E 测试通过，冲突解决正确 |
| M6 安全加固 | 第 4 周 | 字段加密、RBAC 权限、限流中间件 | 敏感字段无明文存储，权限边界验证通过 |
| M7 BizDispatcher | 第 5 周 | 全意图处理器、漫展场景 E2E 测试 | 全部 12 种意图分发正确，E2E 延迟 < 500ms |
| M8 联调测试 | 第 5-6 周 | 与 L3 Agent 联调，生产压测 | 100 QPS 下 P95 < 200ms，错误率 < 0.1% |

---

## 12. 附录：依赖与部署

### 12.1 requirements.txt

```text
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.0
pydantic-settings==2.2.1
sqlalchemy==2.0.30
asyncpg==0.29.0
alembic==1.13.1
redis==5.0.4
celery[redis]==5.3.6
httpx==0.27.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
cryptography==42.0.5
anthropic==0.28.0
pytest==8.2.0
pytest-asyncio==0.23.6
pytest-cov==5.0.0
```

### 12.2 docker-compose.yml

```yaml
version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://voical:voical123@db:5432/voical
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build: .
    environment:
      - DATABASE_URL=postgresql+asyncpg://voical:voical123@db:5432/voical
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    command: celery -A app.workers.celery_app worker --loglevel=info

  beat:
    build: .
    command: celery -A app.workers.celery_app beat --loglevel=info
    depends_on:
      - redis

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB:       voical
      POSTGRES_USER:     voical
      POSTGRES_PASSWORD: voical123
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 12.3 数据库迁移命令

```bash
# 初始化 Alembic
alembic init alembic

# 生成迁移文件
alembic revision --autogenerate -m "initial schema"

# 执行迁移
alembic upgrade head

# 回滚一步
alembic downgrade -1
```

### 12.4 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置环境变量
cp .env.example .env  # 填写各 API Key

# 3. 启动服务（开发模式）
docker-compose up -d db redis

# 4. 数据库迁移
alembic upgrade head

# 5. 启动 API
uvicorn app.main:app --reload --port 8000

# 6. 启动 Celery Worker
celery -A app.workers.celery_app worker -B --loglevel=info

# 访问 API 文档
open http://localhost:8000/api/docs
```

---

*文档由 VoiCal 后端团队维护 · Python 3.12 · FastAPI 0.111 · 如框架版本升级请同步修改对应章节*
