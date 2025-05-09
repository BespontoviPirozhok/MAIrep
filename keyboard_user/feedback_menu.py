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
from database.requests import get_place_by_id
from .search_menu import place_view_reply, place_view_reply_visited, get_place_info_text

router = Router()


class Step(StatesGroup):  # состояния
    place_view = State()  # просмотр информации о месте
    take_rating = State()  # оставляем 1-5 звезд
    take_comment = State()  # оставляем комментарий или пропускаем его
    feedback_full_confirfm = State()  # подтверждение звезд + комментария
    feedback_rating_confirm = State()  # подтверждение только звезд


feedback_full_confirfm_text = """Ваш отзыв будет выглядеть так:
    {username}
    {pretty_rating} {comment_date}
    {comment_text}"""

feedback_rating_confirfm_text = """Ваш отзыв будет выглядеть так:
    {username}
    {pretty_rating} {comment_date}"""

feedback_rating_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Отметить как посещенное без оценки", callback_data="no_comments"
            )
        ],
        [
            InlineKeyboardButton(text="1 ⭐", callback_data="star_1"),
            InlineKeyboardButton(text="2 ⭐", callback_data="star_2"),
            InlineKeyboardButton(text="3 ⭐", callback_data="star_3"),
            InlineKeyboardButton(text="4 ⭐", callback_data="star_4"),
            InlineKeyboardButton(text="5 ⭐", callback_data="star_5"),
        ],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_place_view")],
    ],
)


@router.message(Step.place_view, F.text == "Отметить это место как посещенное")
async def rating(message: Message, state: FSMContext):
    # data = await state.get_data()
    # place_name = data.get("current_place_name")

    # # Сохраняем название для использования в следующих состояниях
    # await state.update_data(current_place_name=place_name)
    # await state.set_state(Step.take_rating)
    await message.answer("Достаем звезды с неба 🌃", reply_markup=ReplyKeyboardRemove())
    await message.answer(
        "Насколько вам понравилось место от 1 до 5?:",
        reply_markup=feedback_rating_inline,
    )


@router.callback_query(F.data.startswith("star_"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    # Получаем сохраненное название места
    data = await state.get_data()
    place_name = data.get("current_place_name")

    rating = int(callback.data.split("_")[1])
    await state.update_data(
        user_rating=rating, place_name=place_name  # Сохраняем название
    )
    await state.set_state(Step.take_comment)

    skip_comment = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_comment")]
        ]
    )
    await callback.message.edit_text(
        "Хотите добавить комментарий? Просто напишите его ниже!",
        reply_markup=skip_comment,
    )
    await callback.answer()
