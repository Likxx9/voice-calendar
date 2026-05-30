"""
User Model
用户模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean

from app.core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 用户信息
    email = Column(String(255), unique=True, nullable=False, index=True)
    nickname = Column(String(100), nullable=False)
    avatar_url = Column(Text, nullable=True)
    
    # 个人字典（联系人、常用地点等）
    address_book = Column(Text, nullable=True)  # JSON: {"张总": ["张总", "张总经理"], ...}
    favorite_locations = Column(Text, nullable=True)  # JSON: {"丽思卡尔顿": ["丽思卡尔顿", "丽思卡尔顿酒店"], ...}
    
    # 偏好设置
    default_timezone = Column(String(50), default="Asia/Shanghai")
    tts_speed = Column(String(10), default="1.0")
    haptic_intensity = Column(String(20), default="medium")
    
    # 状态
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "default_timezone": self.default_timezone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
