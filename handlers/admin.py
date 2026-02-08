from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import db
from config import ADMIN_ID
import asyncio

router = Router()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_start_msg = State()
    waiting_for_channel = State()

def get_admin_keyboard(notify_new, notify_block):
    kb = [
        [types.InlineKeyboardButton(text="تعديل رسالة الترحيب 📝", callback_data="edit_start")],
        [types.InlineKeyboardButton(text="تغيير قناة الاشتراك 📢", callback_data="edit_channel")],
        [
            types.InlineKeyboardButton(text=f"إشعارات الدخول: {'✅' if notify_new == '1' else '❌'}", callback_data="toggle_new"),
            types.InlineKeyboardButton(text=f"إشعارات الحظر: {'✅' if notify_block == '1' else '❌'}", callback_data="toggle_block")
        ],
        [types.InlineKeyboardButton(text="الإحصائيات 📊", callback_data="stats")],
        [types.InlineKeyboardButton(text="إذاعة للكل 📢", callback_data="broadcast")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: types.Message):
    notify_new = await db.get_setting('notify_new_user')
    notify_block = await db.get_setting('notify_block')
    await message.answer("أهلاً بك في لوحة التحكم الخاصة بالمطور:", reply_markup=get_admin_keyboard(notify_new, notify_block))

@router.callback_query(F.data == "stats", F.from_user.id == ADMIN_ID)
async def show_stats(callback: types.CallbackQuery):
    total, active, blocked = await db.get_stats()
    text = (
        f"📊 إحصائيات البوت:\n\n"
        f"👥 عدد الأعضاء الكلي: {total}\n"
        f"✅ المحادثات النشطة: {active}\n"
        f"🚫 من قاموا بحظر البوت: {blocked}"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(
        await db.get_setting('notify_new_user'),
        await db.get_setting('notify_block')
    ))

@router.callback_query(F.data.startswith("toggle_"), F.from_user.id == ADMIN_ID)
async def toggle_settings(callback: types.CallbackQuery):
    key = "notify_new_user" if "new" in callback.data else "notify_block"
    current = await db.get_setting(key)
    new_val = "1" if current == "0" else "0"
    await db.update_setting(key, new_val)
    
    notify_new = await db.get_setting('notify_new_user')
    notify_block = await db.get_setting('notify_block')
    await callback.message.edit_reply_markup(reply_markup=get_admin_keyboard(notify_new, notify_block))
    await callback.answer("تم التحديث!")

@router.callback_query(F.data == "broadcast", F.from_user.id == ADMIN_ID)
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("أرسل الرسالة التي تريد إذاعتها (نص، صورة، فيديو...) أو أرسل 'إلغاء'")
    await state.set_state(AdminStates.waiting_for_broadcast)
    await callback.answer()

@router.message(AdminStates.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def perform_broadcast(message: types.Message, state: FSMContext):
    if message.text == "إلغاء":
        await message.answer("تم الإلغاء.")
        await state.clear()
        return

    users = await db.get_all_users()
    count = 0
    blocked = 0
    msg = await message.answer(f"جاري الإرسال إلى {len(users)} مستخدم...")

    for user_id in users:
        try:
            await message.copy_to(user_id)
            count += 1
            if count % 20 == 0:
                await msg.edit_text(f"تم إرسال {count} من {len(users)}...")
            await asyncio.sleep(0.05) # تجنب الحظر من تلغرام
        except Exception:
            blocked += 1
            await db.set_user_blocked(user_id, 1)

    await message.answer(f"✅ انتهت الإذاعة!\n\nتم الإرسال لـ: {count}\nفشل الإرسال لـ: {blocked}")
    await state.clear()

@router.callback_query(F.data == "edit_start", F.from_user.id == ADMIN_ID)
async def edit_start_init(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("أرسل رسالة الترحيب الجديدة:")
    await state.set_state(AdminStates.waiting_for_start_msg)
    await callback.answer()

@router.message(AdminStates.waiting_for_start_msg, F.from_user.id == ADMIN_ID)
async def edit_start_save(message: types.Message, state: FSMContext):
    await db.update_setting('start_message', message.text)
    await message.answer("✅ تم تحديث رسالة الترحيب بنجاح!")
    await state.clear()

@router.callback_query(F.data == "edit_channel", F.from_user.id == ADMIN_ID)
async def edit_channel_init(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("أرسل معرف القناة الجديد (مثال: @ManusChannel):")
    await state.set_state(AdminStates.waiting_for_channel)
    await callback.answer()

@router.message(AdminStates.waiting_for_channel, F.from_user.id == ADMIN_ID)
async def edit_channel_save(message: types.Message, state: FSMContext):
    new_channel = message.text if message.text.startswith('@') else f"@{message.text}"
    await db.update_setting('force_channel', new_channel)
    await message.answer(f"✅ تم تحديث قناة الاشتراك الإجباري إلى: {new_channel}")
    await state.clear()
