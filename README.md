# MDev Malaka Baholash va Sertifikatlash Telegram Boti

Ushbu bot **MDev** platformasi uchun ishlab chiqilgan bo'lib, foydalanuvchilarga IT va ofis dasturlari yo'nalishlarida bilimlarini sinab ko'rish hamda muvaffaqiyatli topshirganlarga rasmiy sertifikat taqdim etish imkonini beradi.

---

## 🚀 Texnologiyalar
- **Til:** Python 3.10+
- **Telegram Bot Framework:** aiogram 3.x
- **Ma'lumotlar bazasi:** SQLite (aiosqlite bilan to'liq asinxron)
- **Sertifikat generatsiyasi:** Pillow (PIL) va qrcode
- **Kechiktirilgan xabarnomalar:** Asinxron fon tekshiruvi (Asyncio Background Scheduler)

---

## 📂 Loyiha tuzilmasi
```text
C:\Users\777 comp service\Desktop\certificate\
│
├── .env.example               # Muhit o'zgaruvchilari namunasi (MDEV_URL qo'shilgan)
├── .gitignore                  # Git tomonidan e'tiborga olinmaydigan fayllar
├── requirements.txt            # aiogram 3.x, Pillow, aiosqlite, qrcode
├── main.py                     # Botni ishga tushirish asosiy fayli
├── certificate_maker.py        # make_certificate() - Sertifikat va QR kod generatori
├── README.md                   # O'rnatish va foydalanish yo'riqnomasi
│
├── app/
│   ├── __init__.py
│   ├── config.py               # Sozlamalar (BOT_TOKEN, MDEV_URL, yo'llar)
│   ├── database.py             # SQLite bazasi (test_results, certificates, active_sessions)
│   ├── handlers.py             # /start, /cancel, test jarayoni, ism tekshiruvi va sertifikat berish
│   ├── keyboards.py            # Inline tugmalar (yo'nalishlar, test variantlari, Ha/Yo'q)
│   ├── states.py               # FSM holatlari (QuizStates)
│   ├── questions_loader.py     # Savollar bankini boshqarish
│   ├── scheduler.py            # 15 daqiqalik kechiktirilgan natijalarni yuborish
│   └── certificate.py          # certificate_maker moduliga ko'prik
│
├── data/
│   ├── database.db             # SQLite ma'lumotlar bazasi
│   └── questions.json          # 10 ta yo'nalish bo'yicha 200 ta savollar banki
│
├── assets/
│   └── template.png            # Sertifikat shabloni
│
└── output/                     # Generatsiya qilingan rasmiy sertifikatlar papkasi
```

---

## 🛡 Xavfsizlik va yangi imkoniyatlar
1. **Sertifikat ulanishi va tekshiruvi:**
   - 16 yoki undan ko'p to'g'ri javob topshirilganda "Sertifikat olasizmi?" (Ha / Yo'q) tugmasi chiqadi.
   - "Ha" bosilganda Ism-Familiya so'raladi.
   - **Ism-familiya qat'iy tekshiriladi:** faqat harflar va bo'shliq, uzunligi 2 dan 40 belgigacha. Xavfli belgilar (`/`, `\`, `..`, `<`, `>`) va raqamlar qat'iyan rad etiladi.
   - `certificate_maker.make_certificate(...)` chaqirilib, rasm `output/cert_{user_id}_{cert_id}.png` shaklida saqlanadi va Telegram orqali yuboriladi.
   - Har bir test natijasi bo'yicha **faqat 1 marta** sertifikat beriladi (qayta berish cheklangan).
   - Xatolik yuz bersa, to'liq logga yoziladi va foydalanuvchiga *"Xatolik yuz berdi, keyinroq urinib ko'ring"* xabari beriladi.
2. **QR kod:**
   - Sertifikat ostida `.env` dagi `MDEV_URL` manziliga olib boruvchi QR kod avtomatik joylashtiriladi.

---

## 🛠 O'rnatish va ishga tushirish (Windows)

1. **Terminalni oching va loyiha papkasiga o'ting:**
   ```powershell
   cd "C:\Users\777 comp service\Desktop\certificate"
   ```

2. **Kutubxonalarni o'rnating:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Kodni tekshirish:**
   ```powershell
   python -m py_compile main.py certificate_maker.py app/config.py app/database.py app/handlers.py app/keyboards.py app/scheduler.py app/states.py
   python test_verification.py
   ```

4. **Botni ishga tushiring:**
   ```powershell
   python main.py
   ```
