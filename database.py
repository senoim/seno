import aiosqlite
import os
from datetime import datetime

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def init_db(self):
        """إنشاء جداول قاعدة البيانات"""
        async with aiosqlite.connect(self.db_path) as db:
            # جدول المستخدمين
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_date TEXT,
                    is_blocked INTEGER DEFAULT 0,
                    last_active TEXT
                )
            """)
            
            # جدول الإعدادات
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # جدول الإحصائيات
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_type TEXT,
                    count INTEGER DEFAULT 0,
                    date TEXT
                )
            """)
            
            await db.commit()
            
            # إضافة الإعدادات الافتراضية
            await self.init_default_settings()
    
    async def init_default_settings(self):
        """إضافة الإعدادات الافتراضية"""
        default_settings = {
            'welcome_message': '👋 مرحباً بك في بوت تحميل الموسيقى من Spotify!\n\nأرسل لي رابط أغنية وسأقوم بتحميلها لك 🎵',
            'join_notifications': '1',
            'block_notifications': '1',
            'channel_username': os.getenv('CHANNEL_USERNAME', '@your_channel')
        }
        
        async with aiosqlite.connect(self.db_path) as db:
            for key, value in default_settings.items():
                await db.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (key, value)
                )
            await db.commit()
    
    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str = None):
        """إضافة مستخدم جديد"""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, joined_date, last_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, now, now))
            await db.commit()
    
    async def update_user_activity(self, user_id: int):
        """تحديث آخر نشاط للمستخدم"""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                "UPDATE users SET last_active = ? WHERE user_id = ?",
                (now, user_id)
            )
            await db.commit()
    
    async def block_user(self, user_id: int):
        """تحديد مستخدم كمحظور للبوت"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_blocked = 1 WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
    
    async def get_user(self, user_id: int):
        """الحصول على معلومات مستخدم"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                return await cursor.fetchone()
    
    async def get_all_users(self):
        """الحصول على جميع المستخدمين"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users") as cursor:
                return await cursor.fetchall()
    
    async def get_active_users(self):
        """الحصول على المستخدمين النشطين (غير المحظورين)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE is_blocked = 0"
            ) as cursor:
                return await cursor.fetchall()
    
    async def get_stats(self):
        """الحصول على الإحصائيات"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total_users = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE is_blocked = 0"
            ) as cursor:
                active_users = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE is_blocked = 1"
            ) as cursor:
                blocked_users = (await cursor.fetchone())[0]
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'blocked_users': blocked_users
            }
    
    async def get_setting(self, key: str):
        """الحصول على إعداد معين"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def update_setting(self, key: str, value: str):
        """تحديث إعداد"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            await db.commit()
