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
from keyboard_user.main_menu import beautiful_date
from .main_menu import return_to_user_menu, back_reply

router = Router()


class Step(StatesGroup):  # состояния
    search_input = State()  # поисковая строка
    places_list = State()  # список мест согласно выдаче
    place_view = State()  # просмотр информации о месте
    сomments_list = State()  # просмотр списка комментариев
    feedback = State()
    # оставляем отзыв и коммент, попробую все это запихнуть в одно состояние


places_data = {
    "МАИ": {
        "description": "описание для места МАИ",
        "rating": "5.0",
        "summary": "сводка комментариев для МАИ",
        "comments": {
            "Бомонка ли я или ВУЗ самостоятельный?": ("ГУК", (1930, 3, 20)),
            "С днем рождения меня!": ("М.А. Погосян", (2016, 4, 18)),
            "Я простофиля №1": ("участник семги", (1666, 10, 20)),
            "А я простофиля №2": (
                "участник семги",
                (2025, 3, 18),
            ),
            "Ура, МАИ исполнилось 95 лет! 🥳": ("Тимлид семги", (2025, 3, 20)),
            "- Василий Иванович, а что такое камасутра?\n- Помнишь, Петька, ты про нюанс спрашивал?\n Вот то же самое, только двадцатью разными способами.": (
                "Чапаев",
                (1887, 1, 28),
            ),
            "А я простофиля №2": (
                "участник семги, о котором никто не узнает))))",
                (1666, 10, 20),
            ),  # из-за тупой структуры комментариев в виде словаря нельзя показывать одинаковые комментарии, хоть они и от разных авторов и сделаны в разное время
            "А я простофиля №3": ("участник семги", (2025, 3, 18)),
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
            "Комментарий 4 для МГУ": ("Чапаев", (1887, 1, 28)),
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

@router.callback_query(Step.places_list)
async def place_chosen(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "back_to_search":
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

    await callback.message.delete()
    await callback.message.answer(text, reply_markup=place_view_reply)


@router.message(Step.place_view, F.text == "Назад")
async def back_to_places_list(message: Message, state: FSMContext):
    await state.set_state(Step.places_list)
    await message.answer(
        "Смотрим интересные места...", reply_markup=ReplyKeyboardRemove()
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


@router.message(Step.place_view, F.text == "Отметить это место как посещенное")
async def mark_visited(message: Message, state: FSMContext):
    await message.answer(
        "Тут должен быть диалог оценки и комментирования, но тимлид чето захотел спатки",
        reply_markup=place_view_reply,
    )


# @router.message(Step.place_view, F.text == "Посмотреть комментарии") #старая версия показа комментов - показываются сразу все комменты
# async def show_comments(message: Message, state: FSMContext):
#     data = await state.get_data()
#     place = data.get("current_place")
#     await state.set_state(Step.сomments_list)
#     for comment, (comment_user, comment_date) in places_data[place]["comments"].items():
#         await message.answer(
#             f"{comment_user}, {beautiful_date(comment_date)}\n{comment}",
#             reply_markup=back_reply,
#         )


# ниже выдача синего кента по запросу постраничной выдачи комментов


@router.message(Step.place_view, F.text == "Посмотреть комментарии")
async def show_comments(message: Message, state: FSMContext):
    data = await state.get_data()
    place = data.get("current_place")
    await state.set_state(Step.сomments_list)

    # Получаем и сортируем комментарии
    all_comments = sorted(
        places_data[place]["comments"].items(),
        key=lambda x: x[1][1],  # Сортировка по дате (кортеж (год, месяц, день))
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
                [KeyboardButton(text="Показать еще"), KeyboardButton(text="Назад")]
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
    # Показываем следующую порцию
    await show_more_comments(message, state)
