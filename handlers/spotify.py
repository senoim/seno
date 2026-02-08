from aiogram import Router, types, F
import os
import asyncio
import subprocess
import glob

router = Router()

# التأكد من وجود مجلد للتحميلات
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@router.message(F.text.contains("spotify.com"))
async def handle_spotify_link(message: types.Message):
    url = message.text.strip()
    wait_msg = await message.answer("⏳ جاري معالجة الرابط وتحميل الملف، يرجى الانتظار...")

    # إنشاء مجلد فرعي لكل عملية لتجنب تداخل الملفات
    user_download_path = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
    os.makedirs(user_download_path, exist_ok=True)

    try:
        # استخدام spotdl عبر subprocess لتحميل الملف
        # --output يحدد صيغة اسم الملف ومكانه
        process = await asyncio.create_subprocess_exec(
            "spotdl", "download", url,
            "--output", f"{user_download_path}/{{title}} - {{artist}}.{{output-ext}}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            await wait_msg.edit_text("❌ عذراً، فشل تحميل الملف. تأكد من صحة الرابط.")
            return

        # البحث عن ملفات mp3 المحملة في المجلد
        files = glob.glob(f"{user_download_path}/*.mp3")
        
        if not files:
            await wait_msg.edit_text("❌ لم يتم العثور على ملفات محملة.")
            return

        await wait_msg.edit_text("✅ تم التحميل! جاري إرسال الملف...")

        for file_path in files:
            audio = types.FSInputFile(file_path)
            await message.answer_audio(audio)
            # حذف الملف بعد الإرسال لتوفير المساحة
            os.remove(file_path)

    except Exception as e:
        await wait_msg.edit_text(f"❌ حدث خطأ غير متوقع: {str(e)}")
    finally:
        # تنظيف المجلد
        try:
            if os.path.exists(user_download_path):
                for f in os.listdir(user_download_path):
                    os.remove(os.path.join(user_download_path, f))
                os.rmdir(user_download_path)
        except:
            pass
