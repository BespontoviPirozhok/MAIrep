from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardRemove,
)
from aiogram import Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import date
from database.models import async_sessions, VisitedPlace, Comment
from database.requests import get_place_by_id, get_comments
from .search_menu import place_view_reply, place_view_reply_visited, get_place_info_text
from .main_menu import beautiful_date, back_reply

router = Router()


class Step(StatesGroup):  # состояния
    place_view = State()  # просмотр информации о месте
    сomments_list = State()  # просмотр списка комментариев


@router.message(Step.сomments_list, F.text == "Назад")
async def back_from_comments(message: Message, state: FSMContext):
    await state.set_state(Step.place_view)
    await message.answer(
        "Вы вернулись к информации о месте.", reply_markup=place_view_reply
    )


# @router.message(Step.place_view, F.text == "Посмотреть комментарии") #старая версия показа комментов - показываются сразу все комменты
# async def show_comments(message: Message, state: FSMContext):
#     data = await state.get_data()
#     place = data.get("current_place")
#     await state.set_state(Step.сomments_list)
#     for comment, (comment_user, comment_date) in places_data[place]["comments"].items():
#         await message.answer(
#             f"{comment_user}, {beautiful_date(comment_date)}\n{comment}",
#             reply_markup=back_reply,
#         )


@router.message(Step.place_view, F.text == "Посмотреть комментарии")
async def show_comments(message: Message, state: FSMContext):
    data = await state.get_data()
    place_id = data.get("current_place_id")
    await state.set_state(Step.сomments_list)

    # Получаем и сортируем комментарии
    comments = await get_comments(place_id=place_id)
    all_comments = sorted(
        comments,
        key=lambda x: x.comment_date,  # Сортировка по дате (кортеж (год, месяц, день))
        reverse=True,
    )

    # Инициализируем пагинацию
    await state.update_data(all_comments=all_comments, comment_offset=0)

    # Отправляем первую порцию
    await show_more_comments(message, state)


async def show_more_comments(message: Message, state: FSMContext):
    data = await state.get_data()
    all_comments = data["all_comments"]
    offset = data["comment_offset"]

    # Определяем порцию комментариев
    BATCH_SIZE = 5
    comments_batch = all_comments[offset : offset + BATCH_SIZE]

    # Отправляем комментарии
    for comment, (text, date_tuple) in comments_batch:
        await message.answer(
            f"{text}, {beautiful_date(date_tuple)}\n{comment}",
            reply_markup=(
                ReplyKeyboardRemove()
                if offset + BATCH_SIZE >= len(all_comments)
                else None
            ),
        )

    # Обновляем offset
    new_offset = offset + BATCH_SIZE
    await state.update_data(comment_offset=new_offset)

    # Проверяем остались ли еще комментарии
    if new_offset < len(all_comments):
        # Создаем клавиатуру с кнопкой "Показать еще"
        more_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Показать еще")],
                [KeyboardButton(text="Назад")],
            ],
            resize_keyboard=True,
        )
        await message.answer(
            f"Показано {min(new_offset, len(all_comments))} из {len(all_comments)} комментариев",
            reply_markup=more_keyboard,
        )
    else:
        await message.answer("✅ Больше комментариев нет", reply_markup=back_reply)


@router.message(Step.сomments_list, F.text == "Показать еще")
async def load_more_comments(message: Message, state: FSMContext):
    await show_more_comments(message, state)
