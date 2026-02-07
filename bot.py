import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os

from database import Database
from handlers import router

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# الحصول على المتغيرات
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot_database.db')

async def on_startup(bot: Bot):
    """عند بدء تشغيل البوت"""
    logger.info("🚀 البوت يعمل الآن...")
    
    # إنشاء قاعدة البيانات
    db = Database(DATABASE_PATH)
    await db.init_db()
    logger.info("✅ تم تهيئة قاعدة البيانات")
    
    # إرسال رسالة للمطور
    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                "✅ <b>البوت يعمل الآن!</b>\n\n"
                "يمكنك استخدام /admin للوصول إلى لوحة التحكم"
            )
        except Exception as e:
            logger.error(f"خطأ في إرسال رسالة البداية: {e}")

async def on_shutdown(bot: Bot):
    """عند إيقاف البوت"""
    logger.info("⏹ جارٍ إيقاف البوت...")
    
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, "⏹ تم إيقاف البوت")
        except:
            pass

async def main():
    """الدالة الرئيسية"""
    
    # التحقق من وجود التوكن
    if not BOT_TOKEN:
        logger.error("❌ خطأ: لم يتم العثور على BOT_TOKEN في ملف .env")
        return
    
    # إنشاء البوت والموزع
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # تسجيل الموجهات
    dp.include_router(router)
    
    # تسجيل أحداث البداية والنهاية
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # معالج الأخطاء العام
    @dp.error()
    async def error_handler(event, data):
        logger.error(f"خطأ: {event.exception}")
        return True
    
    # معالج my_chat_member للكشف عن حظر البوت
    @dp.my_chat_member()
    async def my_chat_member_handler(event):
        db = Database(DATABASE_PATH)
        
        # إذا تم حظر البوت
        if event.new_chat_member.status == "kicked":
            user = event.from_user
            await db.block_user(user.id)
            
            # إرسال إشعار للمطور
            block_notif = await db.get_setting('block_notifications')
            if block_notif == '1' and ADMIN_ID:
                notification_text = (
                    "🚫 <b>عضو قام بحظر البوت!</b>\n\n"
                    f"👤 الاسم: {user.first_name} {user.last_name or ''}\n"
                    f"🆔 المعرف: @{user.username or 'لا يوجد'}\n"
                    f"🔢 الآيدي: <code>{user.id}</code>"
                )
                try:
                    await bot.send_message(ADMIN_ID, notification_text)
                except Exception as e:
                    logger.error(f"خطأ في إرسال إشعار الحظر: {e}")
    
    try:
        # بدء البوت
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("تم إيقاف البوت يدوياً")
    except Exception as e:
        logger.error(f"خطأ فادح: {e}")
