"""
Calendar API Router
日历事件API路由
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.event import CalendarEvent
from app.models.user import User

router = APIRouter()


@router.get("/events")
async def get_events(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取日历事件列表"""
    query = select(CalendarEvent).where(
        CalendarEvent.user_id == user_id,
        CalendarEvent.deleted_at.is_(None)
    )
    
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        query = query.where(CalendarEvent.start_time >= start_dt)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        query = query.where(CalendarEvent.end_time <= end_dt)
    
    query = query.order_by(CalendarEvent.start_time)
    result = await db.execute(query)
    events = result.scalars().all()
    
    return {"events": [event.to_dict() for event in events]}


@router.get("/events/{event_id}")
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取单个事件详情"""
    query = select(CalendarEvent).where(CalendarEvent.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"event": event.to_dict()}


@router.post("/events")
async def create_event(
    event_data: dict,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """创建新事件"""
    event = CalendarEvent(
        user_id=user_id,
        title=event_data.get("title"),
        description=event_data.get("description"),
        location=event_data.get("location"),
        start_time=datetime.fromisoformat(event_data.get("start_time")),
        end_time=datetime.fromisoformat(event_data.get("end_time")),
        timezone=event_data.get("timezone", "Asia/Shanghai"),
        recurrence_rule=event_data.get("recurrence_rule"),
        participants=event_data.get("participants"),
        is_all_day=event_data.get("is_all_day", False),
        color=event_data.get("color"),
        reminder_minutes=event_data.get("reminder_minutes", 30)
    )
    
    db.add(event)
    await db.flush()
    
    return {"event": event.to_dict(), "message": "Event created successfully"}


@router.put("/events/{event_id}")
async def update_event(
    event_id: str,
    event_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """更新事件"""
    query = select(CalendarEvent).where(CalendarEvent.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # 更新字段
    for field, value in event_data.items():
        if hasattr(event, field) and value is not None:
            if field in ["start_time", "end_time"] and isinstance(value, str):
                value = datetime.fromisoformat(value)
            setattr(event, field, value)
    
    await db.flush()
    
    return {"event": event.to_dict(), "message": "Event updated successfully"}


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除事件（软删除）"""
    query = select(CalendarEvent).where(CalendarEvent.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.deleted_at = datetime.utcnow()
    await db.flush()
    
    return {"message": "Event deleted successfully"}


@router.get("/conflicts")
async def check_conflicts(
    start_time: str = Query(..., description="开始时间 ISO格式"),
    end_time: str = Query(..., description="结束时间 ISO格式"),
    user_id: str = Query(..., description="用户ID"),
    exclude_event_id: Optional[str] = Query(None, description="排除的事件ID"),
    db: AsyncSession = Depends(get_db)
):
    """检查时间冲突"""
    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time)
    
    # 查询时间重叠的事件
    query = select(CalendarEvent).where(
        CalendarEvent.user_id == user_id,
        CalendarEvent.deleted_at.is_(None),
        CalendarEvent.is_cancelled == False,
        # 时间重叠条件：新事件的开始时间 < 现有事件的结束时间 AND 新事件的结束时间 > 现有事件的开始时间
        and_(
            CalendarEvent.start_time < end_dt,
            CalendarEvent.end_time > start_dt
        )
    )
    
    if exclude_event_id:
        query = query.where(CalendarEvent.id != exclude_event_id)
    
    result = await db.execute(query)
    conflicts = result.scalars().all()
    
    return {
        "has_conflict": len(conflicts) > 0,
        "conflicts": [event.to_dict() for event in conflicts]
    }
