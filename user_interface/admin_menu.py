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

from user_interface.main_menu import (
    admin_menu_reply,
    return_to_user_menu,
    back_reply,
    main_menu_reply,
)
from roles.dispatcher_handler import DispatcherHandler
from roles.roles_main import (
    admin_check,
    get_user_status_text,
    owner_check,
)

from database.requests import (
    get_place,
    add_place,
    get_comments,
    get_user,
    change_status_user,
    delete_all_user_non_empty_comments,
)


router = Router()

admin_extended_reply = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Изменить роль пользователя"),
            KeyboardButton(text="Что нужно сделать тимлиду?"),
        ],
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="Назад в обычное меню"),
        ],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
)
delete_comments_reply = ReplyKeyboardMarkup(
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


class Step(StatesGroup):
    admin_menu = State()
    give_roles = State()
    ban_unban = State()


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
async def exit(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await admin_check(user_id):
        user_role = await get_user_status_text(user_id)
        await return_to_user_menu(
            user_id, f"Вы - {user_role}, вам не доступно админ-меню!", message
        )
    else:
        await state.set_state(Step.admin_menu)
        await message.answer(
            "Добро пожаловать в Админ-меню! Скоро здесь будет описание как всем этим пользоваться",
            reply_markup=admin_extended_reply,
        )


@router.message(Step.admin_menu, F.text == "Назад в обычное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu(
        message.from_user.id, "Вы вернулись в обычное меню", message
    )


@router.message(Step.admin_menu, F.text == "Изменить роль пользователя")
async def role_change_welcome(message: Message, state: FSMContext):
    await state.set_state(Step.give_roles)
    await message.answer(
        """Справка о правах пользователей в зависимости от ролей:
- *Ограниченный пользователь*: отметка/снятие отметки о посещении мест и мероприятий.
- *Обычный пользователь*: добавление мест в базу данных, оставление комментариев и оценок.
- *Менеджер* (включая права обычного пользователя): редактирование описаний и категорий мест.
- *Администратор*: смена ролей пользователей (дополнительно ко всем предыдущим функциям).

Введите ID пользователя для изменения его роли.""",
        reply_markup=back_reply,
        parse_mode="MARKDOWN",
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
        reply_markup=delete_comments_reply,
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
    raw_tg_id = message.text
    if len(raw_tg_id) < 8 or not raw_tg_id.isdigit():
        await message.answer(
            "Неверный тип данных!",
            reply_markup=back_reply,
        )
        return

    tg_id = int(raw_tg_id)
    if not await get_user(tg_id):
        await message.answer(
            "Данный пользователь не пользуется ботом!",
            reply_markup=back_reply,
        )
    elif tg_id == message.from_user.id:
        await message.answer_sticker(
            r"CAACAgIAAxkBAAEOeXpoI8k2d0KNlQNw-6N0yhw1FgF_NQACJkQAAlVjOUoDhSheRxpQOjYE"
        )
        await message.answer(
            "Вы не можете уменьшить свои полномочия!", reply_markup=back_reply
        )
    else:
        await handle_role_assignment(message, tg_id)
        await state.update_data(tg_id=tg_id)


@router.message(Step.admin_menu, F.text == "Что нужно сделать тимлиду?")
async def role_change_welcome(message: Message, state: FSMContext):
    await message.answer_sticker(
        r"CAACAgIAAxkBAAEOeetoJG2GqFRopR3iPwYs1cXMJIXkRQACIiIAApfZIUhQxfUZvjllyjYE"
    )
    await message.answer("Тимлиду нужно поспать!", reply_markup=admin_extended_reply)
