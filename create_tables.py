import asyncio
from app.database import init_db
from app.models.user import User
from app.models.event import Event
from app.models.attendee import Attendee
from app.models.reminder import Reminder
from app.models.meeting import Meeting
from app.models.task import Task
from app.database import engine, Base

async def main():
    print("[DB] Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Run default user and seeding in init_db
    await init_db()
    print("[DB] Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
