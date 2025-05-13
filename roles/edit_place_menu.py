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
from roles.roles_main import user_check, manager_check
from database.requests import add_comment, get_comments, delete_comment, get_place
from keyboard_user.search_menu import place_view_smart_reply, get_place_info_text


router = Router()


class Step(StatesGroup):  # состояния
    place_view = State()
    edit_place = State()
    edit_place_confirm = State()


async def get_smart_desc_edit_menu(
    message: Message, place_name: str, place_description: str
):
    """
    Отправляет интеллектуальное меню редактирования описания места
    :param message: Объект сообщения aiogram
    :param place_name: Название места (строка)
    :param place_description: Текущее описание места (строка)
    """
    # Определяем текст сообщения и кнопки
    if not place_description:
        main_text = f"📭 У места *{place_name}* нет описания. Чтобы его добавить, просто введите текст ниже"
        button_text = "Оставить место без описания"
    else:
        main_text = (
            f"📄 Текущее описание *{place_name}* (для копирования нажмите на него):\n"
            f"\n`{place_description}`\n\n\n"
            "✍️ Введите новый текст описания или отредактируйте текущий:"
        )
        button_text = "Оставить прежнее описание"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button_text, callback_data="skip_edit_description"
                )
            ]
        ]
    )

    # Отправляем сообщение
    await message.answer(
        main_text,
        reply_markup=keyboard,
        parse_mode="MARKDOWN",
    )


async def get_category_keyboard(description: str) -> InlineKeyboardMarkup:
    if len(description) > 0:
        button_text = "Оставить прежнюю категорию"
    else:
        button_text = "Не добавлять категорию"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button_text, callback_data="skip_edit_description"
                )
            ]
        ]
    )


@router.message(Step.place_view, F.text == "✏️ Изменить информацию о месте")
async def edit_description(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    if await manager_check(tg_id):
        await state.set_state(Step.edit_place)
        await message.answer(
            "Запуск редактора информации о месте", reply_markup=ReplyKeyboardRemove()
        )
        data = await state.get_data()
        place_id = data.get("place_id")
        places_search_result = await get_place(place_id=place_id)
        place_name = places_search_result.name
        place_description = places_search_result.description
        await get_smart_desc_edit_menu(message, place_name, place_description)
