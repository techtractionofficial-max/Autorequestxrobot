import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import config
from database import db
from handlers import user, requests, admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def main():
    # Initialize SQLite database tables
    await db.init_db()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register modular routers
    dp.include_router(admin.router)
    dp.include_router(requests.router)
    dp.include_router(user.router)

    logging.info("Bot engine initialized. Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "chat_join_request", "callback_query"])
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
  
