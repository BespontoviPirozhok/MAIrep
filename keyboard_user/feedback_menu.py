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
from datetime import date
from roles.roles_main import user_check
from database.requests import add_comment, get_comments, delete_comment, get_place
from .search_menu import place_view_smart_reply, get_place_info_text


router = Router()


class Step(StatesGroup):  # состояния
    place_view = State()  # просмотр информации о месте
    take_rating = State()  # оставляем 1-5 звезд
    take_comment = State()  # оставляем комментарий
    feedback_confirm = State()  # подтверждение отзыва


feedback_full_confirfm_text = """{username}
{pretty_rating} {comment_date}
{comment_text}"""

feedback_rating_confirfm_text = """{username}
{pretty_rating}"""

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

feedback_edit_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✏️ Редактировать")],
        [KeyboardButton(text="❌ Удалить")],
        [KeyboardButton(text="Назад")],
    ],
    input_field_placeholder="Выберите пункт",
    resize_keyboard=True,
)

feedback_visited_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✏️ Оставить отзыв")],
        [KeyboardButton(text="❌ Удалить отметку о посещении")],
        [KeyboardButton(text="Назад")],
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
    place_id = data.get("place_id")
    await state.set_state(Step.place_view)
    await callback.message.delete()

    place_info = await get_place_info_text(place_id=place_id)

    await callback.message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(callback.from_user.id, place_id),
    )
    await callback.answer()


@router.callback_query(Step.take_rating, F.data == "no_review_visit")
async def no_review_visit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    place_id = data.get("place_id")
    places_search_result = await get_place(place_id=place_id)
    current_place_name = places_search_result.name
    tg_id = callback.from_user.id
    await delete_comment(commentator_tg_id=tg_id, place_id=place_id)
    await get_place
    await add_comment(
        commentator_tg_id=tg_id,
        place_name=current_place_name,
        text="",
        rating="",
    )
    await callback.message.answer(f"Вы посетили {current_place_name} без оценки")
    await state.set_state(Step.place_view)
    await callback.message.delete()
    place_info = await get_place_info_text(place_id=place_id)
    await callback.message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(callback.from_user.id, place_id),
    )
    await callback.answer()


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
    await state.set_state(Step.feedback_confirm)
    data = await state.get_data()
    place_id = data.get("place_id")
    places_search_result = await get_place(place_id=place_id)
    current_place_name = places_search_result.name
    await state.update_data(comment_text="")
    await callback.message.answer(
        text=f"Ваша оценка места {current_place_name}:\n{"⭐" * data["user_rating"]}",
        reply_markup=feedback_confirm_reply,
    )
    await callback.answer()


@router.message(Step.take_comment)
async def feedback_full_confirm(message: Message, state: FSMContext):
    await state.set_state(Step.feedback_confirm)
    comment_text_input = message.text
    await state.update_data(comment_text=comment_text_input)
    data = await state.get_data()
    place_id = data.get("place_id")
    places_search_result = await get_place(place_id=place_id)
    current_place_name = places_search_result.name

    full_review = feedback_full_confirfm_text.format(
        username=message.from_user.first_name,
        pretty_rating="⭐" * data["user_rating"],
        comment_date=date.today().strftime("%d.%m.%Y"),
        comment_text=comment_text_input,
    )
    await state.update_data(comment_text=full_review)
    await message.answer(
        text=f"Ваш отзыв о месте {current_place_name} будет выглядеть так:\n\n{full_review}",
        reply_markup=feedback_confirm_reply,
    )


@router.message(
    Step.feedback_confirm, F.text.in_(["✏️ Оставить отзыв", "✏️ Редактировать"])
)
async def rating(message: Message, state: FSMContext):
    await state.set_state(Step.take_rating)
    await message.answer(
        "Запускаем диалоговое окно оценки...", reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Насколько вам понравилось место от 1 до 5?:",
        reply_markup=feedback_rating_inline,
    )
    await state.update_data(user_rating=None, comment_text=None)


@router.message(Step.feedback_confirm, F.text.in_(["❌ Отмена", "Назад"]))
async def back_from_feedback(message: Message, state: FSMContext):
    data = await state.get_data()
    place_id = data.get("place_id")
    await state.set_state(Step.place_view)
    place_info = await get_place_info_text(place_id)
    await message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(message.from_user.id, place_id),
    )
    await state.update_data(user_rating=None, comment_text=None)


@router.message(Step.feedback_confirm, F.text == "✅ Подтвердить")
async def confirm_feedback(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = message.from_user.id
    place_id = data.get("place_id")
    user_rating = data.get("user_rating")
    comment_text = data.get("comment_text")
    await delete_comment(commentator_tg_id=tg_id, place_id=place_id)

    await add_comment(
        commentator_tg_id=tg_id,
        place_id=place_id,
        text=comment_text,
        rating=user_rating,
    )
    await message.answer("✅ Отзыв успешно сохранен!")
    place_info = await get_place_info_text(place_id)
    await message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(message.from_user.id, place_id),
    )
    await state.set_state(Step.place_view)
    await state.update_data(user_rating=None, comment_text=None)


@router.message(Step.place_view, F.text == "Место уже посещено ✅")
async def show_existing_comment(message: Message, state: FSMContext):
    await state.set_state(Step.feedback_confirm)
    data = await state.get_data()
    place_id = data.get("place_id")
    places_search_result = await get_place(place_id=place_id)
    current_place_name = places_search_result.name
    tg_id = message.from_user.id

    comments = await get_comments(place_id=place_id, commentator_tg_id=tg_id)
    comment = comments[0]
    if len(comment.comment_text) == 0 and len(str(comment.commentator_rating)) == 0:
        text = f"Вы отметили место {current_place_name} как посещенное без отзыва. Вы можете удалить отметку о посещении или оставить отзыв"
        await message.answer(text, reply_markup=feedback_visited_reply)
    elif len(comment.comment_text) == 0:
        text = (
            f"Ваша оценка к месту {current_place_name}:\n\n"
            f"{comment.commentator_rating * "⭐"}"
        )
        await message.answer(text, reply_markup=feedback_edit_reply)
    else:
        text = (
            f"Ваш существующий отзыв к месту {current_place_name}:\n\n"
            f"{comment.comment_text}"
        )
        await message.answer(text, reply_markup=feedback_edit_reply)


@router.message(
    Step.feedback_confirm, F.text.in_(["❌ Удалить", "❌ Удалить отметку о посещении"])
)
async def delete_review(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Step.place_view)
    place_id = data.get("place_id")
    place_info = await get_place_info_text(place_id)
    await delete_comment(
        commentator_tg_id=message.from_user.id,
        place_id=place_id,
    )
    await message.answer("Ваш отзыв успешно удален")
    await message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(message.from_user.id, place_id),
    )
    await state.update_data(user_rating=None, comment_text=None)


# "✏️ Изменить описание места"
