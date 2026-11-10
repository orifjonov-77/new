from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any

def get_directions_keyboard(directions: List[Dict[str, str]]) -> InlineKeyboardMarkup:
    """Yo'nalishlarni 2 ustunda ko'rsatish"""
    buttons = []
    row = []
    for item in directions:
        btn = InlineKeyboardButton(
            text=f"📚 {item['title']}", 
            callback_data=f"dir:{item['id']}"
        )
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_question_keyboard(options: Dict[str, str], current_q: int) -> InlineKeyboardMarkup:
    """
    Savol variantlari tugmalari.
    callback_data formatida qidx bo'lishi takroriy yoki eski tugmalarni bosishdan himoya qiladi.
    """
    buttons = []
    for key in ["A", "B", "C", "D"]:
        if key in options:
            btn = InlineKeyboardButton(
                text=f"{key}) {options[key]}",
                callback_data=f"ans:{current_q}:{key}"
            )
            buttons.append([btn])
            
    # Bekor qilish tugmasi
    cancel_btn = InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_quiz")
    buttons.append([cancel_btn])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_certificate_prompt_keyboard(result_id: int) -> InlineKeyboardMarkup:
    """Sertifikat olish taklifi tugmasi (Ha / Yo'q)"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Ha", callback_data=f"cert_yes:{result_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"cert_no:{result_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
