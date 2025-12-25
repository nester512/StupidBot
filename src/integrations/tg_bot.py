from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.on_startup.dispatcher import setup_dispatcher

from conf.config import settings

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = setup_dispatcher(bot)


def get_dispatcher() -> Dispatcher:
    global dp

    return dp


def get_tg_bot() -> Bot:
    global bot

    return bot
