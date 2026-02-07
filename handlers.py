from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from keyboards import Keyboards
import os

# حالات FSM
class AdminStates(StatesGroup):
    waiting_for_welcome = State()
    waiting_for_channel = State()
    waiting_for_broadcast = State()

class DownloadStates(StatesGroup):
    waiting_for_link = State()

router = Router()
db = Database(os.getenv('DATABASE_PATH', 'bot_database.db'))
kb = Keyboards()
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

# دالة للتحقق من الاشتراك
async def check_subscription(user_id: int, bot) -> bool:
    """التحقق من اشتراك المستخدم في القناة"""
    channel_username = await db.get_setting('channel_username')
    if not channel_username or channel_username == '@your_channel':
        return True  # إذا لم يتم تحديد قناة، نسمح بالمرور
    
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except:
        return False

# معالج أمر /start
@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user = message.from_user
    
    # إضافة المستخدم للقاعدة
    existing_user = await db.get_user(user.id)
    if not existing_user:
        await db.add_user(
            user_id=user.id,
            username=user.username or "بدون معرف",
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # إرسال إشعار للمطور عن عضو جديد
        join_notif = await db.get_setting('join_notifications')
        if join_notif == '1' and ADMIN_ID:
            notification_text = (
                "🆕 <b>عضو جديد انضم للبوت!</b>\n\n"
                f"👤 الاسم: {user.first_name} {user.last_name or ''}\n"
                f"🆔 المعرف: @{user.username or 'لا يوجد'}\n"
                f"🔢 الآيدي: <code>{user.id}</code>\n"
                f"📅 التاريخ: {existing_user['joined_date'] if existing_user else 'الآن'}"
            )
            try:
                await message.bot.send_message(ADMIN_ID, notification_text)
            except:
                pass
    else:
        await db.update_user_activity(user.id)
    
    # التحقق من الاشتراك
    is_subscribed = await check_subscription(user.id, message.bot)
    if not is_subscribed:
        channel_username = await db.get_setting('channel_username')
        await message.answer(
            f"⚠️ <b>عذراً، يجب عليك الاشتراك في القناة أولاً لاستخدام البوت!</b>\n\n"
            f"📢 القناة: {channel_username}\n\n"
            f"بعد الاشتراك، اضغط على زر التحقق 👇",
            reply_markup=kb.check_subscription(channel_username)
        )
        return
    
    # رسالة الترحيب
    welcome_msg = await db.get_setting('welcome_message')
    await message.answer(welcome_msg or "مرحباً بك! 👋")
    await state.clear()

# معالج التحقق من الاشتراك
@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    is_subscribed = await check_subscription(callback.from_user.id, callback.bot)
    
    if is_subscribed:
        welcome_msg = await db.get_setting('welcome_message')
        await callback.message.delete()
        await callback.message.answer(welcome_msg or "مرحباً بك! 👋")
    else:
        await callback.answer("❌ لم تقم بالاشتراك في القناة بعد!", show_alert=True)

# معالج أمر /admin
@router.message(Command("admin"))
async def admin_panel_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ ليس لديك صلاحية الوصول لهذا القسم!")
        return
    
    await message.answer(
        "🎛 <b>لوحة تحكم المطور</b>\n\n"
        "اختر الإجراء المطلوب من القائمة أدناه:",
        reply_markup=kb.admin_panel()
    )

# معالج الإحصائيات
@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ ليس لديك صلاحية!", show_alert=True)
        return
    
    stats = await db.get_stats()
    stats_text = (
        "📊 <b>إحصائيات البوت</b>\n\n"
        f"👥 إجمالي الأعضاء: <code>{stats['total_users']}</code>\n"
        f"✅ الأعضاء النشطين: <code>{stats['active_users']}</code>\n"
        f"🚫 المحظورين: <code>{stats['blocked_users']}</code>"
    )
    
    await callback.message.edit_text(stats_text, reply_markup=kb.back_to_admin())

# معالج تعديل رسالة الترحيب
@router.callback_query(F.data == "admin_welcome")
async def admin_welcome_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ ليس لديك صلاحية!", show_alert=True)
        return
    
    current_welcome = await db.get_setting('welcome_message')
    await callback.message.edit_text(
        f"✏️ <b>تعديل رسالة الترحيب</b>\n\n"
        f"الرسالة الحالية:\n{current_welcome}\n\n"
        f"أرسل الرسالة الجديدة الآن:",
        reply_markup=kb.cancel_operation()
    )
    await state.set_state(AdminStates.waiting_for_welcome)

@router.message(AdminStates.waiting_for_welcome)
async def process_welcome_message(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await db.update_setting('welcome_message', message.text)
    await message.answer(
        "✅ تم تحديث رسالة الترحيب بنجاح!",
        reply_markup=kb.back_to_admin()
    )
    await state.clear()

# معالج إعدادات الإشعارات
@router.callback_query(F.data == "admin_notifications")
async def admin_notifications_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ ليس لديك صلاحية!", show_alert=True)
        return
    
    join_status = await db.get_setting('join_notifications') == '1'
    block_status = await db.get_setting('block_notifications') == '1'
    
    await callback.message.edit_text(
        "🔔 <b>إعدادات الإشعارات</b>\n\n"
        "قم بتفعيل أو تعطيل الإشعارات حسب رغبتك:",
        reply_markup=kb.notification_settings(join_status, block_status)
    )

@router.callback_query(F.data == "toggle_join_notif")
async def toggle_join_notif_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ ليس لديك صلاحية!", show_alert=True)
        return
    
    current = await db.get_setting('join_notifications')
    new_value = '0' if current == '1' else '1'
    await db.update_setting('join_notifications', new_value)
    
    join_status = new_value == '1'
    block_status = await db.get_setting('block_notifications') == '1'
    
    await callback.message.edit_reply_markup(
        reply_markup=kb.notification_settings(join_status, block_status)
    )
    await callback.answer("✅ تم التحديث!")

@router.callback_query(F.data == "toggle_block_notif")
async def toggle_block_notif_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ ليس لديك صلاحية!", show_alert=True)
        return
    
    current = await db.get_setting('block_notifications')
    new_value = '0' if current == '1' else '1'
    await db.update_setting('block_notifications', new_value)
    
    join_status = await db.get_setting('join_notifications') == '1'
    block_status = new_value == '1'
    
    await callback.message.edit_reply_markup(
        reply_markup=kb.notification_settings(join_status, block_status)
    )
    await callback.answer("✅ تم التحديث!")

# معالج تغيير رابط القناة
@router.callback_query(F.data == "admin_channel")
async def admin_channel_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ ليس لديك صلاحية!", show_alert=True)
        return
    
    current_channel = await db.get_setting('channel_username')
    await callback.message.edit_text(
        f"🔗 <b>تغيير رابط القناة</b>\n\n"
        f"القناة الحالية: {current_channel}\n\n"
        f"أرسل معرف القناة الجديد (مثال: @channel_name):",
        reply_markup=kb.cancel_operation()
    )
    await state.set_state(AdminStates.waiting_for_channel)

@router.message(AdminStates.waiting_for_channel)
async def process_channel_update(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    channel = message.text.strip()
    if not channel.startswith('@'):
        await message.answer("❌ يجب أن يبدأ معرف القناة بـ @")
        return
    
    await db.update_setting('channel_username', channel)
    await message.answer(
        f"✅ تم تحديث رابط القناة إلى: {channel}",
        reply_markup=kb.back_to_admin()
    )
    await state.clear()

# معالج الإذاعة
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ ليس لديك صلاحية!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 <b>إرسال إذاعة</b>\n\n"
        "أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:",
        reply_markup=kb.cancel_operation()
    )
    await state.set_state(AdminStates.waiting_for_broadcast)

@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast_message(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # حفظ الرسالة للمعاينة
    await state.update_data(broadcast_message=message.text)
    
    await message.answer(
        f"📝 <b>معاينة الإذاعة:</b>\n\n{message.text}\n\n"
        "هل تريد إرسال هذه الرسالة لجميع المستخدمين؟",
        reply_markup=kb.broadcast_confirm()
    )

@router.callback_query(F.data == "broadcast_send")
async def send_broadcast(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ ليس لديك صلاحية!", show_alert=True)
        return
    
    data = await state.get_data()
    broadcast_msg = data.get('broadcast_message')
    
    if not broadcast_msg:
        await callback.answer("❌ خطأ في الرسالة!", show_alert=True)
        return
    
    users = await db.get_active_users()
    success_count = 0
    fail_count = 0
    
    await callback.message.edit_text("⏳ جارٍ إرسال الإذاعة...")
    
    for user in users:
        try:
            await callback.bot.send_message(user['user_id'], broadcast_msg)
            success_count += 1
        except:
            fail_count += 1
            # تحديث حالة المستخدم كمحظور
            await db.block_user(user['user_id'])
    
    await callback.message.edit_text(
        f"✅ <b>تم إرسال الإذاعة!</b>\n\n"
        f"📊 تم الإرسال: {success_count}\n"
        f"❌ فشل الإرسال: {fail_count}",
        reply_markup=kb.back_to_admin()
    )
    await state.clear()

# معالج الرجوع للوحة التحكم
@router.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎛 <b>لوحة تحكم المطور</b>\n\n"
        "اختر الإجراء المطلوب من القائمة أدناه:",
        reply_markup=kb.admin_panel()
    )

# معالج إغلاق اللوحة
@router.callback_query(F.data == "admin_close")
async def admin_close_callback(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("تم الإغلاق ✅")

# معالج روابط Spotify
@router.message(F.text.contains("spotify.com"))
async def spotify_handler(message: Message):
    # التحقق من الاشتراك
    is_subscribed = await check_subscription(message.from_user.id, message.bot)
    if not is_subscribed:
        channel_username = await db.get_setting('channel_username')
        await message.answer(
            f"⚠️ <b>يجب عليك الاشتراك في القناة أولاً!</b>\n\n"
            f"📢 القناة: {channel_username}",
            reply_markup=kb.check_subscription(channel_username)
        )
        return
    
    await db.update_user_activity(message.from_user.id)
    
    processing_msg = await message.answer("⏳ جارٍ معالجة الرابط...")
    
    try:
        # هنا يتم إضافة كود التحميل من Spotify
        # يمكن استخدام مكتبة spotdl أو أي مكتبة أخرى
        await processing_msg.edit_text(
            "✅ <b>تم التحميل بنجاح!</b>\n\n"
            "⚠️ ملاحظة: لتفعيل ميزة التحميل الفعلي، يرجى تثبيت مكتبة spotdl وإضافة الكود المناسب."
        )
        
        # مثال على استخدام spotdl (يحتاج تفعيل):
        # from spotdl import Spotdl
        # spotdl = Spotdl(client_id='YOUR_ID', client_secret='YOUR_SECRET')
        # songs = spotdl.search([message.text])
        # song = spotdl.download(songs[0])
        # await message.answer_audio(audio=song)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ حدث خطأ: {str(e)}")

# معالج الرسائل العامة
@router.message()
async def general_handler(message: Message):
    # التحقق من الاشتراك
    is_subscribed = await check_subscription(message.from_user.id, message.bot)
    if not is_subscribed:
        channel_username = await db.get_setting('channel_username')
        await message.answer(
            f"⚠️ <b>يجب عليك الاشتراك في القناة أولاً!</b>\n\n"
            f"📢 القناة: {channel_username}",
            reply_markup=kb.check_subscription(channel_username)
        )
        return
    
    await db.update_user_activity(message.from_user.id)
    await message.answer(
        "❌ لم أفهم طلبك!\n\n"
        "يرجى إرسال رابط من Spotify 🎵"
    )
