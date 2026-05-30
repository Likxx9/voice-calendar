from typing import List
from datetime import datetime

class AIService:
    async def suggest_reschedule(self, new_event_start: datetime, new_event_end: datetime, conflicting_events: List) -> str:
        # Mock AI suggestion
        return f"建议将原定日程推迟 {int((new_event_end - new_event_start).total_seconds()/60)} 分钟，以避免时间冲突。"
    
    async def generate_meeting_notes(self, title: str, transcript: str) -> dict:
        # Mock AI notes generation
        return {
            "notes": f"【{title}】会议纪要\n1. 会议主要讨论了系统重构事宜。\n2. 各方达成一致，本周启动重构。",
            "action_items": [
                {"title": "编写重构文档", "urgent": True},
                {"title": "测试系统迁移", "urgent": False}
            ]
        }
