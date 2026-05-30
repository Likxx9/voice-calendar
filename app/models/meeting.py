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
