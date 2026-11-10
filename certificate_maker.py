import os
import logging
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from app.config import TEMPLATE_PATH, OUTPUT_DIR, MDEV_URL

logger = logging.getLogger(__name__)

try:
    import qrcode
except ImportError:
    qrcode = None

def create_default_template(path: str = TEMPLATE_PATH):
    """
    Agar template.png mavjud bo'lmasa, yuqori sifatli sertifikat shablonini generatsiya qiladi.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        return

    width, height = 1920, 1080
    image = Image.new("RGB", (width, height), "#0b132b")
    draw = ImageDraw.Draw(image)

    border_color_gold = "#e0a96d"
    border_color_light = "#1c2541"
    
    # Ramkalar
    draw.rectangle([40, 40, width - 40, height - 40], outline=border_color_gold, width=4)
    draw.rectangle([55, 55, width - 55, height - 55], outline=border_color_light, width=2)
    draw.rectangle([70, 70, width - 70, height - 70], outline=border_color_gold, width=2)

    # Burchak bezaklari
    for cx, cy in [(70, 70), (width - 70, 70), (70, height - 70), (width - 70, height - 70)]:
        draw.rectangle([cx - 15, cy - 15, cx + 15, cy + 15], fill=border_color_gold)

    try:
        font_logo = ImageFont.truetype("arialbd.ttf", 64)
        font_title = ImageFont.truetype("arialbd.ttf", 72)
        font_sub = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font_logo = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text((width // 2, 160), "MDEV ACADEMY", fill="#48cae4", font=font_logo, anchor="mm")
    draw.text((width // 2, 220), "MALAKANI BAHOLASH VA SERTIFIKATLASHTIRISH MARKAZI", fill="#adb5bd", font=font_sub, anchor="mm")
    draw.text((width // 2, 330), "SERTIFIKAT", fill=border_color_gold, font=font_title, anchor="mm")
    draw.line([(width // 2 - 250, 390), (width // 2 + 250, 390)], fill=border_color_gold, width=3)
    draw.text((width // 2, 440), "Ushbu sertifikat muvaffaqiyatli test topshirgani uchun taqdim etiladi:", fill="#e0e1dd", font=font_sub, anchor="mm")

    try:
        font_footer = ImageFont.truetype("arial.ttf", 24)
        font_footer_b = ImageFont.truetype("arialbd.ttf", 26)
    except Exception:
        font_footer = ImageFont.load_default()
        font_footer_b = ImageFont.load_default()

    draw.line([(250, 920), (550, 920)], fill="#adb5bd", width=2)
    draw.text((400, 950), "MDev Rahbari", fill="#adb5bd", font=font_footer, anchor="mm")

    draw.line([(width - 550, 920), (width - 250, 920)], fill="#adb5bd", width=2)
    draw.text((width - 400, 950), "Tekshirildi va Tasdiqlandi", fill="#adb5bd", font=font_footer, anchor="mm")

    image.save(path, format="PNG")


def generate_qr_code(url: str, size: int = 140) -> Image.Image:
    """MDEV_URL havolasi uchun QR kod rasm hosil qiladi"""
    if qrcode is not None:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0b132b", back_color="#ffffff").convert("RGBA")
        return img.resize((size, size))
    else:
        # qrcode o'rnatilmagan bo'lsa zaxira oq to'rtburchak
        placeholder = Image.new("RGBA", (size, size), "#ffffff")
        p_draw = ImageDraw.Draw(placeholder)
        p_draw.text((size // 2, size // 2), "MDev QR", fill="#000000", anchor="mm")
        return placeholder


def make_certificate(full_name: str, course: str, score: int, cert_id: int, user_id: int) -> str:
    """
    Foydalanuvchi ma'lumotlari va MDEV_URL QR kodi bilan tayyor sertifikat faylini 
    output papkasida xavfsiz nom bilan yaratadi va yo'lini qaytaradi.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(TEMPLATE_PATH):
        create_default_template(TEMPLATE_PATH)

    image = Image.open(TEMPLATE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # Shriftlarni yuklash
    try:
        font_name = ImageFont.truetype("arialbd.ttf", 68)
        font_body = ImageFont.truetype("arial.ttf", 32)
        font_meta = ImageFont.truetype("arial.ttf", 24)
        font_qr_label = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font_name = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_meta = ImageFont.load_default()
        font_qr_label = ImageFont.load_default()

    # Ism-familiya
    clean_name = " ".join(full_name.split())
    draw.text((width // 2, 540), clean_name.upper(), fill="#ffffff", font=font_name, anchor="mm")

    # Yo'nalish va natija matni
    body_text = f"\"{course}\" yo'nalishi bo'yicha nazariy va amaliy test savollarini"
    draw.text((width // 2, 630), body_text, fill="#caf0f8", font=font_body, anchor="mm")
    
    score_text = f"muvaffaqiyatli topshirdi va {score}/20 ball to'pladi."
    draw.text((width // 2, 680), score_text, fill="#caf0f8", font=font_body, anchor="mm")

    # Sertifikat ID va sana
    date_str = datetime.now().strftime("%d.%m.%Y")
    cert_no = f"MDEV-{cert_id:05d}"
    draw.text((width // 2, 750), f"Sana: {date_str}   |   Sertifikat №: {cert_no}", fill="#90e0ef", font=font_meta, anchor="mm")

    # QR kod joylashtirish (MDEV_URL manziliga yo'naltiruvchi)
    target_url = MDEV_URL if MDEV_URL else "https://mdev.uz"
    qr_img = generate_qr_code(target_url, size=130)
    qr_x = (width - 130) // 2
    qr_y = 825
    image.paste(qr_img, (qr_x, qr_y), qr_img)

    # QR kod ostidagi yozuv
    draw.text((width // 2, 970), f"Rasmiy tekshirish: {target_url}", fill="#e0a96d", font=font_qr_label, anchor="mm")

    # Xavfsiz fayl nomi: har bir foydalanuvchi va sertifikat ID alohida saqlanadi
    output_filename = f"cert_{user_id}_{cert_id}.png"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    rgb_image = image.convert("RGB")
    rgb_image.save(output_path, format="PNG")
    logger.info(f"Sertifikat yaratildi: {output_path}")
    return output_path
