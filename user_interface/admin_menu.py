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

from roles.dispatcher_handler import DispatcherHandler
from roles.roles_main import (
    admin_check,
    get_user_status_text,
    owner_check,
)

from user_interface.ui_main import (
    admin_menu,
    admin_extended_reply,
    return_to_user_menu,
    back_reply,
)
from database.requests import (
    get_user,
    change_status_user,
    delete_all_user_non_empty_comments,
)


router = Router()


class Step(StatesGroup):
    admin_menu = State()
    give_roles = State()
    ban_unban = State()


delete_all_user_comments_reply = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Удалить"),
        ],
        [
            KeyboardButton(text="Не удалять"),
        ],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
    resize_keyboard=True,
)


async def handle_role_assignment(message: Message, user_tg_id: int):
    user_id = await get_user(tg_id=user_tg_id)
    admin_id = message.from_user.id
    is_owner = await owner_check(
        admin_id
    )  # Проверка, является ли текущий пользователь владельцем

    if user_id.user_status == 4:
        await message.answer(
            "Данный пользователь является владельцем, его никто не может ограничить",
            reply_markup=back_reply,
        )
        return
    if user_id.user_status == 12 and not is_owner:
        await message.answer(
            "Данный пользователь является администратором, ограничить его может только владелец",
            reply_markup=back_reply,
        )
        return

    status_text = await get_user_status_text(user_tg_id)

    roles = [
        (3, "Администратор"),
        (2, "Менеджер"),
        (1, "Обычный пользователь"),
        (0, "Пользователь с ограничениями"),
    ]

    available_roles = []
    for role_id, role_name in roles:
        # Пропускаем текущую роль пользователя
        if role_id == user_id.user_status:
            continue
        # Скрываем "Администратор" для НЕ-владельцев
        if role_id == 3 and not is_owner:
            continue
        available_roles.append(KeyboardButton(text=role_name))

    # Создаем клавиатуру
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[btn] for btn in available_roles] + [[KeyboardButton(text="Назад")]],
        resize_keyboard=True,
    )

    await message.answer(
        f"Данный пользователь - {status_text}, какую роль хотите ему выдать:",
        reply_markup=keyboard,
    )


@router.message(F.text == "Ⓜ️ Админ-меню")
async def start_admin_menu(message: Message, state: FSMContext):
    await admin_menu(message, state)


@router.message(Step.admin_menu, F.text == "Назад в обычное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu("Вы вернулись в обычное меню", message)


@router.message(Step.admin_menu, F.text == "Изменить роль пользователя")
async def role_change_welcome(message: Message, state: FSMContext):
    await state.set_state(Step.give_roles)
    await message.answer(
        """Справка о правах пользователей в зависимости от ролей:
- <b>Ограниченный пользователь</b>: отметка/снятие отметки о посещении мест и мероприятий.
- <b>Обычный пользователь</b>: добавление мест в базу данных, оставление комментариев и оценок.
- <b>Менеджер</b> (включая права обычного пользователя): редактирование описаний и категорий мест.
- <b>Администратор</b>: смена ролей пользователей (дополнительно ко всем предыдущим функциям).

Введите TG_ID или <code>@username</code> пользователя для изменения его роли. 
Если ваше сообщение исчезло, это означает, что вы не можете изменить права данного пользователя.""",
        reply_markup=back_reply,
        parse_mode="HTML",
    )


@router.message(Step.give_roles, F.text == "Назад")
async def role_change_exit(message: Message, state: FSMContext):
    await state.set_state(Step.admin_menu)
    await message.answer(
        "Вы вернулись в Админ-меню",
        reply_markup=admin_extended_reply,
    )


@router.message(Step.give_roles, F.text == "Администратор")
async def role_change_exit(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if await owner_check(user_id):
        data = await state.get_data()
        tg_id = data.get("tg_id")
        await change_status_user(tg_id, 3)
        await state.update_data(tg_id=None)
        await message.answer(
            "Вы выдали данному пользователю роль администратора.\n\nЧтобы изменить роль другого пользователя, просто напишите его tg id ниже.",
            reply_markup=back_reply,
        )
        await DispatcherHandler.send_message(tg_id, "Вы стали администратором!")
    else:
        await message.answer(
            f"Администраторы не могут изменять роль других администаторов!",
            reply_markup=back_reply,
        )


@router.message(Step.give_roles, F.text == "Менеджер")
async def role_change_exit(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    await change_status_user(tg_id, 2)
    await state.update_data(tg_id=None)
    await message.answer(
        "Вы выдали данному пользователю роль менеджера.\n\nЧтобы изменить роль другого пользователя, просто напишите его tg id ниже.",
        reply_markup=back_reply,
    )
    await DispatcherHandler.send_message(tg_id, "Вы стали менеджером")


@router.message(Step.give_roles, F.text == "Обычный пользователь")
async def role_change_exit(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    await change_status_user(tg_id, 1)
    await message.answer(
        "Вы выдали данному пользователю роль обычного пользователя.\n\nЧтобы изменить роль другого пользователя, просто напишите его tg id ниже.",
        reply_markup=back_reply,
    )
    await DispatcherHandler.send_message(tg_id, "Вы стали обычным пользователем")


@router.message(Step.give_roles, F.text == "Пользователь с ограничениями")
async def role_change_exit(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    await change_status_user(tg_id, 0)
    await message.answer(
        "Вы ограничили данного пользователя.\n\nВы также можете удалить все уже существующие комментарии и оценки этого пользователя безвозратно.",
        reply_markup=delete_all_user_comments_reply,
    )


@router.message(Step.give_roles, F.text == "Удалить")
async def role_change_exit(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    await delete_all_user_non_empty_comments(tg_id)
    await message.answer(
        "Все комментарии и оценки пользователя удалены\n\nЧтобы изменить роль другого пользователя, просто напишите его tg id ниже.",
        reply_markup=back_reply,
    )
    await DispatcherHandler.send_message(
        tg_id,
        "Вы стали ограниченным пользователем, ваши оценки и комментарии полностью удалены",
    )


@router.message(Step.give_roles, F.text == "Не удалять")
async def role_change_exit(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    await message.answer(
        "Оценки и комментарии остались нетронутыми\n\nЧтобы изменить роль другого пользователя, просто напишите его tg id ниже.",
        reply_markup=back_reply,
    )
    await DispatcherHandler.send_message(
        tg_id,
        "Вы стали ограниченным пользователем, ваши оценки и комментарии в целости и сохранности",
    )


@router.message(Step.give_roles)
async def role_change_menu(message: Message, state: FSMContext):
    raw_input = message.text.strip()
    user = None
    tg_id = None

    # Определение типа ввода
    if raw_input.startswith("@"):
        # Обработка username
        tg_username = raw_input[1:]
        user = await get_user(tg_username=tg_username)
        if user:
            tg_id = user.tg_id

    elif raw_input.isdigit():
        # Обработка ID
        tg_id = int(raw_input)
        user = await get_user(tg_id)
    else:
        await message.delete()
        return

    # Проверка существования пользователя
    if not user:
        await message.delete()
        return

    # Проверка самодеактивации
    if tg_id == message.from_user.id:
        await message.delete()
        return

    # Передача управления и сохранение данных
    await handle_role_assignment(message, tg_id)
    await state.update_data(tg_id=tg_id)
