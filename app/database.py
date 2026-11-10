import aiosqlite
import os
from datetime import datetime
from app.config import DB_PATH

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        # Test natijalari jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                direction_id TEXT NOT NULL,
                direction_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                completed_at TIMESTAMP NOT NULL,
                scheduled_notify_at TIMESTAMP NOT NULL,
                is_notified INTEGER DEFAULT 0
            )
        """)
        # Sertifikat berilgan foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course TEXT NOT NULL,
                full_name TEXT NOT NULL,
                issued_at TIMESTAMP NOT NULL,
                certificate_path TEXT NOT NULL,
                test_result_id INTEGER UNIQUE
            )
        """)
        # Foydalanuvchining ayni vaqtda faol testi bormi-yo'qligini tekshirish uchun jadval
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_sessions (
                user_id INTEGER PRIMARY KEY,
                direction_id TEXT NOT NULL,
                direction_name TEXT NOT NULL,
                current_question INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                answers_json TEXT DEFAULT '[]',
                started_at TIMESTAMP NOT NULL
            )
        """)
        await db.commit()

async def get_active_session(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM active_sessions WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def create_active_session(user_id: int, direction_id: str, direction_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute(
            """INSERT OR REPLACE INTO active_sessions 
               (user_id, direction_id, direction_name, current_question, score, started_at) 
               VALUES (?, ?, ?, 0, 0, ?)""",
            (user_id, direction_id, direction_name, now)
        )
        await db.commit()

async def update_active_session(user_id: int, current_question: int, score: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE active_sessions SET current_question = ?, score = ? WHERE user_id = ?",
            (current_question, score, user_id)
        )
        await db.commit()

async def delete_active_session(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM active_sessions WHERE user_id = ?", (user_id,))
        await db.commit()

async def save_test_result(user_id: int, direction_id: str, direction_name: str, score: int, total_questions: int, scheduled_notify_at: datetime):
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO test_results 
               (user_id, direction_id, direction_name, score, total_questions, completed_at, scheduled_notify_at, is_notified)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
            (user_id, direction_id, direction_name, score, total_questions, now, scheduled_notify_at.isoformat())
        )
        await db.commit()
        return cursor.lastrowid

async def get_pending_results():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM test_results WHERE is_notified = 0"
        ) as cursor:
            return await cursor.fetchall()

async def mark_result_notified(result_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE test_results SET is_notified = 1 WHERE id = ?", (result_id,))
        await db.commit()

async def get_certificate_by_test_result(test_result_id: int):
    """Bitta test natijasi bo'yicha allaqachon sertifikat berilganligini tekshirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM certificates WHERE test_result_id = ?", (test_result_id,)
        ) as cursor:
            return await cursor.fetchone()

async def save_certificate(user_id: int, course: str, full_name: str, certificate_path: str, test_result_id: int):
    """Sertifikat ma'lumotlarini bazada saqlash"""
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO certificates (user_id, course, full_name, issued_at, certificate_path, test_result_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, course, full_name, now, certificate_path, test_result_id)
        )
        await db.commit()
        return cursor.lastrowid
