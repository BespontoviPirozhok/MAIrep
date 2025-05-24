from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram import Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from user_interface.ui_main import (
    event_searching,
    cities_kb_def,
    return_to_user_menu,
)


from database.requests import add_event, get_events, delete_event
from map_and_events.kudago import search_kudago, full_event_data

router = Router()


class Step(StatesGroup):
    event_search = State()
    event_view = State()


async def event_view_smart_reply(tg_id: int, kudago_id: int):
    top_button_text = "Отметить как посещенное"
    if await get_events(tg_id=tg_id, kudago_id=kudago_id):
        top_button_text = "Уже посещено ✅"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=top_button_text)],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выберите пункт",
    )


async def events_search_view(events_list: list, message: Message, state: FSMContext):
    tg_id = message.from_user.id

    choose_back_reply = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Выбрать другой город")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

    if not events_list:
        await message.delete()
        return

    for index, event in enumerate(events_list, start=1):
        emoji = ""
        if await get_events(tg_id, event.kudago_id):
            emoji = " ✅ "
        events_list_inline = InlineKeyboardBuilder()
        events_list_inline.add(
            InlineKeyboardButton(
                text="Подробнее", callback_data=f"event_select_{index}"
            )
        )
        await message.answer(
            text=f"{emoji}*{event.event_name}*\nВремя: {event.event_time}",
            reply_markup=(events_list_inline.as_markup()),
            parse_mode="MARKDOWN",
        )

    await message.answer(
        """В списке нет нужного мероприятия? Попробуйте изменить свой запрос.\nЕсли ваше сообщение исчезло, значит по вашему запросу ничего не нашлось.""",
        reply_markup=choose_back_reply,
    )


async def get_event_info_text(event_short_data: int) -> str:
    full_data = await full_event_data(event_short_data)
    return f"""
*{full_data.event_name}*

Время: {full_data.event_time}
            
Адрес: {full_data.event_address}
            
Описание: {full_data.description}"""


@router.message(F.text == "🏝️ Поиск мероприятий")
@router.message(Step.event_search, F.text == "Выбрать другой город")
async def start_event_searching(message: Message, state: FSMContext):
    await event_searching(message, state)


@router.callback_query(Step.event_search, F.data.startswith("city_"))
async def handle_event_selection(callback: CallbackQuery, state: FSMContext):
    city_rus = callback.data.split("_")[1]
    city_eng = callback.data.split("_")[2]
    data = await state.get_data()
    data_city_eng = data.get("city_eng", "msk")
    if data_city_eng == city_eng:
        await callback.answer()
        return

    await state.update_data(city_rus=city_rus)
    await state.update_data(city_eng=city_eng)

    await callback.message.edit_text(
        f"Выберите город, в котором хотите искать мероприятия. Выбранный город - *{city_rus}*",
        reply_markup=await cities_kb_def(state),
        parse_mode="Markdown",
    )


@router.message(Step.event_search, F.text == "Назад")
async def exit(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu("Операция отменена", message)


@router.message(Step.event_search)
async def event_search_input(message: Message, state: FSMContext):
    data = await state.get_data()
    city_eng = data.get("city_eng", "msk")
    search_events_list = await search_kudago(message.text, city_eng)
    await state.update_data(events_list=search_events_list)
    await events_search_view(search_events_list, message, state)


@router.callback_query(Step.event_search, F.data.startswith("event_select_"))
async def handle_event_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Step.event_view)

    tg_id = callback.from_user.id

    event_index = int(callback.data.split("_")[-1]) - 1
    data = await state.get_data()
    events_list = data.get("events_list")
    current_event = events_list[event_index]
    await state.update_data(current_event=current_event)
    kudago_id = current_event.kudago_id
    await state.update_data(kudago_id=kudago_id)

    event_info = await get_event_info_text(event_short_data=current_event)
    await callback.message.answer(
        event_info,
        reply_markup=await event_view_smart_reply(tg_id=tg_id, kudago_id=kudago_id),
        parse_mode="MARKDOWN",
    )
    await callback.answer()


@router.message(Step.event_view, F.text == "Назад")
async def back_to_event_search(message: Message, state: FSMContext):
    await state.set_state(Step.event_search)
    data = await state.get_data()
    search_events_list = data.get("events_list")
    await state.update_data(current_event=None)
    await events_search_view(search_events_list, message, state)


@router.message(Step.event_view, F.text == "Уже посещено ✅")
async def delete_visit_mark(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    data = await state.get_data()
    current_event = data.get("current_event")
    kudago_id = current_event.kudago_id

    await delete_event(tg_id, kudago_id)
    await message.answer(
        "Отметка о посещении удалена",
        reply_markup=await event_view_smart_reply(tg_id, kudago_id),
    )


@router.message(Step.event_view, F.text == "Отметить как посещенное")
async def delete_visit_mark(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    data = await state.get_data()
    current_event = data.get("current_event")
    kudago_id = current_event.kudago_id

    await add_event(
        tg_id,
        kudago_id,
        current_event.event_name,
        current_event.event_time,
    )
    await message.answer(
        "Вы посетили данное мероприятие",
        reply_markup=await event_view_smart_reply(tg_id, kudago_id),
    )
