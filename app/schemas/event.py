from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.models.event import EventStatus, EventPriority

class AttendeeCreate(BaseModel):
    name:   str   = Field(min_length=1, max_length=64)
    mobile: Optional[str] = None
    email:  Optional[str] = None

class ReminderCreate(BaseModel):
    minutes_before: int = Field(default=15, ge=1, le=10080)   # 最多提前 7 天
    method: str = "push"

class EventCreate(BaseModel):
    title:       str           = Field(min_length=1, max_length=256)
    start_time:  datetime
    end_time:    datetime
    is_all_day:  bool          = False
    location:    Optional[str] = None
    description: Optional[str] = None
    priority:    EventPriority = EventPriority.MEDIUM
    recurrence:  Optional[str] = None
    attendees:   List[AttendeeCreate] = []
    reminders:   List[ReminderCreate] = [] # Changed from [ReminderCreate()] to avoid default instance issues
    color:       Optional[str] = None

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time 必须晚于 start_time")
        return v

class EventUpdate(BaseModel):
    title:       Optional[str]           = None
    start_time:  Optional[datetime]      = None
    end_time:    Optional[datetime]      = None
    location:    Optional[str]           = None
    description: Optional[str]          = None
    priority:    Optional[EventPriority] = None
    status:      Optional[EventStatus]   = None

class EventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id:          uuid.UUID
    title:       str
    start_time:  datetime
    end_time:    datetime
    is_all_day:  bool
    location:    Optional[str]
    status:      EventStatus
    priority:    EventPriority
    recurrence:  Optional[str]
    created_at:  datetime
    attendees:   List[dict] = []

class ConflictInfo(BaseModel):
    has_conflict:   bool
    conflicting_events: List[EventResponse] = []
    suggestion:     Optional[str] = None    # AI 建议调整方案

class FreeSlot(BaseModel):
    start_time: datetime
    end_time:   datetime
    duration_minutes: int
