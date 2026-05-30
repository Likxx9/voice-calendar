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
