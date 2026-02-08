# استخدام صورة بايثون رسمية
FROM python:3.11-slim

# تثبيت التبعيات النظامية و ffmpeg الضروري لـ spotdl
RUN apt-get update && apt-get install -y \
    ffmpeg \
    zip \
    && rm -rf /var/lib/apt/lists/*

# تحديد مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# إنشاء مجلدات البيانات والتحميلات
RUN mkdir -p data downloads

# تشغيل البوت
CMD ["python", "main.py"]
