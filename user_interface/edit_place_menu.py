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
from roles.roles_main import manager_check
from database.requests import get_place, update_place
from user_interface.search_menu import place_view_smart_reply, get_place_info_text
from user_interface.feedback_menu import feedback_confirm_reply


router = Router()


class Step(StatesGroup):  # состояния
    place_view = State()
    edit_category = State()
    edit_description = State()
    edit_place_confirm = State()


async def custom_place_info(
    place_name: str, place_category: str, place_description: str
) -> str:
    a = "*"
    return f"""Информация о месте после изменений будет выглядеть примерно так:
*{place_name}*
    
Оценка: ?

Категория: {place_category}
            
Адрес: ?
            
Описание: {place_description}

Сводка комментариев: ?

? - Информация недоступна в режиме редактирования
"""


async def get_smart_desc_edit_menu(
    obj,  # Принимаем объект без явного указания типа
    place_name: str,
    place_description: str,
):
    # Определяем текст сообщения и кнопки
    if not place_description:
        main_text = f"📭 У места *{place_name}* нет описания. Чтобы его добавить, просто введите текст ниже"
        button_text = "Оставить место без описания"
    else:
        main_text = (
            f"📄 Текущее описание *{place_name}* (для копирования нажмите на него):\n"
            f"\n`{place_description}`\n\n"
            "Введите новый текст описания или отредактируйте текущий:"
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

    if isinstance(obj, CallbackQuery):
        # Для CallbackQuery: редактируем текущее сообщение
        await obj.message.edit_text(
            main_text, reply_markup=keyboard, parse_mode="MARKDOWN"
        )
        await obj.answer()  # Убираем индикатор загрузки
    elif isinstance(obj, Message):
        # Для Message: отправляем новое сообщение
        await obj.answer(main_text, reply_markup=keyboard, parse_mode="MARKDOWN")


async def get_smart_category_edit_menu(
    message: Message,
    place_name: str,
    place_category: str,
):
    # Определяем текст сообщения и кнопки
    if not place_category:
        main_text = f"📭 У места *{place_name}* нет категории. Чтобы добавить ее, просто введите текст ниже"
        button_text = "Оставить место без категории"
    else:
        main_text = (
            f"📄 Текущая категория места *{place_name}* (для копирования нажмите на него):\n"
            f"\n`{place_category}`\n\n"
            "Введите новую категорию или отредактируйте текущую:"
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


@router.message(Step.place_view, F.text == "Изменить информацию о месте")
async def edit_description(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    if await manager_check(tg_id):
        await state.set_state(Step.edit_category)
        await message.answer(
            "Запуск редактора информации о месте", reply_markup=ReplyKeyboardRemove()
        )
        data = await state.get_data()
        place_id = data.get("place_id")
        place_name = data.get("place_name")
        places_search_result = await get_place(place_id=place_id)
        place_category = places_search_result.category
        place_description = places_search_result.description
        await state.update_data(
            place_description=place_description, place_category=place_category
        )
        await get_smart_category_edit_menu(message, place_name, place_category)
    else:
        data = await state.get_data()
        place_id = data.get("place_id")
        await message.answer(
            "Вы не имеете права редактировать информацию о месте",
            reply_markup=await place_view_smart_reply(tg_id, place_id),
        )


@router.callback_query(Step.edit_category, F.data == "back_to_place_view")
async def back_from_place_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Step.place_view)
    data = await state.get_data()
    place_id = data.get("place_id")
    await callback.message.delete()
    place_info = await get_place_info_text(place_id=place_id)
    await callback.message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(callback.from_user.id, place_id),
        parse_mode="MARKDOWN",
    )
    await callback.answer()


@router.message(Step.edit_category)
async def edit_category(message: Message, state: FSMContext):
    category = message.text
    await state.set_state(Step.edit_description)
    await state.update_data(place_category=category)
    data = await state.get_data()
    place_name = data.get("place_name")
    place_description = data.get("place_description")
    await get_smart_desc_edit_menu(
        obj=message,
        place_name=place_name,
        place_description=place_description,
    )


@router.callback_query(Step.edit_category, F.data == "skip_edit_category")
async def skip_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Step.edit_description)
    data = await state.get_data()
    place_name = data.get("place_name")
    place_description = data.get("place_description")
    await get_smart_desc_edit_menu(
        obj=callback,
        place_name=place_name,
        place_description=place_description,
    )


@router.callback_query(Step.edit_description, F.data == "skip_edit_description")
async def skip_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Step.edit_place_confirm)
    data = await state.get_data()
    place_name = data.get("place_name")
    place_category = data.get("place_category")
    place_description = data.get("place_description")
    await callback.message.answer(
        text=await custom_place_info(place_name, place_category, place_description),
        reply_markup=feedback_confirm_reply,
        parse_mode="MARKDOWN",
    )
    await callback.answer()


@router.message(Step.edit_description)
async def edit_category(message: Message, state: FSMContext):
    await state.set_state(Step.edit_place_confirm)
    new_description = message.text
    await state.update_data(place_description=new_description)
    data = await state.get_data()
    place_name = data.get("place_name")
    place_category = data.get("place_category")
    await message.answer(
        text=await custom_place_info(place_name, place_category, new_description),
        reply_markup=feedback_confirm_reply,
        parse_mode="MARKDOWN",
    )


@router.message(Step.edit_place_confirm, F.text == "❌ Отмена")
async def back_from_feedback(message: Message, state: FSMContext):
    await state.set_state(Step.place_view)
    data = await state.get_data()
    place_id = data.get("place_id")
    place_info = await get_place_info_text(place_id)
    await message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(message.from_user.id, place_id),
        parse_mode="MARKDOWN",
    )
    await state.update_data(place_category=None, place_description=None)


@router.message(Step.edit_place_confirm, F.text == "✏️ Редактировать")
async def edit_place_info_again(message: Message, state: FSMContext):
    await state.set_state(Step.edit_category)
    await message.answer(
        "Запуск редактора информации о месте", reply_markup=ReplyKeyboardRemove()
    )
    data = await state.get_data()
    place_id = data.get("place_id")
    place_name = data.get("place_name")
    places_search_result = await get_place(place_id=place_id)
    place_category = places_search_result.category
    place_description = places_search_result.description
    await state.update_data(
        place_description=place_description, place_category=place_category
    )
    await get_smart_category_edit_menu(message, place_name, place_category)


@router.message(Step.edit_place_confirm, F.text == "✅ Подтвердить")
async def edit_place_confirm(message: Message, state: FSMContext):
    await state.set_state(Step.place_view)

    data = await state.get_data()
    place_id = data.get("place_id")
    places_search_result = await get_place(place_id=place_id)
    place_category_manager = data.get("place_category")
    place_description_manager = data.get("place_description")
    place_category_db = places_search_result.category
    place_description_db = places_search_result.description
    if (
        place_category_manager == place_category_db
        and place_description_manager == place_description_db
    ):
        await message.answer("Вы ничего не изменили, данные остались прежними")
    elif place_category_manager == place_category_db:
        await update_place(place_id=place_id, new_description=place_description_manager)
        await message.answer("Вы изменили описание, категория осталась прежней")
    elif place_description_manager == place_description_db:
        await update_place(place_id=place_id, new_category=place_category_manager)
        await message.answer("Вы изменили категорию, описание осталось прежним")
    else:
        await update_place(
            place_id=place_id,
            new_category=place_category_manager,
            new_description=place_description_manager,
        )
        await message.answer("Вы изменили категорию и описание места")
    await state.update_data(place_description=None, place_category=None)
    place_info = await get_place_info_text(place_id=place_id)

    await message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(message.from_user.id, place_id),
        parse_mode="MARKDOWN",
    )
