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
