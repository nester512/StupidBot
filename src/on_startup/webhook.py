import logging

from aiogram import Bot

from conf.config import settings


async def setup_webhook(bot: Bot) -> None:
    logging.info("Setup webhook")
    print("Setup webhook")

    if not settings.WEBHOOK_URL:
        logging.warning("WEBHOOK_URL is not set, skipping webhook setup")
        print("WEBHOOK_URL is not set, skipping webhook setup")
        return

    webhook = await bot.get_webhook_info()
    if webhook.url != settings.WEBHOOK_URL:
        print("Delete webhook")
        await bot.delete_webhook()

    logging.info("Set webhook")
    print("Set webhook")
    await bot.set_webhook(settings.WEBHOOK_URL)

    logging.info("Finish setup")
    print("Finish setup")
