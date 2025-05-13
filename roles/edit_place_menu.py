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
    edit_category = State()
    edit_description = State()
    edit_place_confirm = State()


async def get_smart_desc_edit_menu(
    message: Message, place_name: str, place_description: str
):
    # Определяем текст сообщения и кнопки
    if not place_description:
        main_text = f"📭 У места *{place_name}* нет описания. Чтобы его добавить, просто введите текст ниже"
        button_text = "Оставить место без описания"
    else:
        main_text = (
            f"📄 Текущее описание *{place_name}* (для копирования нажмите на него):\n"
            f"\n`{place_description}`\n\n"
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


async def get_smart_category_edit_menu(
    message: Message, place_name: str, place_category: str
):
    # Определяем текст сообщения и кнопки
    if not place_category:
        main_text = f"📭 У места *{place_name}* нет категории. Чтобы добавить ее, просто введите текст ниже"
        button_text = "Оставить место без категории"
    else:
        main_text = (
            f"📄 Текущая категория места *{place_name}* (для копирования нажмите на него):\n"
            f"\n`{place_category}`\n\n"
            "✍️ Введите новую категорию или отредактируйте текущую:"
        )
        button_text = "Оставить прежнюю категорию"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button_text, callback_data="skip_edit_category"
                )
            ],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_place_view")],
        ],
    )

    # Отправляем сообщение
    await message.answer(
        main_text,
        reply_markup=keyboard,
        parse_mode="MARKDOWN",
    )


@router.message(Step.place_view, F.text == "✏️ Изменить информацию о месте")
async def edit_description(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    if await manager_check(tg_id):
        await state.set_state(Step.edit_category)
        await message.answer(
            "Запуск редактора информации о месте", reply_markup=ReplyKeyboardRemove()
        )
        data = await state.get_data()
        place_id = data.get("place_id")
        places_search_result = await get_place(place_id=place_id)
        place_name = places_search_result.name
        place_category = places_search_result.category
        await get_smart_category_edit_menu(message, place_name, place_category)
    else:
        data = await state.get_data()
        place_id = data.get("place_id")
        await message.answer(
            "Вы не имеете права редактировать информацию о месте",
            reply_markup=await place_view_smart_reply(tg_id, place_id),
        )


@router.callback_query(Step.edit_category, F.data == "back_to_place_view")
async def back_from_feedback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    place_id = data.get("place_id")
    await state.set_state(Step.place_view)
    await callback.message.delete()

    place_info = await get_place_info_text(place_id=place_id)

    await callback.message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(callback.from_user.id, place_id),
        parse_mode="MARKDOWN",
    )
    await callback.answer()


@router.message(Step.edit_category)
async def feedback_full_confirm(message: Message, state: FSMContext):
    category = message.text
    print(category)
    await state.set_state(Step.edit_description)
    await state.update_data(category=category)
    data = await state.get_data()
    place_id = data.get("place_id")
    places_search_result = await get_place(place_id=place_id)
    place_name = places_search_result.name
    place_description = places_search_result.description
    await get_smart_desc_edit_menu(message, place_name, place_description)


@router.message(Step.edit_category, F.data == "skip_edit_category")
async def feedback_full_confirm(message: Message, state: FSMContext):
    await state.set_state(Step.edit_description)
    data = await state.get_data()
    place_id = data.get("place_id")
    places_search_result = await get_place(place_id=place_id)
    place_name = places_search_result.name
    place_description = places_search_result.description
    await get_smart_desc_edit_menu(message, place_name, place_description)
