"""
Calendar Event Model
日历事件模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, TSTZRANGE
from sqlalchemy.orm import relationship

from app.core.database import Base


class CalendarEvent(Base):
    """日历事件表"""
    __tablename__ = "calendar_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # 事件信息
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)
    
    # 时间信息
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(50), default="Asia/Shanghai")
    
    # 重复规则 (iCalendar RRULE)
    recurrence_rule = Column(Text, nullable=True)  # RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=WE
    
    # 参与者
    participants = Column(Text, nullable=True)  # JSON数组
    
    # 元数据
    is_all_day = Column(Boolean, default=False)
    color = Column(String(20), nullable=True)  # 事件颜色
    reminder_minutes = Column(Integer, default=30)  # 提前提醒分钟数
    
    # 状态
    is_completed = Column(Boolean, default=False)
    is_cancelled = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # 软删除
    
    # 索引
    __table_args__ = (
        Index("idx_events_user_time", "user_id", "start_time", "end_time"),
        Index("idx_events_timezone", "timezone"),
    )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "timezone": self.timezone,
            "recurrence_rule": self.recurrence_rule,
            "participants": self.participants,
            "is_all_day": self.is_all_day,
            "color": self.color,
            "reminder_minutes": self.reminder_minutes,
            "is_completed": self.is_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
