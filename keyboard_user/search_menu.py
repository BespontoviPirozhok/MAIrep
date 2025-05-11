from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardRemove,
)
from aiogram import Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboard_user.main_menu import return_to_user_menu, back_reply

from database.requests import get_place, add_place, get_comments

from map_and_events.map import map_search

router = Router()


class Step(StatesGroup):  # состояния
    search_input = State()  # поисковая строка и показ мест
    place_view = State()  # просмотр информации о месте


async def place_view_smart_reply(tg_id: int, place_id: str):
    comment_exists = len(await get_comments(commentator_tg_id=tg_id, place_id=place_id))
    if comment_exists != 0:
        top_button_text = "Место уже посещено ✅"
    else:
        top_button_text = "Отметить это место как посещенное"

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=top_button_text)],
            [KeyboardButton(text="Посмотреть комментарии")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


async def places_search_view(places_list: list, message: Message, state: FSMContext):

    if not places_list:
        await message.answer(
            text="По вашему запросу ничего не нашлось, введите другой запрос",
            reply_markup=back_reply,
        )
        return

    for index, place in enumerate(places_list, start=1):
        place_list_inline = InlineKeyboardBuilder()
        place_list_inline.add(
            InlineKeyboardButton(
                text=f"Показать это место", callback_data=f"place_select_{index}"
            )
        )
        message.from_user.id
        if await get_place(name=place.name, address=place.address):
            place_id = (
                await get_place(name=place.name, address=place.address)
            ).place_id
            if (
                len(
                    await get_comments(
                        commentator_tg_id=message.from_user.id, place_id=place_id
                    )
                )
                != 0
            ):
                await message.answer(
                    text=f"{place.pretty_result} ✅",
                    reply_markup=place_list_inline.as_markup(),
                )
        else:
            await message.answer(
                text=place.pretty_result,
                reply_markup=place_list_inline.as_markup(),
            )

    await message.answer(
        text="Не нашли то, что искали? Попробуйте ввести запрос по-другому",
        reply_markup=back_reply,
    )


async def get_place_info_text(place_id: int) -> str:
    temp_place = await get_place(place_id=place_id)
    return (
        f"{temp_place.name}\n\n"
        f"Категория: {temp_place.category}\n"
        # f"Средняя оценка: {place.summary_rating}\n\n"
        f"Адрес: {temp_place.address}\n"
        f"Описание: {temp_place.description}\n"
        # f"{place_data['summary']}"
    )


@router.message(F.text == "🔍 Поиск мест")
async def search(message: Message, state: FSMContext):
    await state.set_state(Step.search_input)
    await message.answer(
        """Введите название места, котрое хотите найти:""",
        reply_markup=back_reply,
    )


@router.message(Step.search_input, F.text == "Назад")
async def exit(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu("Вы вернулись в меню", message)


@router.message(Step.search_input)
async def inline_places(message: Message, state: FSMContext):
    search_places_list = await map_search(message.text)
    await state.update_data(places_list=search_places_list)
    await places_search_view(search_places_list, message, state)


@router.callback_query(F.data.startswith("place_select_"))
async def handle_place_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Step.place_view)
    place_index = int(callback.data.split("_")[-1]) - 1
    data = await state.get_data()
    places_list = data.get("places_list")
    current_place = places_list[place_index]
    if not await get_place(name=current_place.name, address=current_place.address):
        await add_place(
            name=current_place.name,
            category=current_place.category,
            address=current_place.address,
        )
    place_id = (
        await get_place(name=current_place.name, address=current_place.address)
    ).place_id
    await state.update_data(place_id=place_id)
    place_info = await get_place_info_text(place_id=place_id)
    await state.set_state(Step.place_view)
    await callback.message.answer(
        place_info,
        reply_markup=await place_view_smart_reply(
            tg_id=callback.from_user.id, place_id=place_id
        ),
    )
    await callback.answer()


@router.message(Step.place_view, F.text == "Назад")
async def back_to_places_list(message: Message, state: FSMContext):
    await state.set_state(Step.search_input)
    data = await state.get_data()
    places_list = data.get("places_list")
    await places_search_view(places_list, message, state)
    await state.update_data(current_place=None)
