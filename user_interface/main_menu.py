from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import Router
from aiogram.filters import CommandStart

import datetime

from database.requests import get_user, add_user
from roles.roles_main import admin_check
from ai_services.yandex_gpt import you_mean

router = Router()

main_menu_reply = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Поиск мест"),
            KeyboardButton(text="🏝️ Поиск мероприятий"),
        ],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🤖 Чат с ИИ")],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
)

admin_menu_reply = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Поиск мест"),
            KeyboardButton(text="🏝️ Поиск мероприятий"),
        ],
        [
            KeyboardButton(text="Ⓜ️ Админ-меню"),
            KeyboardButton(text="🤖 Чат с ИИ"),
        ],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
)


back_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


async def return_to_user_menu(
    tg_id: int,
    msg_txt: str,
    message: Message,
) -> None:
    if await admin_check(tg_id):
        await message.answer(
            msg_txt,
            reply_markup=admin_menu_reply,
        )
    else:
        await message.answer(
            msg_txt,
            reply_markup=main_menu_reply,
        )


def pretty_date(date_str: str) -> str:
    months_ru = [
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ]
    year, month, day = map(int, date_str.split("-"))

    return f"{day} {months_ru[month-1]} {year} г."


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
        tg_id,
        f"""{greetings} в бота Location Chooser, {first_name}! Вот мои функции:
🔍 Поиск мест - поиск интересующих вас мест, их оценка и комментирование
💬 Чат с ИИ - возможность по душам поболтать с искусственным интеллектом
🪪 Профиль - информация о ваших посещенных местах, отзывах и комментариях
🏝️ Поиск мероприятий - поиск мероприятий и отметка о их посещении""",
        message,
    )
