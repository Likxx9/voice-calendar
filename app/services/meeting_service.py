from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.meeting import Meeting, MeetingPlatform
from app.models.event import Event

class MeetingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_meeting(self, user_id: uuid.UUID, event: Event, platform: MeetingPlatform) -> Meeting:
        meeting_url = None
        meeting_id_ext = None
        
        # Mock external API integration
        if platform == MeetingPlatform.DINGTALK:
            meeting_url = "https://meeting.dingtalk.com/j/mock_id"
            meeting_id_ext = "ding_mock_123"
        elif platform == MeetingPlatform.TENCENT:
            meeting_url = "https://meeting.tencent.com/j/mock_id"
            meeting_id_ext = "tencent_mock_123"
        else:
            meeting_url = "Offline"
            meeting_id_ext = "offline"

        meeting = Meeting(
            event_id       = event.id,
            organizer_id   = user_id,
            platform       = platform,
            meeting_url    = meeting_url,
            meeting_id_ext = meeting_id_ext,
        )
        self.db.add(meeting)
        await self.db.flush()
        return meeting

    async def get_meeting(self, meeting_id: uuid.UUID) -> Optional[Meeting]:
        from sqlalchemy import select
        result = await self.db.execute(select(Meeting).where(Meeting.id == meeting_id))
        return result.scalar_one_or_none()
