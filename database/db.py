import sqlite3
import aiosqlite
import os
import sys

# إضافة المسار الرئيسي للمشروع لتمكين الاستيراد من config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, SCHEMA_PATH

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    async def init(self):
        # التأكد من وجود المجلد
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                schema = f.read()
            await db.executescript(schema)
            await db.commit()

    async def add_user(self, user_id, username, full_name):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
                (user_id, username, full_name)
            )
            # تحديث حالة الحظر إذا كان المستخدم قد عاد لاستخدام البوت
            await db.execute("UPDATE users SET is_blocked = 0 WHERE user_id = ?", (user_id,))
            await db.commit()

    async def set_user_blocked(self, user_id, status=1):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET is_blocked = ? WHERE user_id = ?", (status, user_id))
            await db.commit()

    async def get_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total = (await cursor.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 0") as cursor:
                active = (await cursor.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1") as cursor:
                blocked = (await cursor.fetchone())[0]
            return total, active, blocked

    async def get_setting(self, key):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def update_setting(self, key, value):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
            await db.commit()

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users WHERE is_blocked = 0") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

# إنشاء كائن قاعدة البيانات للاستخدام في البوت
db = Database()
