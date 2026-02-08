import os

# توكن البوت من @BotFather - يتم جلبه من متغيرات بيئة Railway
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# معرف المطور (Admin) - يتم جلبه من متغيرات بيئة Railway
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# مسار قاعدة البيانات - في Railway يفضل استخدام مسار ثابت أو حجم خارجي إذا توفر
# ولكن للتبسيط سنستخدم المجلد المحلي
DB_PATH = os.getenv("DB_PATH", "data/bot_database.db")

# مسار ملف الـ SQL
SCHEMA_PATH = "data/schema.sql"
