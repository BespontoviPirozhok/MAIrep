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

from .search_menu import place_view_reply, place_view_reply_visited, get_place_info_text

router = Router()


class Step(StatesGroup):  # состояния
    place_view = State()  # просмотр информации о месте
    feedback = State()  # оставляем 1-5 звезд
    waiting_comment = State()
    confirm_feedback = State()


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
    await state.set_state(Step.feedback)
    await message.answer(
        "Пожалуйста, оцените данное место", reply_markup=ReplyKeyboardRemove()
    )
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
        get_place_info_text(place), reply_markup=place_view_reply
    )
    await callback.answer()


@router.callback_query(F.data.startswith("star_"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])

    await state.update_data(user_rating=rating)

    # Исправленная клавиатура
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [  # Каждый ряд - отдельный список
                InlineKeyboardButton(text="Пропустить", callback_data="skip_comment")
            ]
        ]
    )

    await callback.message.edit_text(
        f"Спасибо за оценку {rating} ⭐!\nХотите добавить комментарий? Просто напишите его ниже!",
        reply_markup=keyboard,  # Используем исправленную клавиатуру
    )
    await callback.answer()


# Обработчик пропуска комментария
@router.callback_query(F.data == "skip_comment", Step.waiting_comment)
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await show_confirmation(callback.message, state)
    await callback.answer()


# Обработчик текстового комментария
@router.message(Step.waiting_comment, F.text)
async def handle_comment(message: Message, state: FSMContext):
    # Сохраняем комментарий
    await state.update_data(user_comment=message.text)
    await show_confirmation(message, state)


async def show_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    rating = data["user_rating"]
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


# Обработчик подтверждения
@router.callback_query(F.data == "confirm_feedback", Step.confirm_feedback)
async def confirm_feedback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Здесь сохраняем в базу данных
    # await save_to_database(callback.from_user.id, data)

    # Меняем кнопку и возвращаем к месту
    await callback.message.edit_text("✅ Отзыв успешно сохранен!")
    await return_to_place_view(callback.message, state)
    await callback.answer()


# Обработчик отмены
@router.callback_query(F.data == "cancel_feedback", Step.confirm_feedback)
async def cancel_feedback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Отзыв не был сохранен")
    await return_to_place_view(callback.message, state)
    await callback.answer()


async def return_to_place_view(message: Message, state: FSMContext):
    await state.clear()
    # Здесь должна быть логика возврата к просмотру места
    # с обновленной кнопкой "Место посещено"
    # Например:
    data = await state.get_data()
    place = data.get("current_place")
    await message.answer(
        f"Возвращаемся к месту {place}...",
        reply_markup=place_view_reply_visited,  # Новая клавиатура с измененной кнопкой
    )
