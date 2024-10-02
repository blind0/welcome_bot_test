import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import Config, parse_config

from testHandler import router


async def on_startup(
    dispatcher: Dispatcher, bot: Bot, config: Config,
):
    
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

    async def external_signal(request):
        message_text = "батя заколлил"
        chat_id = config.settings.chat_id
        if chat_id and message_text:
            await bot.send_message(chat_id, message_text)
            return web.json_response({'status': 'ok', 'message': 'Message sent'})
        return web.json_response({'status': 'error', 'message': 'Invalid request'}, status=400)


    logging.warning("Starting bot...")

    config = parse_config(arguments.config)


    session = AiohttpSession(api=TelegramAPIServer.from_base(config.api.bot_api_url, is_local=config.api.is_local))
    token = config.bot.token
    bot_settings = {"session": session}

    bot = Bot(token,default=DefaultBotProperties(parse_mode=ParseMode.HTML), **bot_settings)

    if config.storage.use_persistent_storage:
        storage = RedisStorage(
            redis=RedisStorage.from_url(config.storage.redis_url),
            key_builder=DefaultKeyBuilder(with_destiny=True),
        )
    else:
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    #registry = DialogRegistry(dp)

    context_kwargs = {"config": config, }

    if config.settings.use_webhook:
        logging.getLogger("aiohttp.access").setLevel(logging.CRITICAL)

        web_app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot, **context_kwargs).register(
            web_app, path=config.webhook.path
        )

        web_app.router.add_get("/call", external_signal)

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
