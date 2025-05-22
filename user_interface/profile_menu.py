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
from aiogram.filters import StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import F
from datetime import date
from typing import List
from dataclasses import dataclass
from typing import Callable, Any, List
from .main_menu import return_to_user_menu, pretty_date, back_reply
from database.requests import (
    get_user,
    get_comments,
    get_place,
    get_full_comment_data_by_user,
    get_events,
)
from roles.roles_main import get_user_status_text


PAGINATOR_CONFIG = {
    "comments": {
        "batch_size": 3,
        "format_func": lambda item: f"*{item.name}*\n{item.address}\n\n {item.comment_text}",
        "item_name": "комментариев",
    },
    "ratings": {
        "batch_size": 4,
        "format_func": lambda item: f"*{item.name}*\n{item.address}\n{item.commentator_rating * "⭐"}",
        "item_name": "оценок",
    },
    "just_visits": {
        "batch_size": 4,
        "format_func": lambda item: f"*{item.name}*\n{item.address}",
        "item_name": "посещенных мест",
    },
    "events": {
        "batch_size": 4,
        "format_func": lambda item: f"*{item.event_name}*\n{item.event_time}",
        "item_name": "мероприятий",
    },
}

router = Router()


class Step(StatesGroup):
    profile_menu = State()
    rating_show = State()
    comment_show = State()
    visits_show = State()
    events_show = State()


async def profile_keyboard(tg_id: int, message: Message, state: FSMContext):
    user_info = await get_user(tg_id)
    reg_date = user_info.regist_date
    status_text = await get_user_status_text(tg_id)
    all_comments = (await get_full_comment_data_by_user(tg_id))[::-1]
    await state.update_data(all_comments=all_comments)
    ratings = [c for c in all_comments if c.commentator_rating != 0]
    await state.update_data(ratings=ratings)
    comments = [c for c in all_comments if c.comment_text != ""]
    await state.update_data(comments=comments)
    events = await get_events(tg_id)
    await state.update_data(events=events)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Дата регистрации: {pretty_date(str(reg_date))}",
                    callback_data="reg_date",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Посещённые места: {len(all_comments)}",
                    callback_data="visits",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Оценки: {len(ratings)}", callback_data="ratings"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Комментарии: {len(comments)}",
                    callback_data="comments",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Мероприятия: {len(events)}", callback_data="events"
                )
            ],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")],
        ]
    )
    await message.answer(f"Ваша роль: {status_text}", reply_markup=keyboard)


def compare_times(date_str: str) -> str:
    def plural_form(n: int, forms: tuple[str, str, str]) -> str:
        n = abs(n) % 100
        n1 = n % 10
        if 11 <= n <= 14:
            return forms[2]
        return forms[0] if n1 == 1 else forms[1] if 2 <= n1 <= 4 else forms[2]

    year, month, day = map(int, date_str.split("-"))
    saved_date = date(year, month, day)
    current_date = date.today()

    if saved_date == current_date:
        return "Вы зарегистрировались сегодня"

    delta_days = abs((current_date - saved_date).days)

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

    return f"Вы с нами уже {' '.join(parts)}"


async def show_more_items(message: Message, state: FSMContext):
    data = await state.get_data()

    # Получаем конфигурацию из состояния
    paginator_type = data.get("paginator_type")
    config = PAGINATOR_CONFIG.get(paginator_type, {})

    # Параметры пагинации
    all_items: List[Any] = data.get("paginator_items", [])
    offset: int = data.get("paginator_offset", 0)
    batch_size: int = config.get("batch_size", 5)
    format_func: Callable = config.get("format_func", str)
    item_name: str = config.get("item_name", "элементов")

    # Получаем текущую порцию данных
    items_batch = all_items[offset : offset + batch_size]

    # Отправляем элементы
    for item in items_batch:
        text = format_func(item)
        await message.answer(
            text,
            parse_mode="MARKDOWN",
            reply_markup=(
                ReplyKeyboardRemove() if offset + batch_size >= len(all_items) else None
            ),
        )

    # Обновляем offset
    new_offset = offset + batch_size
    await state.update_data(paginator_offset=new_offset)

    # Формируем сообщение о статусе
    if new_offset < len(all_items):
        status_text = f"Показано {min(new_offset, len(all_items))} из {len(all_items)} {item_name}"
        more_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Показать еще")],
                [KeyboardButton(text="Назад")],
            ],
            resize_keyboard=True,
        )
        await message.answer(status_text, reply_markup=more_keyboard)
    else:
        await message.answer(f"Больше {item_name} нет", reply_markup=back_reply)


@router.message(
    F.text == "Показать еще",
    StateFilter(
        Step.rating_show, Step.comment_show, Step.visits_show, Step.events_show
    ),
)
async def load_more_items(message: Message, state: FSMContext):
    await show_more_items(message, state)


@router.message(F.text == "👤 Профиль")
async def profile(message: Message, state: FSMContext):
    await state.set_state(Step.profile_menu)
    await message.answer(
        "Загрузка вашего профиля 🌐", reply_markup=ReplyKeyboardRemove()
    )
    user_id = message.from_user.id
    await profile_keyboard(user_id, message, state)


@router.callback_query(F.data == "back_to_menu")
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


@router.callback_query(F.data == "visits")
async def show_visits(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    all_comments = data.get("all_comments")
    if all_comments:
        await callback.message.delete()
        await state.update_data(
            paginator_items=all_comments,
            paginator_type="just_visits",
            paginator_offset=0,
        )
        await state.set_state(Step.visits_show)
        await show_more_items(callback.message, state)
    else:
        await callback.answer("Вы не посетили ни одного места", show_alert=True)


@router.callback_query(F.data == "ratings")
async def show_ratings(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ratings = data.get("ratings")
    if ratings:
        await callback.message.delete()
        await state.update_data(
            paginator_items=ratings, paginator_type="ratings", paginator_offset=0
        )
        await state.set_state(Step.rating_show)
        await show_more_items(callback.message, state)
    else:
        await callback.answer("Вы не оценили ни одного места", show_alert=True)


@router.callback_query(F.data == "comments")
async def show_comments(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    comments = data.get("comments")
    if comments:
        await callback.message.delete()
        await state.update_data(
            paginator_items=comments, paginator_type="comments", paginator_offset=0
        )
        await state.set_state(Step.comment_show)
        await show_more_items(callback.message, state)
    else:
        await callback.answer("Вы не написали ни одного комментария", show_alert=True)


@router.callback_query(F.data == "events")
async def show_events(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    events = data.get("events")
    if events:
        await callback.message.delete()
        await state.update_data(
            paginator_items=events, paginator_type="events", paginator_offset=0
        )
        await state.set_state(Step.events_show)
        await show_more_items(callback.message, state)
    else:
        await callback.answer("Вы не посетили ни одного мероприятия", show_alert=True)


@router.message(
    StateFilter(
        Step.rating_show, Step.comment_show, Step.visits_show, Step.events_show
    ),
    F.text == "Назад",
)
async def profile(message: Message, state: FSMContext):
    await state.set_state(Step.profile_menu)
    await message.answer(
        "Возвращаемся к меню профиля 🌐", reply_markup=ReplyKeyboardRemove()
    )
    user_id = message.from_user.id
    await profile_keyboard(user_id, message, state)
