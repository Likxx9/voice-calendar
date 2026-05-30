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
