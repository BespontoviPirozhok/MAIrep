from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import Router
from aiogram.filters import CommandStart

import datetime

from database.requests import get_user, set_user
from roles.roles_main import admin_check

router = Router()
error_rt = Router()

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
    user_tg_id = message.from_user.id
    await set_user(tg_id=user_tg_id, regist_date=datetime.datetime.now().date())
    """Красивый ответ на /start"""

    now = datetime.datetime.now()
    hour = now.hour
    time_str = now.strftime("%H:%M")  # Форматируем время как ЧЧ:ММ
    first_name = message.from_user.first_name
    emoji = "🌃"

    # Определяем приветственную фразу
    if 4 <= hour <= 11:
        greeting = "Доброе утро"
        emoji = "🌄"
    elif 12 <= hour <= 16:
        greeting = "Добрый день"
        emoji = "⛅"
    elif 17 <= hour <= 23:
        greeting = "Добрый вечер"
        emoji = "🌇"
    else:
        greeting = "Доброй ночи"

    # Отправляем приветственное сообщение
    await message.answer(
        f"В Москве сейчас {time_str}\n{greeting}, {first_name}! {emoji}"
    )

    # Отправляем меню
    await return_to_user_menu(
        user_tg_id,
        """Добро пожаловать в бота Location Chooser, вот мои функции:
🔍 Поиск мест - поиск интересующих вас мест
💬 Чат с ИИ - возможность по душам поболтать с искусственным интеллектом
🪪 Профиль - информация о ваших посещенных местах, отзывах и комментариях
❓ Помощь - вывод данной справки еще раз или отправка сообщения о неполадке бота службе поддержки""",
        message,
    )


@error_rt.message()
async def unknown_command(message: Message) -> None:
    """
    Ответ на неизвестное сообщение
    """
    await return_to_user_menu(
        message.from_user.id,
        "Увы, мне не понятны ваши слова, ибо я понимаю только команды 😔",
        message,
    )
