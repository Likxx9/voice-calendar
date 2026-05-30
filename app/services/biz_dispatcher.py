import uuid
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.schedule_service import ScheduleService
from app.services.meeting_service import MeetingService
from app.services.task_service import TaskService
from app.schemas.event import EventCreate, EventUpdate, AttendeeCreate, FreeSlot, ConflictInfo
from app.models.meeting import MeetingPlatform
from app.models.event import EventPriority
import json
import notifier
from sqlalchemy import select
from app.models.event import Event


class BizDispatcher:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.schedule_svc = ScheduleService(db)
        self.meeting_svc  = MeetingService(db)
        self.task_svc     = TaskService(db)

    @staticmethod
    def _broadcast_conflict(conflict: ConflictInfo, new_title: str):
        notifier.broadcast("conflict_detected", {
            "new_event": new_title,
            "conflicting_events": [
                {"title": e.title, "start": e.start_time.isoformat(), "end": e.end_time.isoformat()}
                for e in conflict.conflicting_events[:5]
            ],
            "suggestion": conflict.suggestion,
        })

    @staticmethod
    def _broadcast_event_created(title: str, start: datetime, end: datetime):
        payload = {
            "title": title,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }
        print(f"[BizDispatcher] Broadcasting event_created: {payload}")
        notifier.broadcast("event_created", payload)

    @staticmethod
    def _broadcast_time_suggestion(title: str, start: datetime, end: datetime,
                                   free_slots: List[FreeSlot], reason: str):
        notifier.broadcast("time_suggestion", {
            "title": title,
            "suggested_start": start.isoformat(),
            "suggested_end": end.isoformat(),
            "reason": reason,
            "alternatives": [
                {"start": s.start_time.isoformat(), "end": s.end_time.isoformat(),
                 "duration_minutes": s.duration_minutes}
                for s in free_slots[:5]
            ],
        })

    def _parse_end_time(self, slots: Dict[str, Any], start_time: datetime) -> datetime:
        if 'end_time' in slots:
            return datetime.fromisoformat(slots['end_time'].replace("Z", "+00:00"))
        duration = int(slots.get('duration_minutes', 60))
        return start_time + timedelta(minutes=duration)

    async def _find_free_slot(
        self, user_id: uuid.UUID, duration_minutes: int = 60, search_days: int = 3
    ) -> Tuple[Optional[datetime], Optional[datetime], List[FreeSlot]]:
        now = datetime.now()
        range_end = now + timedelta(days=search_days)

        free_slots = await self.schedule_svc.get_free_slots(
            user_id, now, range_end, duration_minutes
        )

        # Filter out slots that have already passed or are too short after trimming
        valid_slots = []
        for slot in free_slots:
            effective_start = max(slot.start_time, now.replace(second=0, microsecond=0) + timedelta(minutes=1))
            if effective_start + timedelta(minutes=duration_minutes) <= slot.end_time:
                valid_slots.append(FreeSlot(
                    start_time=effective_start,
                    end_time=slot.end_time,
                    duration_minutes=int((slot.end_time - effective_start).total_seconds() / 60),
                ))
        free_slots = valid_slots

        if not free_slots:
            return None, None, []

        best = free_slots[0]
        suggested_start = best.start_time
        # Round up to next full hour for cleaner scheduling
        if suggested_start.minute != 0:
            suggested_start = suggested_start.replace(minute=0, second=0) + timedelta(hours=1)
        suggested_end = suggested_start + timedelta(minutes=duration_minutes)

        return suggested_start, suggested_end, free_slots

    async def _resolve_time(
        self, user_id: uuid.UUID, slots: Dict[str, Any], title: str
    ) -> Tuple[datetime, datetime, str]:
        """
        Resolve start/end time from slots.
        Returns (start_time, end_time, scheduling_note).
        scheduling_note is empty if user specified time, or describes what happened.
        """
        duration = int(slots.get('duration_minutes', 60))

        if 'start_time' not in slots or not slots['start_time']:
            start, end, free_slots = await self._find_free_slot(user_id, duration)
            if start is None:
                raise ValueError(f'未能为"{title}"找到合适的空闲时间，最近3天的工作时段都已排满。')
            self._broadcast_time_suggestion(title, start, end, free_slots, "用户未指定时间")
            note = f'您没有指定时间，我查看了您的日程，推荐了 {start.strftime("%m月%d日 %H:%M")} 这个空闲时段。'
            return start, end, note

        start_time = datetime.fromisoformat(slots['start_time'].replace("Z", "+00:00"))
        end_time = self._parse_end_time(slots, start_time)

        conflict = await self.schedule_svc.check_conflict(user_id, start_time, end_time)
        if not conflict.has_conflict:
            return start_time, end_time, ''

        conflict_names = '、'.join(e.title for e in conflict.conflicting_events[:3])
        self._broadcast_conflict(conflict, title)

        start, end, free_slots = await self._find_free_slot(user_id, duration)
        if start is None:
            note = f'该时段与"{conflict_names}"冲突，但未找到其他空闲时段，仍按原时间安排。'
            return start_time, end_time, note

        self._broadcast_time_suggestion(title, start, end, free_slots,
                                        f'原时间与"{conflict_names}"冲突，已自动调整')
        note = (f'原定时间与"{conflict_names}"存在冲突，'
                f'已自动调整到 {start.strftime("%m月%d日 %H:%M")} 的空闲时段。')
        return start, end, note

    async def dispatch(self, user_id: uuid.UUID, intent: str, slots: Dict[str, Any]) -> str:
        if intent == "CREATE_MEETING":
            return await self._handle_create_meeting(user_id, slots)
        elif intent == "QUERY_FREE_SLOT":
            return await self._handle_query_free_slot(user_id, slots)
        elif intent == "CREATE_SCHEDULE":
            return await self._handle_create_schedule(user_id, slots)
        elif intent == "UPDATE_SCHEDULE":
            return await self._handle_update_schedule(user_id, slots)
        elif intent == "CANCEL_SCHEDULE":
            return await self._handle_cancel_schedule(user_id, slots)
        else:
            return f"暂时不支持的意图：{intent}"

    async def _handle_create_schedule(self, user_id: uuid.UUID, slots: Dict[str, Any]) -> str:
        try:
            title = slots.get('title', '新日程')
            start_time, end_time, note = await self._resolve_time(user_id, slots, title)

            event_data = EventCreate(
                title=title,
                start_time=start_time,
                end_time=end_time,
                priority=EventPriority.MEDIUM
            )

            event, _ = await self.schedule_svc.create_event(user_id, event_data)
            await self.db.commit()
            self._broadcast_event_created(title, start_time, end_time)
            time_str = start_time.strftime('%m月%d日 %H:%M')

            if note:
                return f'{note}已帮您安排好"{title}"。'
            return f'好的，已经为您安排了"{title}"，时间是 {time_str}。'
        except ValueError as e:
            return str(e)
        except Exception as e:
            print(f"[BizDispatcher] create_schedule error: {e}")
            import traceback; traceback.print_exc()
            return f"抱歉，创建日程时发生了错误：{e}"

    async def _handle_create_meeting(self, user_id: uuid.UUID, slots: Dict[str, Any]) -> str:
        try:
            title = slots.get('title', '新会议')
            platform_str = slots.get('platform', 'dingtalk')

            start_time, end_time, note = await self._resolve_time(user_id, slots, title)

            platform = MeetingPlatform.DINGTALK
            if platform_str == 'tencent':
                platform = MeetingPlatform.TENCENT

            attendees_data = []
            for name in slots.get('attendees', []):
                attendees_data.append(AttendeeCreate(name=name))

            event_data = EventCreate(
                title=title,
                start_time=start_time,
                end_time=end_time,
                attendees=attendees_data
            )

            event, _ = await self.schedule_svc.create_event(user_id, event_data)
            meeting = await self.meeting_svc.create_meeting(user_id, event, platform)
            await self.db.commit()
            self._broadcast_event_created(title, start_time, end_time)

            time_str = start_time.strftime('%m月%d日 %H:%M')
            if note:
                return f'{note}已帮您预约{platform.value}会议"{title}"并发送邀请。'
            return f'好的，已经为您预约了{platform.value}会议："{title}"，时间 {time_str}，并发送了邀请。'
        except ValueError as e:
            return str(e)
        except Exception as e:
            print(f"[BizDispatcher] create_meeting error: {e}")
            import traceback; traceback.print_exc()
            return f"抱歉，创建会议时发生了错误：{e}"

    async def _handle_query_free_slot(self, user_id: uuid.UUID, slots: Dict[str, Any]) -> str:
        try:
            now = datetime.now()
            duration = int(slots.get('duration_minutes', 60))

            raw_start = slots.get('time_range_start') or slots.get('start_time') or slots.get('date')
            raw_end = slots.get('time_range_end') or slots.get('end_time')

            if raw_start:
                start_time = datetime.fromisoformat(str(raw_start).replace("Z", "+00:00"))
            else:
                start_time = now

            if raw_end:
                end_time = datetime.fromisoformat(str(raw_end).replace("Z", "+00:00"))
            else:
                end_time = start_time.replace(hour=0, minute=0, second=0) + timedelta(days=3)

            if end_time <= start_time:
                end_time = start_time + timedelta(days=1)

            free_slots = await self.schedule_svc.get_free_slots(user_id, start_time, end_time, duration)

            valid = [s for s in free_slots if s.end_time > now]
            if not valid:
                return f'{start_time.strftime("%m月%d日")} 至 {end_time.strftime("%m月%d日")} 没有足够的空闲时段。'

            lines = []
            for s in valid[:5]:
                day_str = s.start_time.strftime('%m月%d日')
                lines.append(f'{day_str} {s.start_time.strftime("%H:%M")}-{s.end_time.strftime("%H:%M")}，共{s.duration_minutes}分钟')

            return f'为您找到以下空闲时段：{"；".join(lines)}。'
        except Exception as e:
            print(f"[BizDispatcher] query_free_slot error: {e}")
            import traceback; traceback.print_exc()
            return f"查询空闲时段失败：{e}"

    async def _find_event_by_title(self, user_id, title_keyword: str) -> Optional[Event]:
        from sqlalchemy import and_
        stmt = select(Event).where(
            and_(
                Event.owner_id == user_id,
                Event.is_deleted == False,
                Event.title.contains(title_keyword),
            )
        ).order_by(Event.start_time.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _handle_update_schedule(self, user_id: uuid.UUID, slots: Dict[str, Any]) -> str:
        try:
            title_keyword = slots.get('title', '')
            if not title_keyword:
                return '请提供要修改的日程名称。'

            event = await self._find_event_by_title(user_id, title_keyword)
            if not event:
                return f'未找到名称包含"{title_keyword}"的日程。'

            new_start = None
            new_end = None
            if 'new_start_time' in slots and slots['new_start_time']:
                new_start = datetime.fromisoformat(slots['new_start_time'].replace("Z", "+00:00"))
            elif 'start_time' in slots and slots['start_time']:
                new_start = datetime.fromisoformat(slots['start_time'].replace("Z", "+00:00"))

            if new_start:
                duration = int(slots.get('duration_minutes', 0))
                if duration <= 0:
                    duration = int((event.end_time - event.start_time).total_seconds() / 60)
                new_end = new_start + timedelta(minutes=duration)

                conflict = await self.schedule_svc.check_conflict(
                    user_id, new_start, new_end, exclude_id=event.id
                )
                if conflict.has_conflict:
                    conflict_names = '、'.join(e.title for e in conflict.conflicting_events[:3])
                    return f'无法将"{event.title}"改到 {new_start.strftime("%m月%d日 %H:%M")}，该时段与"{conflict_names}"冲突。'

                update_data = EventUpdate(start_time=new_start, end_time=new_end)
            else:
                update_data = EventUpdate()
                if 'new_title' in slots:
                    update_data.title = slots['new_title']

            if 'location' in slots:
                update_data.location = slots['location']

            updated = await self.schedule_svc.update_event(user_id, event.id, update_data)
            if not updated:
                return '修改日程失败。'

            await self.db.commit()

            notifier.broadcast("event_updated", {
                "old_title": event.title,
                "title": updated.title,
                "start_time": updated.start_time.isoformat(),
                "end_time": updated.end_time.isoformat(),
            })

            time_str = updated.start_time.strftime('%m月%d日 %H:%M')
            return f'已将"{event.title}"调整到 {time_str}。'
        except Exception as e:
            print(f"[BizDispatcher] update_schedule error: {e}")
            import traceback; traceback.print_exc()
            return f'修改日程时发生错误：{e}'

    async def _handle_cancel_schedule(self, user_id: uuid.UUID, slots: Dict[str, Any]) -> str:
        try:
            title_keyword = slots.get('title', '')
            if not title_keyword:
                return '请提供要取消的日程名称。'

            event = await self._find_event_by_title(user_id, title_keyword)
            if not event:
                return f'未找到名称包含"{title_keyword}"的日程。'

            deleted = await self.schedule_svc.delete_event(user_id, event.id)
            if not deleted:
                return '取消日程失败。'

            await self.db.commit()
            return f'已取消日程"{event.title}"。'
        except Exception as e:
            print(f"[BizDispatcher] cancel_schedule error: {e}")
            return '取消日程时发生错误。'
