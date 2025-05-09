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
    take_comment = State() # оставляем комментарий или пропускаем его
    feedback_full_confirfm = State() #подтверждение звезд + комментария
    feedback_rating_confirm = State() #подтверждение только звезд


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


async def show_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    rating = data.get("user_rating", "не указана")
    comment = data.get("user_comment", "без комментария")

    text = (
        "Проверьте данные:\n"
        f"★ Оценка: {rating}\n"
        f"📝 Комментарий: {comment}\n\n"
        "Подтверждаете сохранение?"
    )

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить", callback_data="confirm_feedback"
                    ),
                    InlineKeyboardButton(
                        text="❌ Отменить", callback_data="cancel_feedback"
                    ),
                ]
            ]
        ),
    )
    await state.set_state(Step.confirm_feedback)


@router.message(Step.place_view, F.text == "Отметить это место как посещенное")
async def rating(message: Message, state: FSMContext):
    await state.update_data(place_id= await)  # Сохраняем place_id
    await state.set_state(Step.take_rating)
    await message.answer(
        "Насколько вам понравилось место от 1 до 5?:",
        reply_markup=feedback_rating_inline,
    )


@router.callback_query(F.data == "back_to_place_view")
async def back_to_place_view_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    place = data.get("current_place")
    await state.set_state(Step.place_view)
    await callback.message.delete()
    await callback.message.answer(
        await get_place_info_text(place), reply_markup=place_view_reply
    )
    await callback.answer()

@router.callback_query(F.data.startswith("star_"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    place_id = await get_place_by_id()
    rating = int(callback.data.split("_")[1])

    await state.update_data(
        user_rating=rating, place_id=place_id  # Используем сохраненный ID
    )
    await state.set_state(Step.waiting_comment)

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










# @router.callback_query(F.data.startswith("star_"))
# async def handle_rating(callback: CallbackQuery, state: FSMContext):
#     data = await state.get_data()
#     place_id = data.get("place_id")  # Получаем place_id из состояния
#     rating = int(callback.data.split("_")[1])

#     await state.update_data(
#         user_rating=rating, place_id=place_id  # Используем сохраненный ID
#     )
#     await state.set_state(Step.waiting_comment)

#     skip_comment = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="Пропустить", callback_data="skip_comment")]
#         ]
#     )
#     await callback.message.edit_text(
#         "Хотите добавить комментарий? Просто напишите его ниже!",
#         reply_markup=skip_comment,
#     )
#     await callback.answer()


# @router.message(Step.waiting_comment, F.text)
# async def handle_comment(message: Message, state: FSMContext):
#     await state.update_data(user_comment=message.text)
#     await show_confirmation(message, state)


# @router.callback_query(F.data == "confirm_feedback", Step.confirm_feedback)
# async def confirm_feedback(callback: CallbackQuery, state: FSMContext):
#     data = await state.get_data()

#     # Все данные хранятся в состоянии и отправляются вместе
#     async with async_sessions() as session:
#         # Сохраняем посещение
#         session.add(
#             VisitedPlace(
#                 user_id=callback.from_user.id,
#                 place_id=data["place_id"],
#                 visit_date=date.today(),
#             )
#         )

#         # Сохраняем комментарий с оценкой
#         session.add(
#             Comment(
#                 user_id=callback.from_user.id,
#                 username=callback.from_user.full_name,
#                 place_id=data["place_id"],
#                 text=data.get("user_comment", "без комментария"),
#                 rating=data["user_rating"],
#                 comment_date=date.today(),
#             )
#         )
#         await session.commit()

#     await callback.message.edit_text("✅ Отзыв успешно сохранен!")
#     await state.clear()
#     await callback.answer()


# @router.callback_query(F.data.startswith("place_"))
# async def show_place(callback: CallbackQuery, state: FSMContext):
#     place_id = int(callback.data.split("_")[1])
#     place = await get_place_by_id(place_id)  # Ваша функция для получения места
#     await state.update_data(current_place=place)  # Сохраняем объект места
#     await state.set_state(Step.place_view)
#     await callback.message.answer(
#         get_place_info_text(place), reply_markup=place_view_reply
#     )
