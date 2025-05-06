from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import Router
from aiogram.filters import CommandStart
import datetime


router = Router()
error_rt = Router()

main_menu_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Поиск мест"), KeyboardButton(text="🤖 Чат с ИИ")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="❓ Помощь")],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
)


back_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
)


async def return_to_user_menu(
    msg: str,
    message: Message,
    keyboard: ReplyKeyboardMarkup = main_menu_reply,
) -> None:
    await message.answer(
        msg,
        reply_markup=keyboard,
    )


def beautiful_date(date_tuple: tuple[int, int, int]) -> str:
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

    year, month, day = date_tuple
    return f"{day} {months_ru[month-1]} {year} г."


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Красивый ответ на /start
    """
    now = datetime.datetime.now()
    if 4 <= now.hour <= 11:
        await message.answer(f"Доброе утро, {(message.from_user.full_name)}! 🌄")
    if 12 <= now.hour <= 16:
        await message.answer(f"Добрый день, {(message.from_user.full_name)}! ⛅")
    if 17 <= now.hour <= 23:
        await message.answer(f"Добрый вечер, {(message.from_user.full_name)}! 🌇")
    if 0 <= now.hour <= 3:
        await message.answer(f"Доброй ночи, {(message.from_user.full_name)}! 🌃")
    await return_to_user_menu(
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
        "Увы, мне не понятны ваши слова, ибо я понимаю только команды 😔", message
    )
