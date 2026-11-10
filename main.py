import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.config import BOT_TOKEN
from app.database import init_db
from app.handlers import router
from app.scheduler import start_result_scheduler
from app.certificate import create_default_template

# Log sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ":
        logger.error(
            "XATOLIK: .env faylida BOT_TOKEN ko'rsatilmagan! "
            "Iltimos, .env faylini oching va @BotFather bergan tokenni kiriting."
        )
        sys.exit(1)

    # 1. Ma'lumotlar bazasini initsializatsiya qilish
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    # 2. Standart sertifikat shablonini tekshirish/yaratish
    create_default_template()
    logger.info("Sertifikat shabloni tekshirildi.")

    # 3. Bot va Dispatcher yaratish
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    # 4. 15 daqiqalik kechiktirilgan natijalarni tekshiruvchi fon taskini ishga tushirish
    asyncio.create_task(start_result_scheduler(bot))
    logger.info("Natijalarni yetkazish bo'yicha scheduler fonda ishga tushirildi.")

    logger.info("MDev Sertifikat Boti muvaffaqiyatli ishga tushdi! /start")
    
    # Eskirgan webhook va pending yangilanishlarni tozalash
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
