from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import Router, F

from .main_menu import return_to_user_menu

router = Router()


@router.message(F.text == "🤖 Чат с ИИ")
async def ai(message: Message):
    await return_to_user_menu("ИИ устал, он отдыхает", message)
