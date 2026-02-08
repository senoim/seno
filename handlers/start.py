from aiogram import Router, types, F
from aiogram.filters import CommandStart
from database.db import db
from config import ADMIN_ID

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    # الحصول على رسالة الترحيب من قاعدة البيانات
    start_msg = await db.get_setting('start_message')
    
    # إرسال إشعار للمطور إذا كان الخيار مفعلاً
    notify_new = await db.get_setting('notify_new_user')
    if notify_new == '1' and message.from_user.id != ADMIN_ID:
        try:
            admin_notify = (
                f"👤 عضو جديد دخل للبوت:\n\n"
                f"الاسم: {message.from_user.full_name}\n"
                f"المعرف: @{message.from_user.username or 'لا يوجد'}\n"
                f"الآيدي: `{message.from_user.id}`"
            )
            await message.bot.send_message(ADMIN_ID, admin_notify, parse_mode="Markdown")
        except Exception:
            pass

    await message.answer(start_msg)

@router.callback_query(F.data == "check_subscription")
async def check_sub(callback: types.CallbackQuery):
    # سيقوم الميدل وير بالتحقق تلقائياً عند الضغط، وإذا نجح سيمر الطلب هنا
    await callback.answer("شكراً لاشتراكك! يمكنك الآن استخدام البوت.", show_alert=True)
    start_msg = await db.get_setting('start_message')
    await callback.message.edit_text(start_msg)
