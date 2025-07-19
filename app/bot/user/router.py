from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.router import Router
from aiogram_dialog import DialogManager, StartMode
from pydantic import create_model
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.booking.state import BookingState
from app.bot.user.kbs import main_user_kb, user_booking_kb, cancel_book_kb
from app.bot.user.schemas import SUser
from app.config import broker
from app.dao.dao import UserDAO, BookingDAO


router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    session_with_commit: AsyncSession,
    state: FSMContext
):
    await state.clear()
    user_data = message.from_user
    user_id = user_data.id
    user_info = await UserDAO(
        session_with_commit
        ).find_one_or_none_by_id(user_id)
    if user_info is None:
        user_schema = SUser(
            id=user_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            username=user_data.username
            )
        await UserDAO(session_with_commit).add(user_schema)
    text = ('Здесь вы можете забронировать переговорную 🛗\n'
            'Используйте клавиатуру ниже, чтобы создать резерв 🔢')
    await message.answer(text, reply_markup=main_user_kb(user_id))


@router.callback_query(F.data == 'about_us')
async def cmd_about(call: CallbackQuery):
    await call.answer('О сервисе')
    about_text = ('🖥️ Бронирование переговорных')
    await call.message.edit_text(
        about_text,
        reply_markup=main_user_kb(call.from_user.id)
        )


@router.callback_query(F.data == 'book_meeting_room')
async def start_dialog(call: CallbackQuery, dialog_manager: DialogManager):
    await call.answer('Бронирование переговорной')
    await dialog_manager.start(
        state=BookingState.count,
        mode=StartMode.RESET_STACK
        )


@router.callback_query(F.data == 'my_bookings')
async def show_my_bookings(
    call: CallbackQuery,
    session_without_commit: AsyncSession
):
    await call.answer('Мои бронирования')
    user_filter = create_model(
        'UserIDModel',
        user_id=(int, ...)
        )(user_id=call.from_user.id)
    my_bookings = await BookingDAO(
        session_without_commit
        ).find_all(user_filter)
    count_booking = len(my_bookings)
    if count_booking:
        book = True
        text = (
            f'Отлично! У вас {count_booking} '
            f'забронированных переговорных. \n\n'
            f'Чтобы просмотреть детали брони и, при необходимости, '
            f'отменить бронь, воспользуйтесь кнопками ниже.'
            )
    else:
        book = False
        text = ('У вас пока нет активных бронирований. \n\n'
                'Вы можете забронировать переговорную прямо сейчас, '
                'нажав на кнопку ниже.'
                )
    await call.message.edit_text(
        text,
        reply_markup=user_booking_kb(call.from_user.id, book)
        )


@router.callback_query(F.data == 'my_booking_all')
async def show_all_my_bookings(
    call: CallbackQuery,
    session_without_commit: AsyncSession
):
    await call.answer('Мои брони')
    user_bookings = await BookingDAO(
        session_without_commit
        ).get_bookings_with_details(call.from_user.id)

    if not user_bookings:
        await call.message.edit_text(
            'У вас пока нет активных бронирований.',
            reply_markup=None
            )
        return

    for i, booking in enumerate(user_bookings):
        # Форматируем дату и время для удобства чтения
        booking_date = booking.date.strftime('%d.%m.%Y')  # День.Месяц.Год
        start_time = booking.time_slot.start_time
        end_time = booking.time_slot.end_time
        booking_number = i + 1
        status = booking.status
        cancel = False
        home_page = False
        if status == 'booked':
            cancel = True
            status_text = 'Забронировано'
        elif status == 'canceled':
            status_text = 'Отменено'
        else:
            status_text = 'Завершено'
        message_text = (
            f'<b>Бронирование №{booking_number}:</b>\n\n'
            f'📅 <b>Дата:</b> {booking_date}\n'
            f'🕒 <b>Время:</b> {start_time} - {end_time}\n'
            f'🖥️ <b>Переговорная:</b> {booking.meeting_room.name}, '
            f'Вместимость: {booking.meeting_room.capacity}\n'
            f'ℹ️ <b>Описание:</b> {booking.meeting_room.description}\n'
            f'📌 <b>Статус:</b> {status_text}\n\n'
            )
        if booking_number == len(user_bookings):
            home_page = True
        await call.message.answer(
            message_text,
            reply_markup=cancel_book_kb(booking.id, cancel, home_page)
            )


@router.callback_query(F.data.startswith('cancel_book_'))
async def cancel_booking(
    call: CallbackQuery,
    session_with_commit: AsyncSession
):
    book_id = int(call.data.split('_')[-1])
    booking_dao = BookingDAO(session_with_commit)
    await booking_dao.cancel_book(book_id)
    await call.answer('Бронирование отменено!', show_alert=True)
    await broker.publish(
        f'Пользователь отменил запись о брони с ID {book_id}',
        'admin_msg'
        )
    await call.message.edit_reply_markup(reply_markup=cancel_book_kb(book_id))


@router.callback_query(F.data.startswith('dell_book_'))
async def delete_booking(
    call: CallbackQuery,
    session_with_commit: AsyncSession
):
    book_id = int(call.data.split('_')[-1])
    await BookingDAO(session_with_commit).delete_book(book_id)
    await call.answer('Запись о бронировании удалена!', show_alert=True)
    await broker.publish(
        f'Пользователь удалил запись о бронировании с ID {book_id}',
        'admin_msg'
        )
    await call.message.delete()


@router.callback_query(F.data == 'back_home')
async def back_home(call: CallbackQuery):
    await call.answer('Главное меню')
    await call.message.edit_text(
        'Выберите необходимое действие',
        reply_markup=main_user_kb(call.from_user.id)
        )
