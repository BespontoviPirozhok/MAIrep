from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
)
from aiogram import Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import F
from datetime import datetime

from .main_menu import return_to_user_menu

router = Router()


class Step(StatesGroup):
    profile_menu = State()
    rating_show = State()
    comment_show = State()
    places_show = State()


def beautiful_time(time: datetime) -> str:
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

    day = time.day
    month = months_ru[time.month - 1]
    year = time.year
    return f"{day} {month} {year} г."


from datetime import datetime


def compare_times(saved_time: datetime) -> str:
    def plural_form(n: int, forms: tuple[str, str, str]) -> str:
        n = abs(n) % 100
        n1 = n % 10
        if 11 <= n <= 14:
            return forms[2]
        if n1 == 1:
            return forms[0]
        if 2 <= n1 <= 4:
            return forms[1]
        return forms[2]

    now = datetime.now()
    now = now.replace(minute=0, second=0, microsecond=0)
    saved_time = saved_time.replace(minute=0, second=0, microsecond=0)

    delta_days = (now - saved_time).days
    years = delta_days // 360
    months = (delta_days % 360) // 30
    days = (delta_days % 360) % 30

    parts = []
    if years > 0:
        parts.append(f"{years} {plural_form(years, ('год', 'года', 'лет'))}")
    if months > 0:
        parts.append(f"{months} {plural_form(months, ('месяц', 'месяца', 'месяцев'))}")
    if days > 0 or not parts:
        parts.append(f"{days} {plural_form(days, ('день', 'дня', 'дней'))}")

    return f"Вы с нами уже: {' '.join(parts)}"


saved_time = datetime(1666, 8, 8, 23, 59)

# Форматированная информация — только для отображения
info = [
    beautiful_time(saved_time),  # [0]
    2,  # отзывы
    4,  # комментарии
    7,  # места
]

profile_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"   Дата регистрации: {info[0]}   ",
                callback_data="reg_date",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Кол-во отзывов: {info[1]}", callback_data="reviews"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Кол-во комментариев: {info[2]}", callback_data="comments"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Кол-во посещенных мест: {info[3]}", callback_data="places"
            )
        ],
        [InlineKeyboardButton(text="Назад", callback_data="back")],
    ],
    input_field_placeholder="Выберите пункт",
)


@router.message(F.text == "👤 Профиль")
async def profile(message: Message, state: FSMContext):
    await state.set_state(Step.profile_menu)
    await message.answer(
        "Загрузка вашего профиля 🌐", reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("Меню профиля:", reply_markup=profile_keyboard)


@router.callback_query(F.data == "back")
async def exit(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()
    await return_to_user_menu("Операция отменена", callback.message)


@router.callback_query(F.data == "reg_date")
async def show_reg_date(callback: CallbackQuery):
    # используем объект datetime (saved_time), а не info[0] (строка)
    text = compare_times(saved_time)
    await callback.answer(text, show_alert=True)
