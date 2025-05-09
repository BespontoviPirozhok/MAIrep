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
from database.requests import set_user, get_user, add_comment
from .search_menu import place_view_reply, place_view_reply_visited, get_place_info_text

router = Router()


class Step(StatesGroup):  # состояния
    place_view = State()  # просмотр информации о месте
    take_rating = State()  # оставляем 1-5 звезд
    take_comment = State()  # оставляем комментарий или пропускаем его
    feedback_confirfm = State()  # подтверждение отзыва


feedback_full_confirfm_text = """Ваш отзыв о месте {place} будет выглядеть так:

{username}
{pretty_rating} {comment_date}
{comment_text}"""

feedback_rating_confirfm_text = """Ваш отзыв о месте {place} будет выглядеть так:

{username}
{pretty_rating} {comment_date}"""

feedback_rating_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Отметить как посещенное без оценки",
                callback_data="no_review_visit",
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


feedback_confirm_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Подтвердить")],
        [KeyboardButton(text="✏️ Редактировать")],
        [KeyboardButton(text="❌ Отмена")],
    ],
    input_field_placeholder="Выберите пункт",
    resize_keyboard=True,
)


@router.message(Step.place_view, F.text == "Отметить это место как посещенное")
async def rating(message: Message, state: FSMContext):
    await state.set_state(Step.take_rating)
    await message.answer(
        "Загружаем диалоговое окно оценки", reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Насколько вам понравилось место от 1 до 5?:",
        reply_markup=feedback_rating_inline,
    )


@router.callback_query(Step.take_rating, F.data == "back_to_place_view")
async def back_from_feedback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Step.place_view)
    await callback.message.delete()

    place_info = await get_place_info_text(data.get("current_place_name"))

    await callback.message.answer(place_info, reply_markup=place_view_reply)
    await callback.answer()


@router.callback_query(Step.take_rating, F.data == "no_review_visit")
async def no_review_visit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Step.place_view)
    await callback.message.delete()

    place_info = await get_place_info_text(data.get("current_place_name"))

    await callback.message.answer(place_info, reply_markup=place_view_reply_visited)
    await callback.answer()  # тут надо послать данные в бд пользователя, в бд комментов ничего не заносим


@router.callback_query(Step.take_rating, F.data.startswith("star_"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    await state.update_data(user_rating=int(callback.data.split("_")[1]))
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


@router.callback_query(F.data == "skip_comment")
async def feedback_rating_confirm(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Step.feedback_confirfm)
    data = await state.get_data()
    await callback.message.answer(
        text=feedback_rating_confirfm_text.format(
            place=data["current_place_name"],
            username=callback.from_user.first_name,
            pretty_rating="⭐" * data["user_rating"],
            comment_date=date.today().strftime("%d.%m.%Y"),
        ),
        reply_markup=feedback_confirm_reply,
    )
    await callback.answer()


@router.message(Step.take_comment)
async def feedback_full_confirm(message: Message, state: FSMContext):
    await state.set_state(Step.feedback_confirfm)
    comment_text_input = message.text
    await state.update_data(comment_text=comment_text_input)
    data = await state.get_data()
    await message.answer(
        feedback_full_confirfm_text.format(
            place=data["current_place_name"],
            username=message.from_user.first_name,
            pretty_rating="⭐" * data["user_rating"],
            comment_date=date.today().strftime("%d.%m.%Y"),
            comment_text=comment_text_input,
        ),
        reply_markup=feedback_confirm_reply,
    )


@router.message(Step.feedback_confirfm, F.text == "✏️ Редактировать")
async def rating(message: Message, state: FSMContext):
    await state.set_state(Step.take_rating)
    await message.answer(
        "Запускаем диалоговое окно еще раз...", reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Насколько вам понравилось место от 1 до 5?:",
        reply_markup=feedback_rating_inline,
    )
    await state.update_data(user_rating=None, comment_text=None)


@router.message(Step.feedback_confirfm, F.text == "❌ Отмена")
async def back_from_feedback(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Step.place_view)
    place_info = await get_place_info_text(data.get("current_place_name"))
    await message.answer(place_info, reply_markup=place_view_reply)
    await state.update_data(user_rating=None, comment_text=None)


@router.message(Step.feedback_confirfm, F.text == "✅ Подтвердить")
async def confirm_feedback(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = message.from_user.id
    current_place_name = data.get("current_place_name")
    user_rating = data.get("user_rating")
    comment_text = data.get("comment_text")

    await add_comment(
        commentator_tg_id=tg_id,
        place_name=current_place_name,
        text=comment_text,
        rating=user_rating,
    )
    await message.answer("✅ Отзыв успешно сохранен!")
    place_info = await get_place_info_text(current_place_name)
    await message.answer(place_info, reply_markup=place_view_reply_visited)
    await state.set_state(Step.place_view)
    await state.update_data(user_rating=None, comment_text=None)
