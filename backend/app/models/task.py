"""
Todo Task Model
待办任务模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, ForeignKey, Index

from app.core.database import Base


class TodoTask(Base):
    """待办任务表"""
    __tablename__ = "todo_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # 任务信息
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # 时间信息
    due_date = Column(DateTime(timezone=True), nullable=True)  # 截止时间
    reminder_at = Column(DateTime(timezone=True), nullable=True)  # 提醒时间
    
    # 分类
    category = Column(String(100), nullable=True)  # 工作、生活、学习等
    priority = Column(String(20), default="medium")  # low, medium, high
    
    # 关联
    related_event_id = Column(String(36), nullable=True)  # 关联的日历事件
    
    # 状态
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # 软删除
    
    # 索引
    __table_args__ = (
        Index("idx_tasks_user_due", "user_id", "due_date"),
        Index("idx_tasks_priority", "priority"),
    )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "reminder_at": self.reminder_at.isoformat() if self.reminder_at else None,
            "category": self.category,
            "priority": self.priority,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
