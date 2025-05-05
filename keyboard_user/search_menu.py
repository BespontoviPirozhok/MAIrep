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

from .main_menu import return_to_user_menu

router = Router()


class Step(StatesGroup):
    search_input = State()
    places_list = State()
    place_view = State()
    сomments_list = State()


Moscow_places = [
    "МАИ",
    "МГУ",
    "Парк Горького",
    "Парк Покровское-Стрешнево",
    "Офис ВК",
    "Центр",
    "ВДНХ",
    "Лужники",
    "Останкино",
    "Сокольники",
    "Третьяковка",
    "Арбат",
]


search_input_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
)


# ---------- Обработка "🔍 Поиск мест" ----------
@router.message(F.text == "🔍 Поиск мест")
async def search(message: Message, state: FSMContext):
    await state.set_state(Step.search_input)
    await message.answer(
        """Введите название места, например:
- Москва (пока работает только это)""",
        reply_markup=search_input_keyboard,
    )


# ---------- Назад из поиска ----------
@router.message(Step.search_input, F.text == "Назад")
async def exit(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu("Операция отменена", message)


# ---------- Обработка ввода "Москва" ----------
@router.message(Step.search_input, F.text.casefold() == "москва")
async def search_request(message: Message, state: FSMContext):
    await state.set_state(Step.places_list)
    await inline_places(message, state)  # прямо вызываем генерацию inline клавиатуры


# ---------- Обработка остальных текстов ----------
@router.message(Step.search_input)
async def unknown_city(message: Message, state: FSMContext):
    await message.answer(
        "Пока поддерживается только поиск по Москве. Попробуйте ввести 'Москва'."
    )


@router.message(Step.places_list)
async def inline_places(message: Message, state: FSMContext):
    await state.set_state(Step.place_view)

    keyboard = InlineKeyboardBuilder()
    for place in Moscow_places[:4]:
        keyboard.row(InlineKeyboardButton(text=place, callback_data=f"place_{place}"))
    keyboard.row(InlineKeyboardButton(text="Назад", callback_data="back_to_search"))

    # Сначала скрываем системную клавиатуру (если вдруг активна)
    await message.answer("Ищем место на картах 👀", reply_markup=ReplyKeyboardRemove())

    # Потом показываем inline-меню
    await message.answer(
        "Выберите место из списка:",
        reply_markup=keyboard.as_markup(),
    )


# ---------- Callback: Назад из inline списка ----------
@router.callback_query(F.data == "back_to_search")
async def back_to_search_step(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Step.search_input)

    # Убираем inline-клавиатуру, возвращаемся к поиску
    await callback.message.edit_text(
        """Введите название места, например:
- Москва (пока работает только это)"""
    )
    # Отправляем сообщение с reply-клавиатурой "Назад"
    await callback.message.answer(
        "Вы вернулись к поиску:",
        reply_markup=search_input_keyboard,
    )
    await callback.answer()


# ---------- Назад из показа списка ----------
@router.message(Step.place_view, F.text == "Назад")
async def back_from_place_list(message: Message, state: FSMContext):
    await state.set_state(Step.search_input)
    await message.answer(
        """Введите название места, например:
- Москва (пока работает только это)""",
        reply_markup=search_input_keyboard,
    )
