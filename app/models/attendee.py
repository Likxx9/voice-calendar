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
