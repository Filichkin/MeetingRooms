import json
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.config import settings
from app.dao.dao import MeetingRoomDAO, TimeSlotUserDAO
from app.dao.database import async_session_maker


class MeetingRoomBase(BaseModel):
    name: str
    capacity: int
    description: str


class TimeSlotBase(BaseModel):
    start_time: str
    end_time: str


async def add_meeting_rooms_to_db(session: AsyncSession):
    with open(settings.MEETING_ROOMS_JSON, 'r', encoding='utf-8') as file:
        meeting_rooms_data = json.load(file)
    await MeetingRoomDAO(session).add_many(
        [
            MeetingRoomBase(**meeting_room)
            for meeting_room in meeting_rooms_data
            ]
        )


async def add_time_slots_to_db(session: AsyncSession):
    with open(settings.SLOTS_JSON, 'r', encoding='utf-8') as file:
        tables_data = json.load(file)
    await TimeSlotUserDAO(session).add_many(
        [
            TimeSlotBase(**table) for table in tables_data
            ]
        )


async def init_db():
    async with async_session_maker() as session:
        await add_meeting_rooms_to_db(session)
        await add_time_slots_to_db(session)
        await session.commit()
