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
