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

from database.requests import get_places, get_current_place

router = Router()


class Step(StatesGroup):  # состояния
    search_input = State()  # поисковая строка
    places_list = State()  # список мест согласно выдаче
    place_view = State()  # просмотр информации о месте


place_view_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Отметить это место как посещенное")],
        [KeyboardButton(text="Посмотреть комментарии")],
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
    is_persistent=True,
)

place_view_reply_visited = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Место уже посещено ✅")],
        [KeyboardButton(text="Посмотреть комментарии")],
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
    is_persistent=True,
)

async def places():
    all_places = await get_places()
    places_list_inline = InlineKeyboardBuilder()
    for place in all_places:
        places_list_inline.row(InlineKeyboardButton(text=place.name, callback_data=place.name))
    places_list_inline.row(
        InlineKeyboardButton(text="Назад", callback_data="back_to_search")
    )
    return places_list_inline


async def get_place_info_text(place_name: str) -> str:
    place = await get_current_place(place_name)
    return (
        f"{place.name}\n\n"
        f"{place.adress}\n"
        f"{place.description}\n"
        f"Рейтинг: {place.summary_rating}\n\n"
        # f"{place_data['summary']}"
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
    keyboard = await places()
    await message.answer(
        "Выберите место из списка:", reply_markup=keyboard.as_markup()
    )

async def search_request(message: Message, state: FSMContext):
    await state.set_state(Step.places_list)
    await inline_places(message, state)


@router.message(Step.search_input)
async def unknown_city(message: Message, state: FSMContext):
    await message.answer(
        "Пока поддерживается только поиск по Москве. Попробуйте ввести 'Москва'"
    )

@router.callback_query(Step.places_list)
async def place_chosen(callback: CallbackQuery, state: FSMContext):
    if callback.data == "back_to_search":
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
        return

    await state.set_state(Step.place_view)
    await state.update_data(current_place=callback.data)
    await callback.message.delete()
    await callback.message.answer(
        await get_place_info_text(callback.data),
        reply_markup=place_view_reply
    )


@router.message(Step.place_view, F.text == "Назад")
async def back_to_places_list(message: Message, state: FSMContext):
    await state.set_state(Step.places_list)
    await message.answer(
        "Смотрим интересные места...", reply_markup=ReplyKeyboardRemove()
    )
    keyboard = await places()
    await message.answer(
        "Выберите место из списка:",
        reply_markup=keyboard.as_markup(),
    )
<<<<<<< HEAD


@router.message(Step.сomments_list, F.text == "Назад")
async def back_from_comments(message: Message, state: FSMContext):
    await state.set_state(Step.place_view)
    await message.answer(
        "Вы вернулись к информации о месте.", reply_markup=place_view_reply
    )


@router.message(Step.place_view, F.text == "Посмотреть комментарии")
async def show_comments(message: Message, state: FSMContext):
    data = await state.get_data()
    place_id = data.get("current_place_id")
    await state.set_state(Step.сomments_list)

    # Получаем и сортируем комментарии
    comments = await get_comments(place_id=place_id)
    all_comments = sorted(
        comments,
        key=lambda x: x.comment_date,  # Сортировка по дате (кортеж (год, месяц, день))
        reverse=True,
    )

    # Инициализируем пагинацию
    await state.update_data(all_comments=all_comments, comment_offset=0)

    # Отправляем первую порцию
    await show_more_comments(message, state)


async def show_more_comments(message: Message, state: FSMContext):
    data = await state.get_data()
    all_comments = data["all_comments"]
    offset = data["comment_offset"]

    # Определяем порцию комментариев
    BATCH_SIZE = 5
    comments_batch = all_comments[offset : offset + BATCH_SIZE]

    # Отправляем комментарии
    for comment, (text, date_tuple) in comments_batch:
        await message.answer(
            f"{text}, {beautiful_date(date_tuple)}\n{comment}",
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
=======
>>>>>>> 4e7f20b (зарефакторил комменты, на время отключил отзывы)
