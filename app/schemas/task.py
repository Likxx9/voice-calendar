from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.task import TaskStatus, TaskPriority

class TaskCreate(BaseModel):
    title:       str           = Field(min_length=1, max_length=256)
    description: Optional[str] = None
    due_time:    Optional[datetime] = None
    priority:    TaskPriority = TaskPriority.MEDIUM

class TaskUpdate(BaseModel):
    title:       Optional[str] = None
    description: Optional[str] = None
    due_time:    Optional[datetime] = None
    status:      Optional[TaskStatus] = None
    priority:    Optional[TaskPriority] = None
