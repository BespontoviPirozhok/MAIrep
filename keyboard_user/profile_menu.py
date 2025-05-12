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
from datetime import date

from .main_menu import return_to_user_menu, pretty_date
from database.requests import get_user

router = Router()


class Step(StatesGroup):
    profile_menu = State()
    rating_show = State()
    comment_show = State()
    places_show = State()


def compare_times(saved_date: tuple[int, int, int]) -> str:
    def plural_form(n: int, forms: tuple[str, str, str]) -> str:
        n = abs(n) % 100
        n1 = n % 10
        if 11 <= n <= 14:
            return forms[2]
        return forms[0] if n1 == 1 else forms[1] if 2 <= n1 <= 4 else forms[2]

    # Создаем объекты даты из кортежей
    saved_date = date(*saved_date)
    current_date = date.today()

    # Вычисляем абсолютную разницу в днях
    delta_days = abs((current_date - saved_date).days)

    # Разбиваем на годы, месяцы и дни (условные)
    years = delta_days // 360
    remaining_days = delta_days % 360
    months = remaining_days // 30
    days = remaining_days % 30

    parts = []
    if years > 0:
        parts.append(f"{years} {plural_form(years, ('год', 'года', 'лет'))}")
    if months > 0:
        parts.append(f"{months} {plural_form(months, ('месяц', 'месяца', 'месяцев'))}")
    if days > 0 or not parts:
        parts.append(f"{days} {plural_form(days, ('день', 'дня', 'дней'))}")

    return f"Вы с нами уже: {' '.join(parts)}"


# Форматированная информация — только для отображения, я пока не особо имею представление как жто будет выглядеть в БД
info = [
    (2023, 8, 12),  # 12 августа 2023 года
    2,  # отзывы
    4,  # комментарии
    7,  # места
]

profile_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"   Дата регистрации: {pretty_date("2025-12-3")}   ",
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
    await callback.answer(compare_times(info[0]), show_alert=True)
