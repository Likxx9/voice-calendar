import uuid
import re
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone, timedelta


def parse_local_time(raw: str) -> datetime:
    """
    将 LLM / 前端传入的时间字符串解析为 **本地 naive datetime**。
    LLM 输出的时间本质都是本地时间，但可能附带 Z 或 +XX:XX 后缀——
    这里统一剥掉时区信息，避免被误当成 UTC 而产生时差。
    """
    s = str(raw).strip()
    # 去掉尾部的 Z / +HH:MM / +HHMM / -HH:MM 等时区标记
    s = re.sub(r'[Zz]$', '', s)
    s = re.sub(r'[+-]\d{2}:\d{2}$', '', s)
    s = re.sub(r'[+-]\d{4}$', '', s)
    return datetime.fromisoformat(s)


def get_now() -> datetime:
    """返回当前时刻的 naive local datetime。"""
    return datetime.now()
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.schedule_service import ScheduleService
from app.services.meeting_service import MeetingService
from app.services.task_service import TaskService
from app.schemas.event import EventCreate, EventUpdate, AttendeeCreate, FreeSlot, ConflictInfo
from app.models.meeting import MeetingPlatform
from app.models.event import EventPriority
import json
from sqlalchemy import select
from app.models.event import Event


class BizDispatcher:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.schedule_svc = ScheduleService(db)
        self.meeting_svc  = MeetingService(db)
        self.task_svc     = TaskService(db)
        self.last_event_action = None
        self.pending_broadcasts = []

    def _queue_broadcast(self, event_type: str, data: dict):
        self.pending_broadcasts.append((event_type, data))

    def _broadcast_conflict(self, conflict: ConflictInfo, new_title: str):
        self._queue_broadcast("conflict_detected", {
            "new_event": new_title,
            "conflicting_events": [
                {"title": e.title, "start": e.start_time.isoformat(), "end": e.end_time.isoformat()}
                for e in conflict.conflicting_events[:5]
            ],
            "suggestion": conflict.suggestion,
        })

    def _broadcast_time_suggestion(self, title: str, start: datetime, end: datetime,
                                   free_slots: List[FreeSlot], reason: str):
        self._queue_broadcast("time_suggestion", {
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
            end_time = parse_local_time(slots['end_time'])
            
            return end_time
        duration = int(slots.get('duration_minutes', 60))
        return start_time + timedelta(minutes=duration)

    async def _find_free_slot(
        self, user_id: uuid.UUID, title: str = "", duration_minutes: int = 60,
        search_days: int = 3, search_from: datetime = None
    ) -> Tuple[Optional[datetime], Optional[datetime], List[FreeSlot]]:
        now = get_now()
        start = search_from if search_from and search_from > now else now
        range_end = start + timedelta(days=search_days)

        work_start = 9
        work_end = 18
        if any(k in title for k in ["晚饭", "晚餐", "晚上", "夜宵"]):
            work_start = 18
            work_end = 22
        elif any(k in title for k in ["早饭", "早餐", "早上", "晨间"]):
            work_start = 6
            work_end = 9
        elif any(k in title for k in ["午饭", "午餐", "中午"]):
            work_start = 11
            work_end = 14

        free_slots = await self.schedule_svc.get_free_slots(
            user_id, start, range_end, duration_minutes, work_start, work_end
        )

        # Filter out slots that have already passed or are too short after trimming
        valid_slots = []
        for slot in free_slots:
            effective_start = max(slot.start_time, start.replace(second=0, microsecond=0))
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
        is_fixed_time = slots.get('is_fixed_time', False)
        
        # Heuristically detect fixed time events if not explicitly set
        if any(k in title for k in ["高铁", "动车", "火车", "航班", "列车", "班次", "漫展", "展会"]):
            is_fixed_time = True

        if 'start_time' not in slots or not slots['start_time']:
            if is_fixed_time:
                raise ValueError(f'创建"{title}"失败：这是固定时间的行程，必须提供明确的时间（如发车/开始时间）。请您先确认好时间。')

            # 用户可能指定了日期但没指定具体时间，如"6月2号添加项目会议"
            target_date = None
            date_hint = slots.get('date') or slots.get('target_date')
            if date_hint:
                try:
                    target_date = parse_local_time(str(date_hint)).replace(hour=0, minute=0, second=0)
                except Exception:
                    pass

            start, end, free_slots = await self._find_free_slot(
                user_id, title, duration, search_from=target_date
            )
            if start is None:
                date_desc = f'{target_date.strftime("%m月%d日")}起' if target_date else '最近3天'
                raise ValueError(f'未能为"{title}"找到合适的空闲时间，{date_desc}的工作时段都已排满。')

            reason = f'用户指定{target_date.strftime("%m月%d日")}' if target_date else '用户未指定时间'
            self._broadcast_time_suggestion(title, start, end, free_slots, reason)
            note = f'已查看您的日程，推荐了 {start.strftime("%m月%d日 %H:%M")} 这个空闲时段。'
            return start, end, note

        start_time = parse_local_time(slots['start_time'])
        

        now = get_now()
        if start_time < now:
            start_time = start_time.replace(year=now.year, month=now.month, day=now.day)
            if start_time < now:
                start_time += timedelta(days=1)

        end_time = self._parse_end_time(slots, start_time)

        conflict = await self.schedule_svc.check_conflict(user_id, start_time, end_time)
        if not conflict.has_conflict:
            return start_time, end_time, ''

        conflict_names = '、'.join(e.title for e in conflict.conflicting_events[:3])
        self._broadcast_conflict(conflict, title)

        if is_fixed_time:
            raise ValueError(f'无法安排"{title}"，因为它与您的已有行程"{conflict_names}"发生冲突。由于这是固定时间行程，系统无法为您自动推延，请您考虑调整或选择其他车次/时间。')

        start, end, free_slots = await self._find_free_slot(user_id, title, duration)
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
        elif intent == "QUERY_SCHEDULE":
            return await self._handle_query_schedule(user_id, slots)
        elif intent == "CREATE_SCHEDULE":
            return await self._handle_create_schedule(user_id, slots)
        elif intent == "UPDATE_SCHEDULE":
            return await self._handle_update_schedule(user_id, slots)
        elif intent == "CANCEL_SCHEDULE":
            return await self._handle_cancel_schedule(user_id, slots)
        else:
            return f"暂时不支持的意图：{intent}"

    async def _handle_query_schedule(self, user_id: uuid.UUID, slots: Dict[str, Any]) -> str:
        try:
            date_str = slots.get('date')
            start_time = parse_local_time(date_str) if date_str else get_now()
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)
            
            events = await self.schedule_svc.list_events(user_id, start_time, end_time)
            date_desc = start_time.strftime("%m月%d日") if date_str else "今天"
            
            if not events:
                return f"{date_desc}您目前没有安排任何日程。"
            
            msg = f"{date_desc}您共有{len(events)}个日程安排：\n"
            for e in events:
                time_str = e.start_time.strftime("%H:%M")
                msg += f"- {time_str} {e.title}\n"
            return msg
        except Exception as e:
            print(f"[BizDispatcher] query_schedule error: {e}")
            return f"查询日程失败：{e}"

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
            self.last_event_action = {"type": "created", "title": title,
                                      "start_time": start_time.isoformat(), "end_time": end_time.isoformat()}
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
            self.last_event_action = {"type": "created", "title": title,
                                      "start_time": start_time.isoformat(), "end_time": end_time.isoformat()}

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
            now = get_now()
            duration = int(slots.get('duration_minutes', 60))

            raw_start = slots.get('time_range_start') or slots.get('start_time') or slots.get('date')
            raw_end = slots.get('time_range_end') or slots.get('end_time')

            if raw_start:
                start_time = parse_local_time(str(raw_start))
                
                if start_time < now:
                    start_time = now
            else:
                start_time = now

            if raw_end:
                end_time = parse_local_time(str(raw_end))
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

    async def _find_event_by_title(self, user_id, title_keyword: str, date_str: str = None) -> Optional[Event]:
        from sqlalchemy import and_, or_
        import re

        # 构建模糊搜索关键词列表
        keywords = [title_keyword]
        # 按分隔词拆分："杭州到上海" → ["杭州", "上海"]
        parts = re.split(r'[到去从→\-—、的]', title_keyword)
        parts = [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]
        if len(parts) >= 2:
            keywords.extend(parts)
        # 去除无意义后缀
        for suffix in ['的行程', '行程', '的日程', '日程', '的会议', '会议']:
            clean = title_keyword.replace(suffix, '').strip()
            if clean and clean != title_keyword and len(clean) >= 2:
                keywords.append(clean)

        unique_keywords = list(dict.fromkeys(keywords))
        print(f"[BizDispatcher] 搜索日程: keywords={unique_keywords}, date={date_str}")

        title_conditions = [Event.title.contains(kw) for kw in unique_keywords]

        # 第一步：只按标题搜索（不加日期过滤），找出所有匹配的活跃事件
        stmt = select(Event).where(and_(
            Event.owner_id == user_id,
            Event.is_deleted == False,
            or_(*title_conditions),
        )).order_by(Event.start_time.desc())
        result = await self.db.execute(stmt)
        candidates = list(result.scalars().all())
        print(f"[BizDispatcher] 标题匹配到 {len(candidates)} 条: {[(e.title, e.start_time.isoformat()) for e in candidates]}")

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # 第二步：多个匹配时用日期缩小范围
        if date_str:
            try:
                target_date = parse_local_time(date_str)
                day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                dated = [e for e in candidates if day_start <= e.start_time < day_end]
                if dated:
                    print(f"[BizDispatcher] 日期过滤后剩 {len(dated)} 条")
                    return dated[0]
                # 日期不精确匹配时，扩大到前后1天
                day_start_wide = day_start - timedelta(days=1)
                day_end_wide = day_end + timedelta(days=1)
                dated_wide = [e for e in candidates if day_start_wide <= e.start_time < day_end_wide]
                if dated_wide:
                    print(f"[BizDispatcher] 扩大日期范围(±1天)后匹配到 {len(dated_wide)} 条")
                    return dated_wide[0]
            except Exception as ex:
                print(f"[BizDispatcher] 日期解析异常: {ex}")

        # 没有日期或日期过滤无结果，返回最近的一条
        return candidates[0]

    async def _handle_update_schedule(self, user_id: uuid.UUID, slots: Dict[str, Any]) -> str:
        try:
            title_keyword = slots.get('title', '')
            if not title_keyword:
                return '请提供要修改的日程名称。'

            date_hint = slots.get('date') or slots.get('original_date')
            event = await self._find_event_by_title(user_id, title_keyword, date_hint)
            if not event:
                return f'未找到名称包含"{title_keyword}"的日程。'

            new_start = None
            new_end = None
            if 'new_start_time' in slots and slots['new_start_time']:
                new_start = parse_local_time(slots['new_start_time'])
                
            elif 'start_time' in slots and slots['start_time']:
                new_start = parse_local_time(slots['start_time'])
                

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
            self.last_event_action = {"type": "updated", "old_title": event.title,
                                      "title": updated.title,
                                      "start_time": updated.start_time.isoformat(),
                                      "end_time": updated.end_time.isoformat()}

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

            date_hint = slots.get('date') or slots.get('start_time')
            event = await self._find_event_by_title(user_id, title_keyword, date_hint)
            if not event:
                return f'未找到名称包含"{title_keyword}"的日程。'

            print(f"[BizDispatcher] 准备删除日程: '{event.title}' id={event.id}")
            deleted = await self.schedule_svc.delete_event(user_id, event.id)
            if not deleted:
                return '取消日程失败。'

            await self.db.commit()
            print(f"[BizDispatcher] 删除已提交到数据库")
            self.last_event_action = {
                "type": "deleted",
                "title": event.title,
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
            }
            return f'已取消日程"{event.title}"（{event.start_time.strftime("%m月%d日 %H:%M")}）。'
        except Exception as e:
            print(f"[BizDispatcher] cancel_schedule error: {e}")
            return '取消日程时发生错误。'
