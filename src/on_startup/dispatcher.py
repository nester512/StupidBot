# src/on_startup/dispatcher.py
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.handlers.private.router import private_router
from src.handlers.private import main as private_main  # noqa: F401 - импортируем для регистрации handlers
from src.middleware.logger import LogMessageMiddleware


def setup_dispatcher(bot: Bot) -> Dispatcher:
    storage = MemoryStorage()
    # TODO //storage = RedisStorage(redis)
    dp = Dispatcher(storage=storage, bot=bot)

    dp.include_routers(private_router)

    dp.message.middleware(LogMessageMiddleware())
    dp.callback_query.middleware(LogMessageMiddleware())
    dp.edited_message.middleware(LogMessageMiddleware())
    dp.my_chat_member.middleware(LogMessageMiddleware())

    return dp
