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
from typing import List
from dataclasses import dataclass

from .main_menu import return_to_user_menu, pretty_date
from database.requests import (
    get_user,
    get_comments,
    get_visits,
    get_place
)
from database.models import (
    Place,
    Comment,
    VisitedEvents
)
from roles.roles_main import (
    admin_check,
    get_user_status_text,
    owner_check
)

router = Router()



@dataclass
class PaginationData:
    items: List
    current_page: int = 0
    page_size: int = 5

class Step(StatesGroup):
    profile_menu = State()
    rating_show = State()
    comment_show = State()
    places_show = State()
    events_show = State()

# функции для пагинации
async def show_paginated_items(
    callback: CallbackQuery, 
    state: FSMContext, 
    items: List, 
    state_name: str,
    item_formatter: callable,
    empty_message: str
):
    if not items:
        await callback.answer(empty_message, show_alert=True)
        return
    
    data = await state.get_data()
    pagination_key = f"{state_name}_pagination"
    
    if pagination_key not in data:
        pagination = PaginationData(items=items)
    else:
        pagination = PaginationData(**data[pagination_key])
        pagination.items = items  # Обновляем список элементов
    
    start = pagination.current_page * pagination.page_size
    end = start + pagination.page_size
    page_items = pagination.items[start:end]
    
    if not page_items and pagination.current_page > 0:
        pagination.current_page = 0
        start = 0
        end = pagination.page_size
        page_items = pagination.items[start:end]
    
    message_text = "\n\n".join([item_formatter(item) for item in page_items])
    total_pages = (len(pagination.items) + pagination.page_size - 1) // pagination.page_size
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    if len(pagination.items) > pagination.page_size:
        row = []
        if pagination.current_page > 0:
            row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"prev_{state_name}"))
        
        row.append(InlineKeyboardButton(
            text=f"{pagination.current_page + 1}/{total_pages}", 
            callback_data="page_info"
        ))
        
        if end < len(pagination.items):
            row.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"next_{state_name}"))
        
        keyboard.inline_keyboard.append(row)
    
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад в профиль", callback_data="back_to_profile")])
    
    await state.update_data({pagination_key: pagination.__dict__})
    await state.set_state(getattr(Step, f"{state_name}_show"))
    
    try:
        await callback.message.edit_text(message_text, reply_markup=keyboard)
    except:
        await callback.message.answer(message_text, reply_markup=keyboard)

# Форматтеры для разных типов элементов
def format_place(place: Place) -> str:
    return (
        f"📍{place.name}\n"
        f"📌 Адрес: {place.address}"
    )

def format_comment(comment: Comment) -> str:
    return (
        f"📝 Комментарий\n"
        f"⭐ Оценка: {'★' * comment.commentator_rating}{'☆' * (5 - comment.commentator_rating)}\n"
        f"💬 Текст: {comment.comment_text}"
    )

def format_event(event: VisitedEvents) -> str:
    return (
        f"🎫 Посещённое мероприятие\n"
        f"📝 Отзыв: {event.review_text}"
    )


async def profile_keyboard(tg_id: int, message: Message, state: FSMContext):
    user_info = await get_user(tg_id)
    reg_date = user_info.regist_date
    status_text = await get_user_status_text(tg_id)
    all_comments = await get_comments(None, tg_id)
    await state.update_data(all_comments=all_comments)
    non_zero_ratings = [c.commentator_rating for c in all_comments if c.commentator_rating > 0]
    await state.update_data(non_zero_ratings=non_zero_ratings)
    non_zero_comments = [c.commentator_rating for c in all_comments if c.comment_text != '']
    await state.update_data(non_zero_comments=non_zero_comments)
    events = await get_visits(tg_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Дата регистрации: {await pretty_date(str(reg_date))}",
                    callback_data="reg_date",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Посещённые места: {len({c.place_id for c in all_comments})}", 
                    callback_data="places"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Оценки: {len(non_zero_ratings)}", 
                    callback_data="ratings"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Комментарии: {len(non_zero_comments)}", 
                    callback_data="comments"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Мероприятия: {len(events)}", 
                    callback_data="events"
                )
            ],
            [InlineKeyboardButton(text="Назад", callback_data="back")],
        ]
    )
    await message.answer(f"Меню профиля\nВаша роль: {status_text}", reply_markup=keyboard)

# Обработчики кнопок
@router.callback_query(F.data == "places")
async def show_places(callback: CallbackQuery, state: FSMContext):
    comments = await get_comments(commentator_tg_id=callback.from_user.id)
    place_ids = {comment.place_id for comment in comments}
    places = []
    for place_id in place_ids:
        place = await get_place(place_id=place_id)
        if place:
            places.append(place)
    
    await show_paginated_items(
        callback, 
        state, 
        places, 
        "places",
        format_place,
        "Вы ещё не посещали мест"
    )


@router.callback_query(F.data == "visits")
async def show_ratings(callback: CallbackQuery, state: FSMContext):
    data = state.get_data()
    # all_comments = data.get("all_comments")
    places_with_ratings = data.get('non_zero_ratings')
    await show_paginated_items(
        callback, 
        state, 
        places_with_ratings, 
        "rating",
        format_place,  # Используем тот же форматтер, что и для мест
        "Вы ещё не оценивали места"
    )

@router.callback_query(F.data == "reviews")
async def show_comments(callback: CallbackQuery, state: FSMContext):
    comments = await get_comments(commentator_tg_id=callback.from_user.id)
    non_empty_comments = [c for c in comments if c.comment_text]
    await show_paginated_items(
        callback, 
        state, 
        non_empty_comments, 
        "comment",
        format_comment,
        "У вас ещё нет комментариев"
    )

@router.callback_query(F.data == "events")
async def show_events(callback: CallbackQuery, state: FSMContext):
    events = await get_visits(callback.from_user.id)
    await show_paginated_items(
        callback, 
        state, 
        events, 
        "events",
        format_event,
        "Вы ещё не посещали мероприятий"
    )

# Обработчики пагинации
@router.callback_query(F.data.startswith("prev_"))
async def prev_page(callback: CallbackQuery, state: FSMContext):
    state_name = callback.data.split("_")[1]
    data = await state.get_data()
    pagination_key = f"{state_name}_pagination"
    
    if pagination_key in data:
        pagination = PaginationData(**data[pagination_key])
        pagination.current_page -= 1
        await state.update_data({pagination_key: pagination.__dict__})
        
        # Вызываем соответствующий обработчик для обновления данных
        if state_name == "places":
            await show_places(callback, state)
        elif state_name == "rating":
            await show_ratings(callback, state)
        elif state_name == "comment":
            await show_comments(callback, state)
        elif state_name == "events":
            await show_events(callback, state)


@router.callback_query(F.data.startswith("next_"))
async def next_page(callback: CallbackQuery, state: FSMContext):
    state_name = callback.data.split("_")[1]
    data = await state.get_data()
    pagination_key = f"{state_name}_pagination"
    
    if pagination_key in data:
        pagination = PaginationData(**data[pagination_key])
        pagination.current_page += 1
        await state.update_data({pagination_key: pagination.__dict__})
        
        # Вызываем соответствующий обработчик для обновления данных
        if state_name == "places":
            await show_places(callback, state)
        elif state_name == "rating":
            await show_ratings(callback, state)
        elif state_name == "comment":
            await show_comments(callback, state)
        elif state_name == "events":
            await show_events(callback, state)


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


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(Step.profile_menu)
    await profile_keyboard(callback.from_user.id, callback.message, state)


@router.message(F.text == "👤 Профиль")
async def profile(message: Message, state: FSMContext):
    await state.set_state(Step.profile_menu)
    await message.answer(
        "Загрузка вашего профиля 🌐", reply_markup=ReplyKeyboardRemove()
    )
    user_id = message.from_user.id
    await profile_keyboard(user_id, message, state)


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