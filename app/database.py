from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select, func
from app.config import settings
import uuid
from datetime import datetime, timedelta

class Base(DeclarativeBase):
    pass

from sqlalchemy.pool import NullPool

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,
)

async def init_db():
    from app.models.user import User
    from app.models.event import Event

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    default_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == default_user_id))
        if not result.scalar_one_or_none():
            session.add(User(id=default_user_id, name="Test User"))
            await session.commit()

        count_result = await session.execute(
            select(func.count()).select_from(Event).where(Event.owner_id == default_user_id)
        )
        if count_result.scalar() == 0:
            await _seed_demo_events(session, default_user_id)


async def _seed_demo_events(session: AsyncSession, user_id: uuid.UUID):
    """Seed demo events matching the frontend calendar (week starts on Sunday)."""
    from app.models.event import Event, EventPriority

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Frontend calendar uses JS getDay(): 0=Sunday. Match that.
    js_day = (today.weekday() + 1) % 7  # Python Mon=0 → JS Sun=0
    sunday = today - timedelta(days=js_day)
    # col:1=Monday, col:2=Tuesday, col:3=Wednesday (matching store.js hardcoded events)
    mon = sunday + timedelta(days=1)
    tue = sunday + timedelta(days=2)
    wed = sunday + timedelta(days=3)

    demo_events = [
        {
            "title": "高管周会",
            "start_time": mon.replace(hour=9, minute=30),
            "end_time":   mon.replace(hour=11, minute=0),
            "location": "会议室A",
            "priority": EventPriority.HIGH,
        },
        {
            "title": "产品评审",
            "start_time": tue.replace(hour=13, minute=0),
            "end_time":   tue.replace(hour=15, minute=0),
            "location": "线上会议",
            "priority": EventPriority.MEDIUM,
        },
        {
            "title": "战略研讨会",
            "start_time": wed.replace(hour=10, minute=0),
            "end_time":   wed.replace(hour=12, minute=30),
            "location": "CEO办公室",
            "priority": EventPriority.HIGH,
        },
    ]

    for ev_data in demo_events:
        event = Event(
            owner_id=user_id,
            title=ev_data["title"],
            start_time=ev_data["start_time"],
            end_time=ev_data["end_time"],
            location=ev_data.get("location"),
            priority=ev_data["priority"],
        )
        session.add(event)

    await session.commit()
    print(f"[DB] 已创建 {len(demo_events)} 条演示日程 (Mon={mon.strftime('%m-%d')}, Tue={tue.strftime('%m-%d')}, Wed={wed.strftime('%m-%d')})")


AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
