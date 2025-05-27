from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
)
from aiogram import Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from roles.roles_main import (
    get_user_status_text,
    get_user,
    admin_check,
)

from database.requests import get_full_comment_data_by_user, get_user, get_events

from map_and_events.kudago import cities_kudago, pretty_date

router = Router()


class Step(StatesGroup):  # состояния
    place_search = State()
    event_search = State()
    profile_menu = State()
    ai_chat = State()
    admin_menu = State()


back_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


main_menu_reply = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Поиск мест"),
            KeyboardButton(text="🏝️ Поиск мероприятий"),
        ],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🤖 Чат с ИИ")],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
)

admin_menu_reply = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Поиск мест"),
            KeyboardButton(text="🏝️ Поиск мероприятий"),
        ],
        [
            KeyboardButton(text="Ⓜ️ Админ-меню"),
            KeyboardButton(text="🤖 Чат с ИИ"),
        ],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
)


async def return_to_user_menu(
    msg_txt: str, message: Message, tg_id: int = None
) -> None:
    if not tg_id:
        tg_id = message.from_user.id
    if await admin_check(tg_id):
        await message.answer(
            msg_txt,
            reply_markup=admin_menu_reply,
        )
    else:
        await message.answer(
            msg_txt,
            reply_markup=main_menu_reply,
        )


async def search_places(message: Message, state: FSMContext):
    await state.set_state(Step.place_search)
    await message.answer(
        """
Рядом названием каждого места есть специальный значок:
✅ - Вы уже посетили данное место;
🌎 - Место есть в базе данных, возможно у него уже есть оценки и комментарии;
🌐 - Места еще нет в базе данных, но вы можете его туда добавить.
Если ваше сообщение исчезло, значит по вашему запросу ничего не нашлось.
""",
    )
    await message.answer(
        """Введите название места, которое хотите найти
""",
        reply_markup=back_reply,
    )


async def cities_kb_def(state):
    data = await state.get_data()
    city_eng = data.get("city_eng", "msk")
    city_dict = await cities_kudago()
    cities_keyboard = []
    for city_rus_dict, city_eng_dict in city_dict.items():
        if city_eng == city_eng_dict:
            continue
        cities_keyboard.append(
            [
                InlineKeyboardButton(
                    text=city_rus_dict,
                    callback_data=f"city_{city_rus_dict}_{city_eng_dict}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=cities_keyboard)


async def event_searching(message: Message, state: FSMContext):
    data = await state.get_data()
    city_rus = data.get("city_rus", "Москва")

    await state.set_state(Step.event_search)
    await message.answer(
        f"Выберите город, в котором хотите искать мероприятия. Выбранный город - *{city_rus}*",
        reply_markup=await cities_kb_def(state),
        parse_mode="Markdown",
    )
    await message.answer(
        f"🔎 *Введите название мероприятия, которое хотите найти.\nЕсли ваше сообщение исчезло, значит по вашему запросу ничего не нашлось.*",
        reply_markup=back_reply,
        parse_mode="Markdown",
    )


async def ai_chat(message: Message, state: FSMContext):
    await state.set_state(Step.ai_chat)
    await message.answer(
        """Добро пожаловать в чат с ИИ, вот что он умеет:
- Вы можете поболтать с нашим ИИ ассистентом на любые темы, просто набрав сообщение сюда ⬇️
- С опцией "Маршрут построен 😎" ассистент порекомендует вам новые интересные места на основании 5-ти последних посещенных. При повторном нажатии бот пишет новую рекомендацию."
        """,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Маршрут построен 😎")],
                [KeyboardButton(text="Назад")],
            ],
            input_field_placeholder="Выберите пункт",
            resize_keyboard=True,
            is_persistent=True,
        ),
    )


async def profile_keyboard(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    user_info = await get_user(tg_id)
    reg_date = user_info.regist_date
    await state.update_data(reg_date=reg_date)
    status_text = await get_user_status_text(tg_id)
    all_comments = (await get_full_comment_data_by_user(tg_id))[::-1]
    await state.update_data(all_comments=all_comments)
    ratings = [c for c in all_comments if c.commentator_rating != 0]
    await state.update_data(ratings=ratings)
    comments = [c for c in all_comments if c.comment_text != ""]
    await state.update_data(comments=comments)
    events = await get_events(tg_id)
    await state.update_data(events=events)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"    Дата регистрации: {pretty_date(str(reg_date))}    ",
                    callback_data="reg_date",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Посещённые места: {len(all_comments)}",
                    callback_data="visits",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Оценки: {len(ratings)}", callback_data="ratings"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Комментарии: {len(comments)}",
                    callback_data="comments",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Мероприятия: {len(events)}", callback_data="events"
                )
            ],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")],
        ]
    )
    await message.answer(f"Ваша роль: {status_text}", reply_markup=keyboard)


async def profile(message: Message, state: FSMContext):
    await state.set_state(Step.profile_menu)
    await message.answer(
        "Загрузка вашего профиля 🌐", reply_markup=ReplyKeyboardRemove()
    )
    await profile_keyboard(message, state)


admin_extended_reply = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Изменить роль пользователя"),
            KeyboardButton(text="Удаление комментариев"),
        ],
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="Назад в обычное меню"),
        ],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
)


async def admin_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await admin_check(user_id):
        user_role = await get_user_status_text(user_id)
        await return_to_user_menu(
            f"Вы - {user_role}, вам не доступно админ-меню!", message
        )
    else:
        await state.set_state(Step.admin_menu)
        await message.answer(
            "Добро пожаловать в Админ-меню!",
            reply_markup=admin_extended_reply,
        )
