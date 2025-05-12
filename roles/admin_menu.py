from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import Router

from database.requests import get_user

router = Router()


admin_main_menu_reply = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Поиск мест"),
            KeyboardButton(text="🏝️ Поиск мероприятий"),
        ],
        [
            KeyboardButton(text="Ⓜ️ Меню админа"),
            KeyboardButton(text="🤖 Чат с ИИ"),
        ],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
)

admin_extended_menu_reply = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Выдать роль админа или менеджера"),
            KeyboardButton(text="Ограничить пользователя или снять ограничение"),
        ],
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="Назад в обычное меню"),
        ],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
)
