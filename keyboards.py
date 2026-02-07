from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

class Keyboards:
    @staticmethod
    def admin_panel():
        """لوحة تحكم المطور"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="✏️ تعديل رسالة الترحيب", callback_data="admin_welcome")],
            [InlineKeyboardButton(text="🔔 إعدادات الإشعارات", callback_data="admin_notifications")],
            [InlineKeyboardButton(text="🔗 تغيير رابط القناة", callback_data="admin_channel")],
            [InlineKeyboardButton(text="📢 إرسال إذاعة", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        return keyboard
    
    @staticmethod
    def notification_settings(join_status: bool, block_status: bool):
        """إعدادات الإشعارات"""
        join_text = "✅ تفعيل" if not join_status else "❌ تعطيل"
        block_text = "✅ تفعيل" if not block_status else "❌ تعطيل"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"إشعارات الدخول: {'مفعّل ✅' if join_status else 'معطّل ❌'}",
                callback_data="toggle_join_notif"
            )],
            [InlineKeyboardButton(
                text=f"إشعارات الحظر: {'مفعّل ✅' if block_status else 'معطّل ❌'}",
                callback_data="toggle_block_notif"
            )],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin_back")]
        ])
        return keyboard
    
    @staticmethod
    def back_to_admin():
        """زر الرجوع للوحة التحكم"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin_back")]
        ])
        return keyboard
    
    @staticmethod
    def cancel_operation():
        """زر إلغاء العملية"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="admin_back")]
        ])
        return keyboard
    
    @staticmethod
    def check_subscription(channel_username: str):
        """زر التحقق من الاشتراك"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 الاشتراك في القناة", url=f"https://t.me/{channel_username.replace('@', '')}")],
            [InlineKeyboardButton(text="✅ تحققت من الاشتراك", callback_data="check_sub")]
        ])
        return keyboard
    
    @staticmethod
    def broadcast_confirm():
        """تأكيد الإذاعة"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ إرسال", callback_data="broadcast_send"),
                InlineKeyboardButton(text="❌ إلغاء", callback_data="admin_back")
            ]
        ])
        return keyboard
