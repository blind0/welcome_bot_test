import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apschedule.update_usd_price import update_usd_price

from db import db_manager

from config import Config, parse_config
from arguments import parse_arguments

from routers.hello import router


async def on_startup(
    dispatcher: Dispatcher, bot: Bot, config: Config,
):
    #upd usd_rate
    await update_usd_price(config)

    dispatcher.include_router(router)

    if config.settings.use_webhook:
        webhook_url = (
            config.webhook.url + config.webhook.path
            if config.webhook.url
            else f"http://localhost:{config.webhook.port}{config.webhook.path}"
        )
        await bot.set_webhook(
            webhook_url,
            drop_pending_updates=config.settings.drop_pending_updates,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    else:
        await bot.delete_webhook(
            drop_pending_updates=config.settings.drop_pending_updates,
        )

    bot_info = await bot.get_me()

    logging.info(f"Name - {bot_info.full_name}")
    logging.info(f"Username - @{bot_info.username}")
    logging.info(f"ID - {bot_info.id}")

    states = {
        True: "Enabled",
        False: "Disabled",
    }

    logging.debug(f"Groups Mode - {states[bot_info.can_join_groups]}")
    logging.debug(f"Privacy Mode - {states[not bot_info.can_read_all_group_messages]}")
    logging.debug(f"Inline Mode - {states[bot_info.supports_inline_queries]}")

    logging.warning("Bot started!")


async def on_shutdown(dispatcher: Dispatcher, bot: Bot, config: Config):
    logging.warning("Stopping bot...")
    await bot.delete_webhook(drop_pending_updates=config.settings.drop_pending_updates)
    await dispatcher.fsm.storage.close()
    await bot.session.close()




async def main():

    logging.warning("Starting bot...")
    arguments = parse_arguments()
    config = parse_config(arguments.config)


    session = AiohttpSession(api=TelegramAPIServer.from_base(config.api.bot_api_url, is_local=config.api.is_local))
    token = config.bot.token
    bot_settings = {"session": session}

    bot = Bot(token,default=DefaultBotProperties(parse_mode=ParseMode.HTML), **bot_settings)

    if config.storage.use_persistent_storage:
        pass
    else:
        storage = MemoryStorage()

    await db_manager.init("dbp.db")
    await db_manager.create_schema()

    dp = Dispatcher(storage=storage)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(update_usd_price, trigger="interval",  hours=1, kwargs={"config": config})
    scheduler.start()

    context_kwargs = {"config": config, }

    if config.settings.use_webhook:
        logging.getLogger("aiohttp.access").setLevel(logging.DEBUG)

        web_app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot, **context_kwargs).register(
            web_app, path=config.webhook.path
        )

        setup_application(web_app, dp, bot=bot, **context_kwargs)

        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, port=config.webhook.port)
        await site.start()

        await asyncio.Event().wait()
    else:
        await dp.start_polling(bot, **context_kwargs)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
