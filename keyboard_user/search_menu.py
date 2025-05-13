from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardRemove,
)
from aiogram import Bot, Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboard_user.main_menu import return_to_user_menu, back_reply

from roles.roles_main import user_check, manager_check

from database.requests import get_place, add_place, get_comments

from map_and_events.map import map_search

router = Router()


class Step(StatesGroup):  # состояния
    search_input = State()  # поисковая строка и показ мест
    place_view = State()  # просмотр информации о месте


async def place_view_smart_reply(tg_id: int, place_id: str):
    top_button_text = "Отметить это место как посещенное"
    comment_exists = len(await get_comments(commentator_tg_id=tg_id, place_id=place_id))
    if comment_exists != 0:
        top_button_text = "Место уже посещено ✅"
    keyboard = []
    keyboard.append([KeyboardButton(text=top_button_text)])
    if await manager_check(tg_id):
        keyboard.append([KeyboardButton(text="✏️ Изменить описание места")])

    keyboard.extend(
        [
            [KeyboardButton(text="Посмотреть комментарии")],
            [KeyboardButton(text="Назад")],
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


async def places_search_view(places_list: list, message: Message, state: FSMContext):
    user = await user_check(message.from_user.id)
    message_ids = []  # Список для хранения ID сообщений

    if not places_list:
        sent_message = await message.answer(
            text="По вашему запросу ничего не нашлось...", reply_markup=back_reply
        )
        message_ids.append(sent_message.message_id)
        await state.update_data(search_message_ids=message_ids)
        return

    for index, place in enumerate(places_list, start=1):
        # Инициализируем переменные для каждого места
        emoji = "🌐 "
        button_text = "Добавить место в базу данных"
        ban = ""

        place_in_db = await get_place(name=place.name, address=place.address)
        place_list_inline = InlineKeyboardBuilder()

        if place_in_db:
            button_text = "Показать это место"
            place_id = place_in_db.place_id
            # Проверяем комментарии для текущего места
            if await get_comments(
                commentator_tg_id=message.from_user.id, place_id=place_id
            ):
                emoji = "✅ "
            else:
                emoji = "🌎 "
        else:
            if not user:
                ban = "\n\n❌ Место недоступно ❌"
                emoji = ""  # Сбрасываем эмодзи для неавторизованных

        # Добавляем кнопку только если место есть в БД ИЛИ пользователь авторизован
        if place_in_db or user:
            place_list_inline.add(
                InlineKeyboardButton(
                    text=button_text, callback_data=f"place_select_{index}"
                )
            )

        sent_message = await message.answer(
            text=f"{emoji}{place.pretty_result}{ban}",
            reply_markup=(
                place_list_inline.as_markup() if place_list_inline.buttons else None
            ),
        )
        message_ids.append(sent_message.message_id)

    # Сохраняем ID финального сообщения
    sent_message = await message.answer(
        "В списке нет нужного места? Попробуйте изменить свой запрос.",
        reply_markup=back_reply,
    )
    message_ids.append(sent_message.message_id)

    # Записываем все ID в состояние
    await state.update_data(search_message_ids=message_ids)


async def get_place_info_text(place_id: int) -> str:
    temp_place = await get_place(place_id=place_id)
    return f"""{temp_place.name}
            
Категория: {temp_place.category}
            
Адрес: {temp_place.address}
            
Описание: {temp_place.description}"""


@router.message(F.text == "🔍 Поиск мест")
async def search(message: Message, state: FSMContext):
    await state.set_state(Step.search_input)
    await message.answer(
        """
Рядом названием каждого места есть специальный значок:
✅ - Вы уже посетили данное место;
🌎 - Место есть в базе данных, возможно у него уже есть оценки и комментарии;
🌐 - Места еще нет в базе данных, но вы можете его туда добавить;
""",
    )
    await message.answer(
        """Введите название места, которое хотите найти
""",
        reply_markup=back_reply,
    )


@router.message(Step.search_input, F.text == "Назад")
async def exit(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu(message.from_user.id, "Вы вернулись в меню", message)


@router.message(Step.search_input)
async def inline_places(message: Message, state: FSMContext):
    search_places_list = await map_search(message.text)
    await state.update_data(places_list=search_places_list)
    await places_search_view(search_places_list, message, state)


@router.callback_query(F.data.startswith("place_select_"))
async def handle_place_selection(
    callback: CallbackQuery, state: FSMContext, bot: Bot  # Добавляем инжекцию бота
):
    await state.set_state(Step.place_view)
    tg_id = callback.from_user.id

    # Удаляем предыдущие сообщения поисковой выдачи
    data = await state.get_data()
    message_ids = data.get("search_message_ids", [])

    # Удаление сообщений
    for msg_id in message_ids:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)

    # Остальная логика обработчика
    place_index = int(callback.data.split("_")[-1]) - 1
    places_list = data.get("places_list")
    current_place = places_list[place_index]

    place_in_db = await get_place(
        name=current_place.name, address=current_place.address
    )

    if not place_in_db:
        await add_place(
            name=current_place.name,
            category=current_place.category,
            address=current_place.address,
        )
        place_in_db = await get_place(
            name=current_place.name, address=current_place.address
        )
        await callback.message.answer(
            f"Место {current_place.name} добавлено в базу данных"
        )

    place_id = place_in_db.place_id
    await state.update_data(place_id=place_id)

    place_info = await get_place_info_text(place_id=place_id)
    await callback.message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(tg_id=tg_id, place_id=place_id),
    )
    #  await callback.answer()


@router.message(Step.place_view, F.text == "Назад")
async def back_to_places_list(message: Message, state: FSMContext):
    await state.set_state(Step.search_input)
    data = await state.get_data()
    places_list = data.get("places_list")
    await places_search_view(places_list, message, state)
    await state.update_data(current_place=None)

    # еще один тест
