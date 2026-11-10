from aiogram.fsm.state import State, StatesGroup

class QuizStates(StatesGroup):
    answering = State()       # Foydalanuvchi savollarga javob berayotgan holat
    awaiting_name = State()   # Sertifikat uchun ism-familiya kiritish holati
