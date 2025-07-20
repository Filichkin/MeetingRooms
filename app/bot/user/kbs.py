from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings


def main_user_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.add(InlineKeyboardButton(
        text='Забронировать переговорную',
        callback_data='book_meeting_room'
        )
    )
    kb.add(InlineKeyboardButton(
        text='📅 Мои брони',
        callback_data='my_bookings'
        )
    )
    kb.add(InlineKeyboardButton(
        text='ℹ️ Правила бронирования',
        callback_data='booking_rules'
        )
    )

    if user_id in settings.ADMIN_IDS:
        kb.add(InlineKeyboardButton(
            text='🔐 Админ-панель',
            callback_data='admin_panel'
            )
        )

    kb.adjust(1)
    return kb.as_markup()


def user_booking_kb(user_id: int, book: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if book:
        kb.add(InlineKeyboardButton(
            text='🎫 Мои бронирования',
            callback_data='my_booking_all'
            )
        )
    kb.add(InlineKeyboardButton(
        text='Забронировать переговорную',
        callback_data='book_meeting_room'
        )
    )
    kb.add(InlineKeyboardButton(
        text='🏠 На главную',
        callback_data='back_home'
        )
    )
    if user_id in settings.ADMIN_IDS:
        kb.add(InlineKeyboardButton(
            text='🔐 Админ-панель',
            callback_data='admin_panel'
            )
        )
    kb.adjust(1)
    return kb.as_markup()


def cancel_booking_kb(
        book_id: int,
        cancel: bool = False,
        home_page: bool = False
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if cancel:
        kb.add(InlineKeyboardButton(
            text='Отмена пронирования',
            callback_data=f'cancel_book_{book_id}'
            )
        )
    kb.add(InlineKeyboardButton(
        text='Удалить запись',
        callback_data=f'delete_book_{book_id}'
        )
    )
    if home_page:
        kb.add(InlineKeyboardButton(
            text='🏠 На главную',
            callback_data='back_home'
            )
        )
    kb.adjust(1)
    return kb.as_markup()
