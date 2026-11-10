import logging
import re
import os
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from app import database
from app.config import RESULT_DELAY_MINUTES
from app.states import QuizStates
from app.keyboards import (
    get_directions_keyboard, 
    get_question_keyboard, 
    get_certificate_prompt_keyboard
)
from app.questions_loader import (
    get_directions, 
    get_questions_for_direction, 
    get_direction_title
)
import certificate_maker

logger = logging.getLogger(__name__)
router = Router()

# Ism va familiyani tekshirish: faqat harf va bo'shliqlar (o'zbek lotin, kirill va ingliz harflari)
NAME_REGEX = re.compile(r"^[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ\s'ʻ`-]+$")
DANGEROUS_CHARS = ["/", "\\", "..", "<", ">"]

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Faol test mavjudligini tekshirish
    active = await database.get_active_session(user_id)
    if active:
        await message.answer(
            f"⚠️ Sizda ayni vaqtda <b>\"{active['direction_name']}\"</b> yo'nalishi bo'yicha faol test mavjud!\n\n"
            f"Testni davom ettirishingiz yoki /cancel buyrug'i orqali to'xtatishingiz mumkin.",
            parse_mode="HTML"
        )
        return

    await state.clear()
    directions = get_directions()
    welcome_text = (
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        f"🌟 <b>MDev</b> malaka baholash va sertifikatlash tizimiga xush kelibsiz!\n"
        f"Bu yerda siz turli IT va ofis dasturlari bo'yicha bilimlaringizni sinab ko'rishingiz "
        f"hamda rasmiy sertifikatga ega bo'lishingiz mumkin.\n\n"
        f"📌 Test shartlari:\n"
        f"• Har bir yo'nalishda 20 ta test savoli beriladi.\n"
        f"• Test natijasi yakunlangandan so'ng <b>15 daqiqa o'tgach</b> yuboriladi.\n"
        f"• 16 yoki undan ko'p to'g'ri javob topsangiz, <b>MDev Sertifikati</b> taqdim etiladi!\n\n"
        f"Marhamat, test topshirmoqchi bo'lgan yo'nalishingizni tanlang:"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_directions_keyboard(directions),
        parse_mode="HTML"
    )

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    user_id = message.from_user.id
    active = await database.get_active_session(user_id)
    if active:
        await database.delete_active_session(user_id)
        await state.clear()
        await message.answer(
            "🛑 Test to'xtatildi. Istalgan vaqtda qaytadan /start bosib yangi test boshlashingiz mumkin."
        )
    else:
        await state.clear()
        await message.answer(
            "ℹ️ Hozirda faol test mavjud emas. Yangi test boshlash uchun /start buyrug'ini yuboring."
        )

@router.callback_query(F.data == "cancel_quiz")
async def callback_cancel_quiz(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await database.delete_active_session(user_id)
    await state.clear()
    await callback.message.edit_text(
        "🛑 Test to'xtatildi. Istalgan vaqtda qaytadan /start bosib yangi test topshirishingiz mumkin."
    )
    await callback.answer("Test bekor qilindi.")

@router.callback_query(F.data.startswith("dir:"))
async def on_direction_selected(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    direction_id = callback.data.split(":")[1]

    # Boshqa faol test bor-yo'qligini tekshirish
    active = await database.get_active_session(user_id)
    if active:
        await callback.answer("Sizda allaqachon faol test mavjud!", show_alert=True)
        return

    questions = get_questions_for_direction(direction_id)
    if not questions:
        await callback.answer("Ushbu yo'nalish uchun savollar topilmadi.", show_alert=True)
        return

    direction_name = get_direction_title(direction_id)
    await database.create_active_session(user_id, direction_id, direction_name)
    await state.set_state(QuizStates.answering)
    await state.update_data(
        direction_id=direction_id,
        direction_name=direction_name,
        current_q=0,
        score=0,
        total=len(questions)
    )

    first_q = questions[0]
    text = (
        f"📚 <b>Yo'nalish:</b> {direction_name}\n\n"
        f"<b>1-savol (jami {len(questions)} ta):</b>\n"
        f"{first_q['question']}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_question_keyboard(first_q["options"], 0),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("ans:"))
async def on_answer_received(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    q_index = int(parts[1])
    selected_option = parts[2]

    active = await database.get_active_session(user_id)
    if not active:
        await callback.answer("Faol test sessiyasi topilmadi. Qaytadan /start bosing.", show_alert=True)
        return

    direction_id = active["direction_id"]
    current_db_q = active["current_question"]
    current_score = active["score"]

    if q_index != current_db_q:
        await callback.answer("Bu savolga allaqachon javob berilgan!", show_alert=False)
        return

    questions = get_questions_for_direction(direction_id)
    if q_index >= len(questions):
        await callback.answer()
        return

    correct_option = questions[q_index].get("answer")
    new_score = current_score + (1 if selected_option == correct_option else 0)
    next_q = q_index + 1

    if next_q < len(questions):
        await database.update_active_session(user_id, next_q, new_score)
        await state.update_data(current_q=next_q, score=new_score)

        next_q_data = questions[next_q]
        text = (
            f"📚 <b>Yo'nalish:</b> {active['direction_name']}\n\n"
            f"<b>{next_q + 1}-savol (jami {len(questions)} ta):</b>\n"
            f"{next_q_data['question']}"
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_question_keyboard(next_q_data["options"], next_q),
            parse_mode="HTML"
        )
        await callback.answer("Javob qabul qilindi.")
    else:
        # Test yakunlandi
        total_questions = len(questions)
        await database.delete_active_session(user_id)
        await state.clear()

        delay_minutes = RESULT_DELAY_MINUTES
        scheduled_notify_at = datetime.now() + timedelta(minutes=delay_minutes)
        await database.save_test_result(
            user_id=user_id,
            direction_id=direction_id,
            direction_name=active["direction_name"],
            score=new_score,
            total_questions=total_questions,
            scheduled_notify_at=scheduled_notify_at
        )

        finish_text = (
            f"✅ <b>Siz testni muvaffaqiyatli yakunladingiz!</b>\n\n"
            f"Yo'nalish: <b>{active['direction_name']}</b>\n"
            f"Savollar soni: <b>{total_questions} ta</b>\n\n"
            f"⏳ <i>MDev qoidalariga ko'ra, natijangiz tekshirilmoqda va {int(delay_minutes)} daqiqadan so'ng "
            f"ushbu bot orqali e'lon qilinadi.</i>\n\n"
            f"Sabringiz uchun rahmat!"
        )
        await callback.message.edit_text(finish_text, parse_mode="HTML")
        await callback.answer("Test yakunlandi!")

@router.callback_query(F.data.startswith("cert_no:"))
async def on_cert_declined(callback: CallbackQuery):
    await callback.message.edit_text(
        "Tushunarli. Agar keyinchalik qayta test topshirmoqchi bo'lsangiz, /start buyrug'idan foydalaning. Omad!"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cert_yes:"))
async def on_cert_accepted(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    result_id = int(callback.data.split(":")[1])

    # Natija ma'lumotlarini olish
    async with database.aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = database.aiosqlite.Row
        async with db.execute("SELECT * FROM test_results WHERE id = ?", (result_id,)) as cursor:
            res = await cursor.fetchone()

    if not res:
        await callback.answer("Natija topilmadi.", show_alert=True)
        return

    # Faqat natija egasi sertifikat olishi mumkin
    if res["user_id"] != user_id:
        await callback.answer("Bu natija sizga tegishli emas!", show_alert=True)
        return

    # Bir test uchun bir marta sertifikat olish tekshiruvi
    existing_cert = await database.get_certificate_by_test_result(result_id)
    if existing_cert:
        await callback.answer("Ushbu test uchun sertifikat allaqachon berilgan!", show_alert=True)
        if os.path.exists(existing_cert["certificate_path"]):
            photo = FSInputFile(existing_cert["certificate_path"])
            await callback.message.answer_photo(
                photo=photo,
                caption=f"Sizning ushbu test bo'yicha oldin olingan sertifikatingiz ({existing_cert['course']})."
            )
        return

    await state.set_state(QuizStates.awaiting_name)
    await state.update_data(
        cert_result_id=result_id,
        direction_name=res["direction_name"],
        score=res["score"]
    )

    prompt_text = (
        f"🎓 <b>Sertifikat rasmiylashtirish</b>\n\n"
        f"Iltimos, sertifikatda ko'rsatilishi kerak bo'lgan <b>Ism va Familiyangizni</b> yozib yuboring.\n"
        f"<i>(Masalan: Rustam Karimov)</i>\n\n"
        f"⚠️ <i>Eslatma: 2 dan 40 tagacha harflardan iborat bo'lishi lozim.</i>"
    )
    await callback.message.answer(prompt_text, parse_mode="HTML")
    await callback.answer()

@router.message(QuizStates.awaiting_name)
async def on_name_submitted(message: Message, state: FSMContext, bot: Bot):
    full_name = message.text.strip() if message.text else ""

    # Xavfsizlik: xavfli belgilarni tekshirish (/, \, .., <, >)
    for bad_char in DANGEROUS_CHARS:
        if bad_char in full_name:
            await message.answer("⚠️ Ism-familiyada taqiqlangan maxsus belgilar mavjud. Iltimos, qaytadan to'g'ri kiriting:")
            return

    # Uzunlik tekshiruvi: 2 dan 40 belgigacha
    if len(full_name) < 2 or len(full_name) > 40:
        await message.answer("⚠️ Ism va familiya uzunligi 2 dan 40 tagacha belgidan iborat bo'lishi kerak. Qaytadan kiriting:")
        return

    # Faqat harf va bo'shliq bo'lishi tekshiruvi
    if not NAME_REGEX.match(full_name):
        await message.answer("⚠️ Ism va familiya faqat harflar va bo'shliqdan iborat bo'lishi kerak. Qaytadan kiriting:")
        return

    data = await state.get_data()
    result_id = data.get("cert_result_id")
    course = data.get("direction_name", "IT Mutaxassis")
    score = data.get("score", 20)
    user_id = message.from_user.id

    if not result_id:
        await message.answer("Xatolik yuz berdi, keyinroq urinib ko'ring")
        await state.clear()
        return

    # Qayta tekshirish: ushbu test natijasi bo'yicha sertifikat olinganmi?
    existing_cert = await database.get_certificate_by_test_result(result_id)
    if existing_cert:
        await message.answer("⚠️ Ushbu test uchun sertifikat allaqachon olingan!")
        await state.clear()
        return

    await message.answer("⏳ Sertifikatingiz tayyorlanmoqda, iltimos kuting...")

    try:
        # certificate_maker.make_certificate chaqiriladi
        cert_path = certificate_maker.make_certificate(
            full_name=full_name,
            course=course,
            score=score,
            cert_id=result_id,
            user_id=user_id
        )

        # Bazaga yozish: id, user_id, course, full_name, issued_at, certificate_path, test_result_id
        await database.save_certificate(
            user_id=user_id,
            course=course,
            full_name=full_name,
            certificate_path=cert_path,
            test_result_id=result_id
        )

        caption = (
            f"🎉 <b>Tabriklaymiz, {full_name}!</b>\n\n"
            f"Sizning <b>MDev</b> malaka sertifikatingiz muvaffaqiyatli tayyorlandi!\n"
            f"Ushbu sertifikat sizning {course} yo'nalishidagi bilimingizni tasdiqlaydi.\n\n"
            f"Kelgusi faoliyatingizda ulkan zafarlar tilaymiz! 🚀"
        )
        photo = FSInputFile(cert_path)
        await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML")
        await state.clear()
    except Exception as e:
        logger.error(f"Sertifikat yaratishda xatolik yuz berdi: {e}", exc_info=True)
        await message.answer("Xatolik yuz berdi, keyinroq urinib ko'ring")
        await state.clear()
