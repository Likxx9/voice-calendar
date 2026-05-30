"""
Session Service
会话服务 - 多轮对话状态管理
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

import redis.asyncio as redis

from app.core.config import settings


class SessionService:
    """会话服务类"""
    
    def __init__(self):
        self.redis_client = None
        self.session_prefix = "session:"
        self.session_expire = settings.SESSION_EXPIRE_MINUTES * 60
    
    async def init_redis(self):
        """初始化Redis连接"""
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话状态"""
        if not self.redis_client:
            await self.init_redis()
        
        session_data = await self.redis_client.get(f"{self.session_prefix}{session_id}")
        
        if session_data:
            return json.loads(session_data)
        return None
    
    async def create_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """创建新会话"""
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)).isoformat(),
            "history": [],
            "current_draft": None,
            "context": {
                "address_book": {},
                "favorite_locations": {}
            }
        }
        
        await self.save_session(session_id, session)
        return session
    
    async def save_session(self, session_id: str, session: Dict[str, Any]):
        """保存会话状态"""
        if not self.redis_client:
            await self.init_redis()
        
        # 更新过期时间
        session["expires_at"] = (datetime.utcnow() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)).isoformat()
        
        await self.redis_client.setex(
            f"{self.session_prefix}{session_id}",
            self.session_expire,
            json.dumps(session)
        )
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加消息到会话历史"""
        session = await self.get_session(session_id)
        
        if not session:
            return None
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata
        }
        
        session["history"].append(message)
        
        # 限制历史长度
        if len(session["history"]) > settings.SESSION_MAX_HISTORY:
            session["history"] = session["history"][-settings.SESSION_MAX_HISTORY:]
        
        await self.save_session(session_id, session)
        return session
    
    async def update_draft(
        self,
        session_id: str,
        draft: Dict[str, Any]
    ):
        """更新当前事件草稿"""
        session = await self.get_session(session_id)
        
        if not session:
            return None
        
        # 合并草稿
        if session.get("current_draft"):
            session["current_draft"].update(draft)
        else:
            session["current_draft"] = draft
        
        await self.save_session(session_id, session)
        return session
    
    async def get_draft(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取当前事件草稿"""
        session = await self.get_session(session_id)
        
        if session:
            return session.get("current_draft")
        return None
    
    async def clear_draft(self, session_id: str):
        """清除事件草稿"""
        session = await self.get_session(session_id)
        
        if session:
            session["current_draft"] = None
            await self.save_session(session_id, session)
    
    async def update_context(
        self,
        session_id: str,
        context_update: Dict[str, Any]
    ):
        """更新会话上下文"""
        session = await self.get_session(session_id)
        
        if not session:
            return None
        
        session["context"].update(context_update)
        await self.save_session(session_id, session)
        return session
    
    async def delete_session(self, session_id: str):
        """删除会话"""
        if not self.redis_client:
            await self.init_redis()
        
        await self.redis_client.delete(f"{self.session_prefix}{session_id}")
    
    async def extend_session(self, session_id: str):
        """延长会话有效期"""
        session = await self.get_session(session_id)
        
        if session:
            await self.save_session(session_id, session)


# 全局会话服务实例
session_service = SessionService()
