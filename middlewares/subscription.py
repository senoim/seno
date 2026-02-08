from aiogram import BaseMiddleware
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from config import ADMIN_ID

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        # تحديث أو إضافة المستخدم لقاعدة البيانات
        await db.add_user(user.id, user.username, user.full_name)

        # استثناء المطور من التحقق
        if user.id == ADMIN_ID:
            return await handler(event, data)

        # الحصول على رابط القناة من الإعدادات
        channel_link = await db.get_setting('force_channel')
        
        # إذا لم يتم تعيين قناة، استمر
        if not channel_link or channel_link == "@YourChannelLink":
            return await handler(event, data)

        try:
            # التحقق من عضوية المستخدم في القناة
            # ملاحظة: يجب أن يكون البوت مشرفاً في القناة ليتمكن من التحقق
            channel_id = channel_link if channel_link.startswith('-100') else f"@{channel_link.replace('@', '')}"
            member = await event.bot.get_chat_member(chat_id=channel_id, user_id=user.id)
            
            if member.status in ['member', 'administrator', 'creator']:
                return await handler(event, data)
            else:
                raise Exception("Not Subscribed")
        except Exception:
            # إذا لم يكن مشتركاً، أرسل رسالة تطلب الاشتراك
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="انضم للقناة أولاً", url=f"https://t.me/{channel_link.replace('@', '')}")],
                [InlineKeyboardButton(text="تم الاشتراك ✅", callback_data="check_subscription")]
            ])
            await event.answer(
                "عذراً! يجب عليك الاشتراك في قناة المطور لاستخدام البوت.\n\nاشترك ثم اضغط على زر التحقق.",
                reply_markup=keyboard
            )
            return
