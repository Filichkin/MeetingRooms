from datetime import date, timedelta, timezone

from aiogram_dialog import Window
from aiogram_dialog.widgets.kbd import (
    Button,
    Group,
    ScrollingGroup,
    Select,
    Calendar,
    CalendarConfig,
    Back,
    Cancel
)
from aiogram_dialog.widgets.text import Const, Format

from app.bot.booking.getters import (
    get_all_meeting_rooms,
    get_all_available_slots,
    get_confirmed_data
)
from app.bot.booking.handlers import (
    cancel_logic,
    on_confirmation,
    on_meeting_room_selected,
    process_add_count_capacity,
    process_date_selected,
    process_slots_selected,
    )
from app.bot.booking.state import BookingState


def get_capacity_window() -> Window:
    """Окно выбора количества участников."""

    return Window(
        Const('Выберите количество участников:'),
        Group(
            *[Button(
                text=Const(str(i)),
                id=str(i),
                on_click=process_add_count_capacity
            ) for i in range(1, 11)],
            Cancel(Const('Отмена'), on_click=cancel_logic),
            width=2
        ),
        state=BookingState.count
    )


def get_meeting_room_window() -> Window:
    """Окно выбора переговорной."""

    return Window(
        Format('{text_meeting_room}'),
        ScrollingGroup(
            Select(
                Format(
                    'Переговорная {item[name]}'
                    ),
                id='selected_meeting_room',
                item_id_getter=lambda item: str(item['id']),
                items='meeting_rooms',
                on_click=on_meeting_room_selected,
            ),
            id='meeting_rooms_scrolling',
            width=1,
            height=1,
        ),
        Group(
            Back(Const('Назад')),
            Cancel(Const('Отмена'), on_click=cancel_logic),
            width=2
        ),
        getter=get_all_meeting_rooms,
        state=BookingState.meeting_room,
    )


def get_date_window() -> Window:
    """Окно выбора даты."""

    return Window(
        Const('На какой день бронируем переговорную?'),
        Calendar(
            id='cal',
            on_click=process_date_selected,
            config=CalendarConfig(
                firstweekday=0,
                timezone=timezone(timedelta(hours=3)),
                min_date=date.today()
            )
        ),
        Back(Const('Назад')),
        Cancel(Const('Отмена'), on_click=cancel_logic),
        state=BookingState.booking_date,
    )


def get_slots_window() -> Window:
    """Окно выбора слота."""

    return Window(
        Format('{text_slots}'),
        ScrollingGroup(
            Select(
                Format('{item[start_time]} до {item[end_time]}'),
                id='slotes_select',
                item_id_getter=lambda item: str(item['id']),
                items='slots',
                on_click=process_slots_selected,
            ),
            id='slotes_scrolling',
            width=2,
            height=3,
        ),
        Back(Const('Назад')),
        Cancel(Const('Отмена'), on_click=cancel_logic),
        getter=get_all_available_slots,
        state=BookingState.booking_time,
    )


def get_confirmed_windows():
    return Window(
        Format('{confirmed_text}'),
        Group(
            Button(Const('Все верно'), id='confirm', on_click=on_confirmation),
            Back(Const('Назад')),
            Cancel(Const('Отмена'), on_click=cancel_logic),
        ),
        state=BookingState.confirmation,
        getter=get_confirmed_data
    )
