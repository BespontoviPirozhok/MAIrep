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
from database.requests import (
    get_user,
    get_comments,
    count_non_zero_rating_comments
)
from roles.roles_main import (
    admin_check,
    get_user_status_text,
    owner_check
)

router = Router()


class Step(StatesGroup):
    profile_menu = State()
    rating_show = State()
    comment_show = State()
    places_show = State()


def compare_times(date_str: str) -> str:
    def plural_form(n: int, forms: tuple[str, str, str]) -> str:
        n = abs(n) % 100
        n1 = n % 10
        if 11 <= n <= 14:
            return forms[2]
        return forms[0] if n1 == 1 else forms[1] if 2 <= n1 <= 4 else forms[2]

    # Разбираем строку даты
    year, month, day = map(int, date_str.split('-'))
    saved_date = date(year, month, day)
    current_date = date.today()

    # Если дата регистрации совпадает с текущей датой
    if saved_date == current_date:
        return "Вы зарегистрировались сегодня"

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
    if days > 0:
        parts.append(f"{days} {plural_form(days, ('день', 'дня', 'дней'))}")

    return f"Вы с нами уже: {' '.join(parts)}"



async def def_keyboard(tg_id: int, message: Message):
    user_info = await get_user(tg_id)
    reg_date = user_info.regist_date
    status_text = await get_user_status_text(tg_id)
    all_comments = await get_comments(None, tg_id)
    non_zero_comments = await count_non_zero_rating_comments(None, tg_id)

    profile_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"   Дата регистрации: {await pretty_date(str(reg_date))}   ",
                callback_data="reg_date",
            )
        ],

        [
            InlineKeyboardButton(
                text=f"Кол-во посещённых мест: {len(all_comments)}", callback_data="places"
            )
        ],

        [
            InlineKeyboardButton(
                text=f"Кол-во оценок: {non_zero_comments}", callback_data="reviews"
            )
        ],

        [
            InlineKeyboardButton(
                text=f"Кол-во комментариев: {non_zero_comments}", callback_data="reviews"
            )
        ],
    
        [
            InlineKeyboardButton(
                text=f"Кол-во посещённых мероприятий: 42", callback_data="events"
            )
        ],
        
        [InlineKeyboardButton(text="Назад", callback_data="back")],
    ],
    input_field_placeholder="Выберите пункт",
)
    await message.answer(f"Меню профиля:\nВаша роль: {status_text}", reply_markup=profile_keyboard)
    print(non_zero_comments)
    


@router.message(F.text == "👤 Профиль")
async def profile(message: Message, state: FSMContext):
    await state.set_state(Step.profile_menu)
    await message.answer(
        "Загрузка вашего профиля 🌐", reply_markup=ReplyKeyboardRemove()
    )
    user_id = message.from_user.id
    await def_keyboard(user_id, message)


@router.callback_query(F.data == "back")
async def exit(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()
    await return_to_user_menu(
        callback.from_user.id, "Операция отменена", callback.message
    )


@router.callback_query(F.data == "reg_date")
async def show_reg_date(callback: CallbackQuery):
    user_info = await get_user(callback.from_user.id)
    reg_date = str(user_info.regist_date)
    await callback.answer(compare_times(reg_date), show_alert=True)