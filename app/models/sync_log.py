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
