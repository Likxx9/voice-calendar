from __future__ import annotations
import uuid
import asyncio
from datetime import datetime, timedelta, timezone

def ensure_naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)
    return dt

def get_now() -> datetime:
    return datetime.now()
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.event import Event, EventStatus
from app.models.reminder import Reminder
from app.models.attendee import Attendee
from app.schemas.event import EventCreate, EventUpdate, EventResponse, ConflictInfo, FreeSlot
from app.core.security import FieldEncryptor
from app.services.ai_service import AIService

# Dummy reminder function to replace celery
async def dummy_schedule_reminder(event_id: str, user_id: str, eta: datetime):
    print(f"[Dummy Celery Task] scheduled reminder for event {event_id} at {eta}")

class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db        = db
        self.encryptor = FieldEncryptor()
        self.ai        = AIService()

    # ── 创建日程 ───────────────────────────────────────────────
    async def create_event(self, user_id: uuid.UUID, data: EventCreate) -> Tuple[Event, ConflictInfo]:
        conflict = await self.check_conflict(
            user_id, data.start_time, data.end_time
        )

        event = Event(
            owner_id    = user_id,
            title       = data.title,
            description = data.description,
            start_time  = data.start_time,
            end_time    = data.end_time,
            is_all_day  = data.is_all_day,
            location    = data.location,
            priority    = data.priority,
            recurrence  = data.recurrence,
            color       = data.color,
        )
        self.db.add(event)
        await self.db.flush()   # 获取 event.id

        # 参会人（加密手机/邮箱）
        for att_data in data.attendees:
            attendee = Attendee(
                event_id         = event.id,
                name             = att_data.name,
                mobile_encrypted = self.encryptor.encrypt(att_data.mobile) if att_data.mobile else None,
                email_encrypted  = self.encryptor.encrypt(att_data.email)  if att_data.email  else None,
            )
            self.db.add(attendee)

        # 提醒
        for rem_data in data.reminders:
            remind_at = data.start_time - timedelta(minutes=rem_data.minutes_before)
            if remind_at > get_now():
                reminder = Reminder(
                    event_id       = event.id,
                    remind_at      = remind_at,
                    method         = rem_data.method,
                    minutes_before = rem_data.minutes_before,
                )
                self.db.add(reminder)
                asyncio.create_task(dummy_schedule_reminder(str(event.id), str(user_id), remind_at))

        await self.db.flush()
        return event, conflict

    # ── 查询日程 ───────────────────────────────────────────────
    async def list_events(
        self,
        user_id:    uuid.UUID,
        start_time: datetime,
        end_time:   datetime,
        status:     Optional[EventStatus] = None,
    ) -> List[Event]:
        """查询时间范围内的日程"""
        stmt = (
            select(Event)
            .where(
                and_(
                    Event.owner_id == user_id,
                    Event.is_deleted == False,
                    Event.start_time < end_time,
                    Event.end_time   > start_time,
                )
            )
            .order_by(Event.start_time)
        )
        if status:
            stmt = stmt.where(Event.status == status)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> Optional[Event]:
        stmt = select(Event).where(
            Event.id == event_id,
            Event.owner_id == user_id,
            Event.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ── 修改日程 ───────────────────────────────────────────────
    async def update_event(
        self, user_id: uuid.UUID, event_id: uuid.UUID, data: EventUpdate
    ) -> Optional[Event]:
        event = await self.get_event(user_id, event_id)
        if not event:
            return None

        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(event, field, value)

        if data.start_time or data.end_time:
            await self._reschedule_reminders(event)

        return event

    async def delete_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> bool:
        event = await self.get_event(user_id, event_id)
        if not event:
            print(f"[ScheduleService] delete_event: 未找到 event_id={event_id}")
            return False
        event.is_deleted = True
        event.status = EventStatus.CANCELLED
        await self.db.flush()
        print(f"[ScheduleService] delete_event: 已标记删除 '{event.title}' (id={event.id})")
        return True

    # ── 冲突检测 ───────────────────────────────────────────────
    async def check_conflict(
        self,
        user_id:    uuid.UUID,
        start_time: datetime,
        end_time:   datetime,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> ConflictInfo:
        stmt = select(Event).where(
            and_(
                Event.owner_id  == user_id,
                Event.is_deleted == False,
                Event.status    != EventStatus.CANCELLED,
                Event.start_time < end_time,
                Event.end_time   > start_time,
            )
        )
        if exclude_id:
            stmt = stmt.where(Event.id != exclude_id)

        result = await self.db.execute(stmt)
        conflicts = list(result.scalars().all())

        suggestion = None
        if conflicts:
            suggestion = await self.ai.suggest_reschedule(
                new_event_start=start_time,
                new_event_end=end_time,
                conflicting_events=conflicts,
            )

        conflict_responses = [
            EventResponse(
                id=e.id,
                title=e.title,
                start_time=e.start_time,
                end_time=e.end_time,
                is_all_day=e.is_all_day,
                location=e.location,
                status=e.status,
                priority=e.priority,
                recurrence=e.recurrence,
                created_at=e.created_at,
            )
            for e in conflicts
        ]

        return ConflictInfo(
            has_conflict       = len(conflicts) > 0,
            conflicting_events = conflict_responses,
            suggestion         = suggestion,
        )

    # ── 空闲时段计算 ───────────────────────────────────────────
    async def get_free_slots(
        self,
        user_id:          uuid.UUID,
        range_start:      datetime,
        range_end:        datetime,
        min_duration_min: int = 60,
        work_hour_start:  int = 9,
        work_hour_end:    int = 18,
    ) -> List[FreeSlot]:
        events = await self.list_events(user_id, range_start, range_end)
        busy: List[Tuple[datetime, datetime]] = sorted(
            [(e.start_time, e.end_time) for e in events],
            key=lambda x: x[0]
        )
        merged_busy: List[Tuple[datetime, datetime]] = []
        for start, end in busy:
            if merged_busy and start <= merged_busy[-1][1]:
                merged_busy[-1] = (merged_busy[-1][0], max(merged_busy[-1][1], end))
            else:
                merged_busy.append((start, end))

        free_slots: List[FreeSlot] = []
        cursor = range_start
        work_windows = self._get_work_windows(range_start, range_end, work_hour_start, work_hour_end)

        for win_start, win_end in work_windows:
            slot_cursor = max(cursor, win_start)
            for busy_start, busy_end in merged_busy:
                if busy_start >= win_end:
                    break
                if busy_end <= slot_cursor:
                    continue
                gap_min = int((busy_start - slot_cursor).total_seconds() / 60)
                if gap_min >= min_duration_min:
                    free_slots.append(FreeSlot(
                        start_time       = slot_cursor,
                        end_time         = busy_start,
                        duration_minutes = gap_min,
                    ))
                slot_cursor = max(slot_cursor, busy_end)

            tail_min = int((win_end - slot_cursor).total_seconds() / 60)
            if tail_min >= min_duration_min and slot_cursor < win_end:
                free_slots.append(FreeSlot(
                    start_time       = slot_cursor,
                    end_time         = win_end,
                    duration_minutes = tail_min,
                ))

        return free_slots[:10]

    def _get_work_windows(
        self, range_start: datetime, range_end: datetime,
        work_start: int, work_end: int,
    ) -> List[Tuple[datetime, datetime]]:
        windows = []
        current = range_start.replace(hour=work_start, minute=0, second=0, microsecond=0)
        while current < range_end:
            win_start = current
            win_end   = current.replace(hour=work_end)
            if win_end > range_start and win_start < range_end:
                windows.append((
                    max(win_start, range_start),
                    min(win_end, range_end),
                ))
            current += timedelta(days=1)
        return windows

    async def _reschedule_reminders(self, event: Event) -> None:
        stmt = select(Reminder).where(
            Reminder.event_id == event.id,
            Reminder.is_sent  == False,
        )
        result = await self.db.execute(stmt)
        reminders = result.scalars().all()
        for r in reminders:
            new_time = event.start_time - timedelta(minutes=r.minutes_before)
            r.remind_at = new_time
            asyncio.create_task(dummy_schedule_reminder(str(event.id), str(event.owner_id), new_time))
