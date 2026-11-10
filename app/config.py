import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
RESULT_DELAY_MINUTES = float(os.getenv("RESULT_DELAY_MINUTES", "15"))
MDEV_URL = os.getenv("MDEV_URL", "https://mdev.uz").strip()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "database.db")
QUESTIONS_PATH = os.path.join(BASE_DIR, "data", "questions.json")
TEMPLATE_PATH = os.path.join(BASE_DIR, "assets", "template.png")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
