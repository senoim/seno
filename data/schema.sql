-- مخطط قاعدة البيانات لبوت سبوتيفاي

-- جدول المستخدمين لتخزين معلومات المشتركين
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,          --معرف المستخدم في تلغرام
    username TEXT,                        --اسم مستخدم تلغرام (قد يكون فارغاً)
    full_name TEXT NOT NULL,              --الاسم الكامل للمستخدم
    is_admin INTEGER DEFAULT 0,           --علامة لتحديد ما إذا كان المستخدم مطوراً (0 = لا، 1 = نعم)
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, --تاريخ ووقت انضمام المستخدم
    is_blocked INTEGER DEFAULT 0            --علامة لتحديد ما إذا حظر المستخدم البوت (0 = لا، 1 = نعم)
);

-- جدول الإعدادات لتخزين إعدادات البوت القابلة للتغيير
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,                   --مفتاح الإعداد (مثل: رسالة البدء)
    value TEXT                              --قيمة الإعداد
);

-- إدخال القيم الافتراضية للإعدادات عند إنشاء قاعدة البيانات لأول مرة
-- سيتم تجاهل هذا الأمر إذا كانت المفاتيح موجودة بالفعل
INSERT OR IGNORE INTO settings (key, value) VALUES ('start_message', 'أهلاً بك في بوت تحميل Spotify! أرسل رابط الأغنية أو الألبوم أو قائمة التشغيل للبدء.');
INSERT OR IGNORE INTO settings (key, value) VALUES ('force_channel', '@YourChannelLink'); -- يجب استبداله بالرابط الفعلي للقناة
INSERT OR IGNORE INTO settings (key, value) VALUES ('notify_new_user', '1'); -- تفعيل إشعارات دخول الأعضاء الجدد (1 = مفعل, 0 = معطل)
INSERT OR IGNORE INTO settings (key, value) VALUES ('notify_block', '1'); -- تفعيل إشعارات حظر البوت (1 = مفعل, 0 = معطل)
INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_id', 'YOUR_TELEGRAM_ID'); -- يجب استبداله بمعرف المطور العددي

