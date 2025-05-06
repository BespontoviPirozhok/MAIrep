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

from datetime import datetime
from keyboard_user.main_menu import beautiful_time
from .main_menu import return_to_user_menu, back_reply

router = Router()


class Step(StatesGroup):
    search_input = State()
    places_list = State()
    place_view = State()
    feedback = State()
    сomments_list = State()


places_data = {
    "МАИ": {
        "description": "описание для места МАИ",
        "rating": "5.0",
        "summary": "сводка комментариев для МАИ",
        "comments": {
            "Комментарий 1 для МАИ": ("95 лет МАИ, юхууу", (1930, 3, 20)),
            "Комментарий 2 для МАИ": ("Чапаев", (1887, 1, 28)),
            "Комментарий 3 для МАИ": ("Петька", (1666, 10, 20)),
            "Комментарий 3 для МАИ": ("Семга-Вемон", (2025, 3, 18)),
        },
    },
    "МГУ": {
        "description": "описание для места МГУ",
        "rating": "1.0",
        "summary": "сводка комментариев для МГУ",
        "comments": {
            "Комментарий 1 для МГУ": ("Штирлиц", (1900, 10, 8)),
            "Комментарий 2 для МГУ": ("Сталин", (1879, 12, 21)),
            "Комментарий 3 для МГУ": ("Калыван", (1666, 8, 3)),
        },
    },
    "Парк Горького": {
        "description": "описание для места Парк Горького",
        "rating": "3.6",
        "summary": "сводка комментариев для Парка Горького",
        "comments": {
            "Комментарий 1 для Парка Горького": ("Горький", (1666, 6, 10)),
            "Комментарий 2 для Парка Горького": ("Кислый", (1666, 6, 20)),
            "Комментарий 3 для Парка Горького": ("Сладкий)", (1666, 7, 5)),
        },
    },
    "Парк Покровское-Стрешнево": {
        "description": "описание для места Парк Покровское-Стрешнево",
        "rating": "4.9",
        "summary": "сводка комментариев для Парка Покровское-Стрешнево",
        "comments": {
            "Комментарий 1 для Парка Покровское-Стрешнево": (
                "Эщкере",
                (1666, 5, 30),
            ),
            "Комментарий 2 для Парка Покровское-Стрешнево": (
                "Тампоны для Алены",
                (1666, 6, 12),
            ),
            "Комментарий 3 для Парка Покровское-Стрешнево": (
                "Та самая белка",
                (1666, 6, 25),
            ),
        },
    },
    "Офис ВК": {
        "description": "описание для места Офис ВК",
        "rating": "0.0",
        "summary": "сводка комментариев для Офис ВК",
        "comments": {
            "Комментарий 1 для Офис ВК": ("Сеньор без опыта", (1666, 4, 18)),
            "Комментарий 2 для Офис ВК": ("Опрометчивый маркетолог", (1666, 5, 2)),
            "Комментарий 3 для Офис ВК": ("Дэб", (1666, 5, 15)),
        },
    },
}


place_view_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Отметить это место как посещенное")],
        [KeyboardButton(text="Посмотреть комментарии")],
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
    is_persistent=True,
)

places_list_inline = InlineKeyboardBuilder()
for place in places_data.keys():
    places_list_inline.row(InlineKeyboardButton(text=place, callback_data=place))
places_list_inline.row(
    InlineKeyboardButton(text="Назад", callback_data="back_to_search")
)


@router.message(F.text == "🔍 Поиск мест")
async def search(message: Message, state: FSMContext):
    await state.set_state(Step.search_input)
    await message.answer(
        """Введите название места, например:
- Москва (пока работает только это)""",
        reply_markup=back_reply,
    )


@router.message(Step.search_input, F.text == "Назад")
async def exit(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu("Операция отменена", message)


# ---------- Обработка ввода "Москва" ----------, тут надо сделать запрос в карты и потом уже чето из них получать
@router.message(Step.search_input, F.text.casefold() == "москва")
async def inline_places(message: Message, state: FSMContext):
    await state.set_state(Step.places_list)
    await message.answer("Ищем место на картах 👀", reply_markup=ReplyKeyboardRemove())
    await message.answer(
        "Выберите место из списка:", reply_markup=places_list_inline.as_markup()
    )


async def search_request(message: Message, state: FSMContext):
    await state.set_state(Step.places_list)
    await inline_places(message, state)


@router.message(Step.search_input)
async def unknown_city(message: Message, state: FSMContext):
    await message.answer(
        "Пока поддерживается только поиск по Москве. Попробуйте ввести 'Москва'"
    )


@router.callback_query(F.data == "back_to_search")
async def back_to_search_step(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Step.search_input)

    await callback.message.edit_text(
        """Введите название места, например:
- Москва (пока работает только это)"""
    )
    await callback.message.answer(
        "Вы вернулись к поиску:",
        reply_markup=back_reply,
    )
    await callback.answer()


@router.callback_query(Step.places_list)
async def place_chosen(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "back_to_search":
        return
    place = data
    if place not in places_data:
        await callback.answer("Неизвестное место", show_alert=True)
        return

    await state.set_state(Step.place_view)
    await state.update_data(current_place=place)

    d = places_data[place]
    text = (
        f"{place}\n\n"
        f"{d['description']}\n"
        f"Рейтинг: {d['rating']}\n\n"
        f"{d['summary']}"
    )

    await callback.message.edit_reply_markup(None)
    await callback.message.answer(text, reply_markup=place_view_reply)
    await callback.answer()


@router.message(Step.place_view, F.text == "Назад")
async def back_to_places_list(message: Message, state: FSMContext):
    await state.set_state(Step.places_list)
    await message.answer(
        "Продолжаем искать дальше...", reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Выберите место из списка:",
        reply_markup=places_list_inline.as_markup(),
    )


@router.message(Step.сomments_list, F.text == "Назад")
async def back_from_comments(message: Message, state: FSMContext):
    await state.set_state(Step.place_view)
    await message.answer(
        "Вы вернулись к информации о месте.", reply_markup=place_view_reply
    )


# 4) «отметить как посещенное»
@router.message(Step.place_view, F.text == "Отметить это место как посещенное")
async def mark_visited(message: Message, state: FSMContext):
    await message.answer(
        "Тут должен быть диалог оценки и комментирования, но тимлид чето захотел спатки",
        reply_markup=place_view_reply,
    )


@router.message(Step.place_view, F.text == "Посмотреть комментарии")
async def show_comments(message: Message, state: FSMContext):
    data = await state.get_data()
    place = data.get("current_place")
    await state.set_state(Step.сomments_list)
    for comment, (user, dt) in places_data[place]["comments"].items():
        await message.answer(
            f"{user}, {beautiful_time(datetime(*dt))}\n{comment}",
            reply_markup=back_reply,
        )
