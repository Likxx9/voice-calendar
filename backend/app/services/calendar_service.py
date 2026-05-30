"""
Calendar Service
日历服务 - 事件管理、冲突检测、时间转换
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

import pytz
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import CalendarEvent
from app.core.config import settings


class CalendarService:
    """日历服务类"""
    
    def __init__(self):
        self.default_timezone = settings.DEFAULT_TIMEZONE
    
    async def create_event(
        self,
        db: AsyncSession,
        user_id: UUID,
        event_data: Dict[str, Any]
    ) -> CalendarEvent:
        """
        创建日历事件
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            event_data: 事件数据
        
        Returns:
            创建的事件对象
        """
        # 时区转换
        timezone = event_data.get("timezone", self.default_timezone)
        start_time = self._parse_datetime(event_data.get("start_time"), timezone)
        end_time = self._parse_datetime(event_data.get("end_time"), timezone)
        
        # 如果没有结束时间，默认1小时后
        if not end_time and start_time:
            end_time = start_time + timedelta(hours=1)
        
        event = CalendarEvent(
            user_id=user_id,
            title=event_data.get("title", "未命名事件"),
            description=event_data.get("description"),
            location=event_data.get("location"),
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            recurrence_rule=event_data.get("recurrence_rule"),
            participants=event_data.get("participants"),
            is_all_day=event_data.get("is_all_day", False),
            color=event_data.get("color"),
            reminder_minutes=event_data.get("reminder_minutes", 30)
        )
        
        db.add(event)
        await db.flush()
        
        return event
    
    async def check_conflicts(
        self,
        db: AsyncSession,
        user_id: UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_event_id: Optional[UUID] = None
    ) -> List[CalendarEvent]:
        """
        检查时间冲突
        
        使用PostgreSQL的TSTZRANGE重叠运算符进行高效查询
        """
        query = select(CalendarEvent).where(
            CalendarEvent.user_id == user_id,
            CalendarEvent.deleted_at.is_(None),
            CalendarEvent.is_cancelled == False,
            # 时间重叠条件
            and_(
                CalendarEvent.start_time < end_time,
                CalendarEvent.end_time > start_time
            )
        )
        
        if exclude_event_id:
            query = query.where(CalendarEvent.id != exclude_event_id)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_events_by_date_range(
        self,
        db: AsyncSession,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """获取日期范围内的事件"""
        query = select(CalendarEvent).where(
            CalendarEvent.user_id == user_id,
            CalendarEvent.deleted_at.is_(None),
            CalendarEvent.start_time >= start_date,
            CalendarEvent.end_time <= end_date
        ).order_by(CalendarEvent.start_time)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_today_events(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> List[CalendarEvent]:
        """获取今天的事件"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        return await self.get_events_by_date_range(db, user_id, today, tomorrow)
    
    def generate_alternatives(
        self,
        conflicts: List[CalendarEvent],
        requested_time: datetime,
        duration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        生成替代时间建议
        
        基于冲突事件的时间，寻找空闲时段
        """
        alternatives = []
        
        # 获取所有冲突事件的时间段
        busy_slots = [
            (e.start_time, e.end_time) for e in conflicts
        ]
        busy_slots.sort(key=lambda x: x[0])
        
        # 尝试在冲突前后寻找空闲时段
        check_times = [
            requested_time - timedelta(hours=1),
            requested_time + timedelta(hours=1),
            requested_time + timedelta(hours=2),
            requested_time - timedelta(days=1),
            requested_time + timedelta(days=1),
        ]
        
        for check_time in check_times:
            check_end = check_time + timedelta(minutes=duration_minutes)
            
            # 检查是否与任何冲突事件重叠
            has_conflict = False
            for busy_start, busy_end in busy_slots:
                if check_time < busy_end and check_end > busy_start:
                    has_conflict = True
                    break
            
            if not has_conflict:
                alternatives.append({
                    "start_time": check_time.isoformat(),
                    "end_time": check_end.isoformat(),
                    "reason": self._get_suggestion_reason(check_time, requested_time)
                })
                
                if len(alternatives) >= 3:
                    break
        
        return alternatives
    
    def _get_suggestion_reason(self, suggested: datetime, original: datetime) -> str:
        """生成建议原因"""
        diff = suggested - original
        
        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours > 0:
                return f"推迟{hours}小时"
            else:
                return f"提前{abs(hours)}小时"
        elif diff.days == 1:
            return "明天同一时间"
        elif diff.days == -1:
            return "昨天同一时间"
        else:
            return f"{diff.days}天后"
    
    def _parse_datetime(self, dt_str: str, timezone: str) -> Optional[datetime]:
        """解析日期时间字符串"""
        if not dt_str:
            return None
        
        try:
            # 尝试解析ISO格式
            dt = datetime.fromisoformat(dt_str)
            
            # 如果没有时区信息，添加指定时区
            if dt.tzinfo is None:
                tz = pytz.timezone(timezone)
                dt = tz.localize(dt)
            
            return dt
        except Exception as e:
            print(f"Error parsing datetime: {e}")
            return None
    
    def normalize_to_utc(self, dt: datetime, timezone: str) -> datetime:
        """将本地时间转换为UTC"""
        tz = pytz.timezone(timezone)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        return dt.astimezone(pytz.utc)
    
    def display_in_local(self, utc_dt: datetime, target_timezone: str) -> datetime:
        """将UTC时间转换为目标时区显示"""
        target_tz = pytz.timezone(target_timezone)
        return utc_dt.astimezone(target_tz)


# 全局日历服务实例
calendar_service = CalendarService()
