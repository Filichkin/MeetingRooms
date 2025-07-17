from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram_dialog import setup_dialogs
import locale
from loguru import logger

from app.bot.booking.dialog import booking_dialog
from app.bot.user.router import router as user_router
from app.bot.admin.router import router as admin_router
from app.config import settings
from app.dao.database_middleware import (
    DatabaseMiddlewareWithoutCommit,
    DatabaseMiddlewareWithCommit
)
from app.dao.init_logic import init_db


bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
dp = Dispatcher(storage=MemoryStorage())


async def set_commands():
    commands = [BotCommand(command='start', description='Старт')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


def set_russian_locale():
    try:
        # Пробуем установить локаль для Windows
        locale.setlocale(locale.LC_TIME, 'Russian_Russia.1251')
    except locale.Error:
        try:
            # Пробуем установить локаль для Linux/macOS
            locale.setlocale(locale.LC_TIME, 'ru_RU.utf8')
        except locale.Error:
            # Игнорируем ошибку, если локаль не поддерживается
            pass


async def start_bot():
    set_russian_locale()
    if settings.INIT_DB:
        await init_db()
    setup_dialogs(dp)
    dp.update.middleware.register(DatabaseMiddlewareWithoutCommit())
    dp.update.middleware.register(DatabaseMiddlewareWithCommit())
    await set_commands()
    dp.include_router(booking_dialog)
    dp.include_router(user_router)
    dp.include_router(admin_router)

    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, 'Бот запущен!')
        except TelegramAPIError as error:
            logger.error(
                f'Ошибка при запуске бота: {error}'
                )
    logger.info('Бот успешно запущен.')


async def stop_bot():
    try:
        for admin_id in settings.ADMIN_IDS:
            await bot.send_message(admin_id, 'Бот остановлен!')
    except TelegramAPIError as error:
        logger.error(
            f'Ошибка при остановке бота: {error}'
            )
    logger.error('Бот остановлен!')
