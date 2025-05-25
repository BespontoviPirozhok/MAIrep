from aiogram.types import Message
from aiogram import Router
from aiogram.filters import CommandStart

import datetime

from database.requests import get_user, add_user

from user_interface.ui_main import return_to_user_menu

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    greetings = "С возвращением"
    tg_id = message.from_user.id
    first_name = message.from_user.first_name
    if not await get_user(tg_id):
        tg_username = message.from_user.username
        greetings = "Добро пожаловать"
        await add_user(
            tg_id=tg_id,
            tg_username=tg_username,
            regist_date=datetime.datetime.now().date(),
        )
    """Красивый ответ на /start"""
    await return_to_user_menu(
        f"""{greetings} в бота GeoEventy, {first_name}! Вот мои функции:
🔍 Поиск мест - поиск интересующих вас мест, их оценка и комментирование
🏝️ Поиск мероприятий - поиск мероприятий и отметка о их посещении
👤 Профиль - информация о ваших посещенных местах, отзывах и комментариях
🤖 Чат с ИИ - возможность поболтать с ИИ и ознакомиться с персональным списком рекомендованных к посещению мест""",
        message,
    )
