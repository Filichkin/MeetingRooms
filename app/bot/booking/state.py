from aiogram.fsm.state import StatesGroup, State


class BookingState(StatesGroup):
    count = State()
    meeting_room = State()
    booking_date = State()
    booking_time = State()
    confirmation = State()
    success = State()
