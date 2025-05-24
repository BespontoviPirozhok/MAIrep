from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, F

from .main_menu import return_to_user_menu
from ai_services.yandex_gpt import chat, recom, describe_places
from database.requests import get_full_comment_data_by_user, get_user
from user_interface.ui_main import ai_chat

router = Router()


class Step(StatesGroup):
    ai_chat = State()


ai_chat_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Маршрут построен 😎")],
        [KeyboardButton(text="Назад")],
    ],
    input_field_placeholder="Выберите пункт",
    resize_keyboard=True,
    is_persistent=True,
)


@router.message(F.text == "🤖 Чат с ИИ")
async def start_ai_chat(message: Message, state: FSMContext):
    await ai_chat(message, state)


@router.message(Step.ai_chat, F.text == "Назад")
async def exit(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu("Операция отменена", message)


@router.message(Step.ai_chat, F.text == "Маршрут построен 😎")
async def ai_advice_request(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    data = await state.get_data()
    places_history = data.get("recomm_chat", [])
    if not places_history:
        raw_last_visited_places = await get_full_comment_data_by_user(tg_id)
        count_places = len(raw_last_visited_places)
        if count_places < 5:
            await message.answer(
                f"Недостаточно мест для составления рекомендации, нужно посетить еще {5 - count_places}.",
                reply_markup=ai_chat_keyboard,
            )
            return
        places_history = [*[f"{c.name}, {c.address}" for c in raw_last_visited_places]]
    ai_raw_places = await recom(places_history)
    described_places = await describe_places(ai_raw_places)
    if len(places_history) > 2:
        del places_history[0]
    places_history.append(ai_raw_places)
    await state.update_data(request_list=places_history, recomm_chat=places_history)
    await message.answer(
        described_places, reply_markup=ai_chat_keyboard, parse_mode="Markdown"
    )


@router.message(Step.ai_chat)
async def sending_message_to_ai(message: Message, state: FSMContext):
    latest_request_to_ai = message.text
    data = await state.get_data()
    request_list = data.get("request_list", [])
    request_list.append(f"Пользователь: {latest_request_to_ai}")
    ai_answer = await chat(request_list)
    if (
        ai_answer
        == "В интернете есть много сайтов с информацией на эту тему. [Посмотрите, что нашлось в поиске](https://ya.ru)"
    ):
        ai_answer = "Недопустимый запрос"
    request_list.append(f"Ассистент: {ai_answer}")
    if len(request_list) >= 10:
        del request_list[0:2]
    await state.update_data(request_list=request_list)

    await message.answer(ai_answer, reply_markup=ai_chat_keyboard)
