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
from database.requests import get_comments
from roles.roles_main import admin_check
from .search_menu import place_view_smart_reply, get_place_info_text
from .ui_main import back_reply

router = Router()


class Step(StatesGroup):  # состояния
    place_view = State()  # просмотр информации о месте
    сomments_list = State()  # просмотр списка комментариев


@router.message(Step.сomments_list, F.text == "Назад")
async def back_from_comments(message: Message, state: FSMContext):
    await state.set_state(Step.place_view)
    data = await state.get_data()
    place_id = data.get("place_id")
    place_info = await get_place_info_text(place_id=place_id)
    await message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(
            tg_id=message.from_user.id, place_id=place_id
        ),
        parse_mode="MARKDOWN",
    )


@router.message(Step.place_view, F.text == "Посмотреть комментарии")
async def show_comments(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    data = await state.get_data()
    place_id = data.get("place_id")
    await state.set_state(Step.сomments_list)

    # Получаем и сортируем комментарии
    all_comments = (await get_comments(place_id=place_id, filter_empty_text=True))[::-1]

    if not all_comments:
        await message.answer(
            "🧑💻 Никто еще не написал комментарий",
            reply_markup=await place_view_smart_reply(tg_id, place_id),
        )
        await state.set_state(Step.place_view)

    else:
        # Инициализируем пагинацию
        await state.update_data(all_comments=all_comments, comment_offset=0)

        # Отправляем первую порцию
        await show_more_comments(message, state)


async def show_more_comments(message: Message, state: FSMContext):
    data = await state.get_data()
    all_comments = data.get("all_comments")
    offset = data.get("comment_offset")

    # Определяем порцию комментариев
    BATCH_SIZE = 5
    comments_batch = all_comments[offset : offset + BATCH_SIZE]

    # Отправляем комментарии
    for comment in comments_batch:
        await message.answer(
            f"{comment.comment_text}",
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
