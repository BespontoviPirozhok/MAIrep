from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import Router

import datetime
import database.requests as rq

from database.requests import get_user

router = Router()


async def admin_check(tg_id: int) -> bool:
    if (await get_user(tg_id)).user_status == 3:
        return True
    else:
        return False


async def manager_check(tg_id: int) -> bool:
    if (await get_user(tg_id)).user_status > 1:
        return True
    else:
        return False


async def common_user_check(tg_id: int) -> bool:
    if (await get_user(tg_id)).user_status > 1:
        return True
    else:
        return False


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
