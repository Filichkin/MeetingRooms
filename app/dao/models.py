from datetime import datetime

from sqlalchemy import BigInteger, String
from sqlalchemy import Integer, Date, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.dao.database import Base, str_uniq


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str_uniq]
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]
    bookings: Mapped[list['Booking']] = relationship(
        'Booking',
        back_populates='user'
        )


class MeetingRoom(Base):
    __tablename__ = 'meeting_rooms'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None]
    bookings: Mapped[list['Booking']] = relationship(
        'Booking',
        back_populates='table'
        )


class TimeSlot(Base):
    __tablename__ = 'time_slots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Используем String для времени,
    # так как SQLite не имеет встроенного типа Time
    # формат: HH:MM
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    # формат: HH:MM
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)

    bookings: Mapped[list['Booking']] = relationship(
        'Booking',
        back_populates='time_slot',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'TimeSlot(id={self.id}, {self.start_time}-{self.end_time})'


class Booking(Base):
    __tablename__ = 'bookings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('users.id')
        )
    meeting_room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('meeting_rooms.id')
        )
    time_slot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('time_slots.id')
        )
    date: Mapped[datetime] = mapped_column(Date)
    status: Mapped[str]
    user: Mapped['User'] = relationship(
        'User',
        back_populates='bookings'
        )
    table: Mapped['MeetingRoom'] = relationship(
        'MeetingRoom',
        back_populates='bookings'
        )
    time_slot: Mapped['TimeSlot'] = relationship(
        'TimeSlot',
        back_populates='bookings'
        )
