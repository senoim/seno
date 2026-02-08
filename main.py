import asyncio
import logging
import sys
import os

# إضافة المسار الحالي للمشروع لتمكين الاستيرادات
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMIN_ID
from database.db import db
from handlers import start, admin, spotify
from middlewares.subscription import SubscriptionMiddleware

# إعداد السجلات (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

async def on_startup(bot: Bot):
    # تهيئة قاعدة البيانات
    await db.init()
    logging.info("Database initialized.")
    
    # إشعار المطور بتشغيل البوت
    if ADMIN_ID != 0:
        try:
            await bot.send_message(ADMIN_ID, "🚀 تم تشغيل البوت بنجاح!")
        except Exception as e:
            logging.warning(f"Could not send startup message to admin: {e}")

async def main():
    # التأكد من وجود التوكن
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logging.error("Please set your BOT_TOKEN in config.py")
        return

    # إنشاء كائن البوت
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # إنشاء الموزع (Dispatcher)
    dp = Dispatcher()

    # تسجيل الميدل وير (التحقق من الاشتراك والبيانات)
    dp.message.middleware(SubscriptionMiddleware())

    # تسجيل الراوترات (Handlers)
    # ملاحظة: ترتيب الراوترات مهم، نضع الأدمن أولاً
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(spotify.router)

    # تنفيذ مهام عند التشغيل
    await on_startup(bot)
    
    # بدء استقبال التحديثات (Polling)
    logging.info("Starting bot polling...")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
