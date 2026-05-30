from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate

class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, user_id: uuid.UUID, data: TaskCreate, source_event_id: Optional[uuid.UUID] = None) -> Task:
        task = Task(
            owner_id        = user_id,
            title           = data.title,
            description     = data.description,
            due_time        = data.due_time,
            priority        = data.priority,
            source_event_id = source_event_id,
        )
        self.db.add(task)
        await self.db.flush()
        return task

    async def update_task(self, user_id: uuid.UUID, task_id: uuid.UUID, data: TaskUpdate) -> Optional[Task]:
        stmt = select(Task).where(Task.id == task_id, Task.owner_id == user_id, Task.is_deleted == False)
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            return None

        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        await self.db.flush()
        return task

    async def list_pending_tasks(self, user_id: uuid.UUID) -> List[Task]:
        stmt = select(Task).where(
            Task.owner_id == user_id,
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
            Task.is_deleted == False
        ).order_by(Task.due_time)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
