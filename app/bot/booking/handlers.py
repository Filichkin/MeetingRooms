from datetime import date

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram.types import CallbackQuery

from app.bot.booking.schemas import SCapacity, SNewBooking
from app.bot.user.kbs import main_user_kb
from app.config import broker
from app.dao.dao import BookingDAO, TimeSlotUserDAO, MeetingRoomDAO


async def cancel_logic(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
        ):
    await callback.answer('Сценарий бронирования отменен!')
    await callback.message.answer(
        'Вы отменили сценарий бронирования.',
        reply_markup=main_user_kb(callback.from_user.id)
        )


async def process_add_count_capacity(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
        ):
    """Обработчик выбора количества участников."""

    session = dialog_manager.middleware_data.get('session_without_commit')
    selected_capacity = int(button.widget_id)
    dialog_manager.dialog_data['capacity'] = selected_capacity
    dialog_manager.dialog_data[
        'meeting_rooms'
        ] = await MeetingRoomDAO(session).find_all(
            SCapacity(capacity=selected_capacity)
            )
    await callback.answer(f'Выбрано {selected_capacity} участников')
    await dialog_manager.next()


async def on_meeting_room_selected(
        callback: CallbackQuery,
        widget,
        dialog_manager: DialogManager,
        item_id: str
        ):
    """Обработчик выбора переговорной."""

    session = dialog_manager.middleware_data.get('session_without_commit')
    meeting_room_id = int(item_id)
    selected_meeting_room = await MeetingRoomDAO(
        session
        ).find_one_or_none_by_id(meeting_room_id)
    dialog_manager.dialog_data[
        'selected_meeting_room'
        ] = selected_meeting_room
    await callback.answer(
        f'Выбрана переговорная {selected_meeting_room.name} на '
        f'{selected_meeting_room.capacity} мест'
        )
    await dialog_manager.next()


async def process_date_selected(
        callback: CallbackQuery,
        widget,
        dialog_manager: DialogManager,
        selected_date: date
        ):
    """Обработчик выбора даты."""

    dialog_manager.dialog_data['booking_date'] = selected_date
    session = dialog_manager.middleware_data.get('session_without_commit')
    selected_meeting_room = dialog_manager.dialog_data['selected_meeting_room']
    slots = await BookingDAO(session).get_available_time_slots(
        meeting_room_id=selected_meeting_room.id,
        booking_date=selected_date
        )
    if slots:
        await callback.answer(f'Выбрана дата: {selected_date}')
        dialog_manager.dialog_data['slots'] = slots
        await dialog_manager.next()
    else:
        await callback.answer(
            f'Нет мест на {selected_date} для '
            f'переговорной{selected_meeting_room.name}!'
            )
        await dialog_manager.back()


async def process_slots_selected(
        callback: CallbackQuery,
        widget,
        dialog_manager: DialogManager,
        item_id: str
        ):
    """Обработчик выбора слота."""

    session = dialog_manager.middleware_data.get('session_without_commit')
    slot_id = int(item_id)
    selected_slot = await TimeSlotUserDAO(
        session
        ).find_one_or_none_by_id(slot_id)
    await callback.answer(
        f'Выбрано время с {selected_slot.start_time} '
        f'до {selected_slot.end_time}'
        )
    dialog_manager.dialog_data['selected_slot'] = selected_slot
    await dialog_manager.next()


async def on_confirmation(
        callback: CallbackQuery,
        widget, dialog_manager: DialogManager,
        **kwargs
        ):
    """Обработчик подтверждения бронирования."""

    session = dialog_manager.middleware_data.get('session_without_commit')

    # Получаем выбранные данные
    selected_meeting_room = dialog_manager.dialog_data['selected_meeting_room']
    selected_slot = dialog_manager.dialog_data['selected_slot']
    booking_date = dialog_manager.dialog_data['booking_date']
    user_id = callback.from_user.id
    check = await BookingDAO(session).check_available_bookings(
        meeting_room_id=selected_meeting_room.id,
        time_slot_id=selected_slot.id,
        booking_date=booking_date
        )
    if check:
        await callback.answer('Приступаю к сохранению')
        add_model = SNewBooking(
            user_id=user_id,
            meeting_room_id=selected_meeting_room.id,
            time_slot_id=selected_slot.id,
            date=booking_date,
            status='booked'
            )
        await BookingDAO(session).add(add_model)
        await callback.answer('Переговорная успешно забронирована!')
        text = (
            'Бронь успешно сохранена. '
            'Со списком своих броней можно ознакомиться '
            'в меню "МОИ БРОНИРОВАНИЯ"'
        )
        await callback.message.answer(text, reply_markup=main_user_kb(user_id))

        admin_text = (
            f'Пользователь с ID {callback.from_user.id} '
            f'забронировал переговорную {selected_meeting_room.name} '
            f'на {booking_date}. Время брони с {selected_slot.start_time} '
            f'до {selected_slot.end_time}'
            )
        await broker.publish(admin_text, 'admin_msg')
        await broker.publish(callback.from_user.id, 'user_notification')
        await dialog_manager.done()
    else:
        await callback.answer('Переговорные на этот слот уже заняты!')
        await dialog_manager.back()
