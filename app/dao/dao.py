from datetime import date, datetime
from typing import Dict

from loguru import logger
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.dao.base import BaseDAO
from app.dao.models import Booking, MeetingRoom, TimeSlot, User


class UserDAO(BaseDAO[User]):
    model = User


class TimeSlotUserDAO(BaseDAO[TimeSlot]):
    model = TimeSlot


class MeetingRoomDAO(BaseDAO[MeetingRoom]):
    model = MeetingRoom

    async def find_all_by_capacity(self, capacity: int):

        logger.info(
            f'Поиск всех записей {self.model.__name__} '
            f'для количества участников: {capacity}'
            )
        try:
            query = select(self.model).filter(
                self.model.capacity >= capacity.capacity
            )
            result = await self._session.execute(query)
            records = result.scalars().all()
            logger.info(f'Найдено {len(records)} записей.')

            return records

        except SQLAlchemyError as e:
            logger.error(
                f'Ошибка при поиске всех записей для количества участников '
                f'{capacity}: {e}'
                )
            raise


class BookingDAO(BaseDAO[Booking]):
    model = Booking

    async def check_available_bookings(
            self,
            meeting_room_id: int,
            booking_date: date,
            time_slot_id: int
            ):
        """
        Проверяет наличие существующих броней для
        переговорной на указанную дату и временной слот.
        """
        try:
            query = select(self.model).filter_by(
                meeting_room_id=meeting_room_id,
                date=booking_date,
                time_slot_id=time_slot_id
            )
            result = await self._session.execute(query)

            # Если результатов нет, переговорная свободна.
            if not result.scalars().all():
                return True

            # Проверяем статус существующих бронирований.
            for booking in result.scalars().all():
                if booking.status == 'booked':
                    return False  # Переговорная занята.

                # Для других статусов считаем переговорную свободной.
                continue
            # Если все брони имеют неактивные статусы
            return True

        except SQLAlchemyError as e:
            logger.error(f'Ошибка при проверке доступности брони: {e}')

    async def get_available_time_slots(
            self,
            meeting_room_id: int,
            booking_date: date
            ):
        """
        Получает список доступных временных слотов
        для переговорной на указанную дату.
        """
        try:
            # Получаем все брони для переговорной и даты
            bookings_query = select(self.model).filter_by(
                meeting_room_id=meeting_room_id,
                date=booking_date
            )
            bookings_result = await self._session.execute(bookings_query)
            # Составляем набор занятых слотов (только с активными бронями)
            booked_slots = {
                booking.time_slot_id
                for booking in bookings_result.scalars().all()
                if booking.status == 'booked'
                }
            # Получаем все доступные слоты, исключая занятые
            available_slots_query = select(TimeSlot).filter(
                ~TimeSlot.id.in_(booked_slots)
            )
            available_slots_result = await self._session.execute(
                available_slots_query
                )
            return available_slots_result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(
                f'Ошибка при получении доступных временных слотов: {e}'
                )

    async def get_bookings_with_details(self, user_id: int):
        """
        Получает список всех бронирований сотрудника
        с полной информацией о переговорной и временном слоте.

        :param user_id: ID сотрудника, брони которого нужно получить.
        :return: Список объектов Booking с загруженными данными
        о переговорной и времени.
        """
        try:
            query = select(self.model).options(
                joinedload(self.model.meeting_room),
                joinedload(self.model.time_slot)
            ).filter_by(user_id=user_id)
            result = await self._session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при получении бронирований с деталями: {e}')
            return []

    async def complete_past_bookings(self):
        """
        Обновляет статус бронирований на 'completed',
        если дата и время бронирования уже прошли.
        """
        try:
            # Получаем текущее время
            now = datetime.now()
            subquery = select(TimeSlot.start_time).where(
                TimeSlot.id == self.model.time_slot_id
                ).scalar_subquery()
            query = select(Booking.id).where(
                Booking.date < now.date(),
                self.model.status == 'booked'
            ).union_all(
                select(Booking.id).where(
                    self.model.date == now.date(),
                    subquery < now.time(),
                    self.model.status == 'booked'
                )
            )

            # Выполняем запрос и получаем id бронирований,
            # которые нужно обновить
            result = await self._session.execute(query)
            booking_ids_to_update = result.scalars().all()

            if booking_ids_to_update:
                # Формируем запрос на обновление статуса бронирований
                update_query = update(Booking).where(
                    Booking.id.in_(booking_ids_to_update)
                ).values(status='completed')

                # Выполняем запрос на обновление
                await self._session.execute(update_query)

                # Подтверждаем изменения
                await self._session.commit()

                logger.info(
                    f'Обновлен статус для {len(booking_ids_to_update)} '
                    f'бронирований на "completed"'
                    )
            else:
                logger.info('Нет бронирований для обновления статуса.')

        except SQLAlchemyError as e:
            logger.error(f'Ошибка при обновлении статуса бронирований: {e}')
            await self._session.rollback()

    async def cancel_booking(self, booking_id: int):
        try:
            query = (
                update(self.model)
                .filter_by(id=booking_id)
                .values(status='canceled')
                .execution_options(synchronize_session='fetch')
            )
            result = await self._session.execute(query)
            await self._session.flush()
            return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при отмене брони с ID {booking_id}: {e}')
            await self._session.rollback()
            raise

    async def delete_booking(self, booking_id: int):
        try:
            query = delete(self.model).filter_by(id=booking_id)
            result = await self._session.execute(query)
            logger.info(f'Удалено {result.rowcount} записей.')
            await self._session.flush()
            return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при удалении записей: {e}')
            raise

    async def booking_count(self) -> Dict[str, int]:
        """
        Подсчитывает количество заявок по каждому
        статусу (booked, completed, canceled).
        """
        try:
            status_counts = {}
            statuses = ['booked', 'completed', 'canceled']

            for status in statuses:
                query = select(func.count(self.model.id)).where(
                    self.model.status == status
                    )
                result = await self._session.execute(query)
                count = result.scalar()
                status_counts[status] = count
                logger.info(f'Найдено {count} заявок со статусом "{status}".')

            total_query = select(func.count(self.model.id))
            total_result = await self._session.execute(total_query)
            total_count = total_result.scalar()
            status_counts['total'] = total_count
            logger.info(f'Всего найдено {total_count} заявок.')

            return status_counts
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при подсчете заявок по статусам: {e}')
            raise
