from aiogram_dialog import DialogManager


async def get_all_meeting_rooms(dialog_manager: DialogManager, **kwargs):
    """
    Получение списка переговорных с учетом выбранной вместимости.
    """
    meeting_rooms = dialog_manager.dialog_data['meeting_rooms']
    capacity = dialog_manager.dialog_data['capacity']
    return {
        'meeting_rooms': [
            meeting_room.to_dict() for meeting_room in meeting_rooms
            ],
        'text_meeting_room': f'Всего для {capacity} человек найдено '
        f'{len(meeting_rooms)} переговорных. Выберите нужную по описанию'
        }


async def get_all_available_slots(dialog_manager: DialogManager, **kwargs):
    """
    Получение списка доступных временных слотов
    для выбранной переговорной и даты.
    """
    selected_meeting_room = dialog_manager.dialog_data['selected_meeting_room']
    slots = dialog_manager.dialog_data['slots']
    text_slots = (
        f'Для переговорной {selected_meeting_room.name} найдено {len(slots)} '
        f'{"свободных слотов" if len(slots) != 1 else "свободный слот"}. '
        'Выберите удобное время'
    )
    return {
        'slots': [slot.to_dict() for slot in slots],
        'text_slots': text_slots
        }


async def get_confirmed_data(dialog_manager: DialogManager, **kwargs):
    """Получение списка переговорных с учетом выбранной вместимости."""
    selected_meeting_room = dialog_manager.dialog_data['selected_meeting_room']
    booking_date = dialog_manager.dialog_data['booking_date']
    selected_slot = dialog_manager.dialog_data['selected_slot']

    confirmed_text = (
        '<b>📅 Подтверждение бронирования</b>\n\n'
        f'<b>📆 Дата:</b> {booking_date}\n\n'
        f'<b>💻 Информация о переговорной:</b>\n'
        f'  - ❗️ Название переговорной: {selected_meeting_room.name}\n\n'
        f'  - 👥 Вместимость: {selected_meeting_room.capacity}\n'
        f'  - 📝 Описание: {selected_meeting_room.description}\n'
        f'<b>⏰ Время бронирования:</b>\n'
        f'  - С <i>{selected_slot.start_time}</i> '
        f'до <i>{selected_slot.end_time}</i>\n\n'
        '✅ Все ли верно?'
    )

    return {'confirmed_text': confirmed_text}
