import asyncio
import logging
from datetime import datetime
from aiogram import Bot
from app import database
from app.keyboards import get_certificate_prompt_keyboard

logger = logging.getLogger(__name__)

async def check_and_send_pending_results(bot: Bot):
    """
    Har 20 soniyada ma'lumotlar bazasini tekshiradi va belgilangan kechikish vaqti
    yetgan natijalarni foydalanuvchiga yuboradi.
    """
    try:
        pending = await database.get_pending_results()
        now = datetime.now()
        for item in pending:
            scheduled_time = datetime.fromisoformat(item["scheduled_notify_at"])
            if now >= scheduled_time:
                user_id = item["user_id"]
                score = item["score"]
                total = item["total_questions"]
                direction_name = item["direction_name"]
                result_id = item["id"]

                # 16 yoki undan ko'p to'g'ri javob bo'lsa (score >= 16)
                if score >= 16:
                    status_text = (
                        f"🎉 <b>Tabriklaymiz! Ajoyib natija!</b>\n\n"
                        f"📊 Yo'nalish: <b>{direction_name}</b>\n"
                        f"✅ Natijangiz: <b>{total} tadan {score} tasi to'g'ri</b>\n\n"
                        f"🎓 <b>Sertifikat olasizmi?</b>"
                    )
                    kb = get_certificate_prompt_keyboard(result_id)
                else:
                    status_text = (
                        f"📋 <b>Test natijangiz tayyor!</b>\n\n"
                        f"📊 Yo'nalish: <b>{direction_name}</b>\n"
                        f"✅ Natijangiz: <b>{total} tadan {score} tasi to'g'ri</b>\n\n"
                        f"ℹ️ Sertifikat olish uchun kamida 16 ta to'g'ri javob talab etiladi. "
                        f"Bilimingizni yanada mustahkamlab, qaytadan urinib ko'rishingiz mumkin! /start"
                    )
                    kb = None

                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=status_text,
                        parse_mode="HTML",
                        reply_markup=kb
                    )
                    await database.mark_result_notified(result_id)
                    logger.info(f"Natija yuborildi: user_id={user_id}, result_id={result_id}")
                except Exception as e:
                    logger.error(f"Foydalanuvchiga xabar yuborishda xatolik (user_id={user_id}): {e}")
    except Exception as e:
        logger.error(f"Scheduler xatoligi: {e}")

async def start_result_scheduler(bot: Bot):
    """Orqa fonda doimiy ishlovchi loop"""
    while True:
        await check_and_send_pending_results(bot)
        await asyncio.sleep(20)
