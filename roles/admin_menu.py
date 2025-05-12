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

from keyboard_user.main_menu import (
    admin_menu_reply,
    return_to_user_menu,
    back_reply,
)

from roles.roles_main import user_check, manager_check, admin_check, translate

from database.requests import get_place, add_place, get_comments, get_user

from map_and_events.map import map_search

router = Router()

admin_extended_reply = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Выдать роль админа или менеджера"),
            KeyboardButton(text="Ограничить пользователя или снять ограничение"),
        ],
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="Назад в обычное меню"),
        ],
    ],
    is_persistent=True,
    input_field_placeholder="Выберите пункт",
)


class Step(StatesGroup):  # состояния
    admin_menu = State()
    give_roles = State()
    ban_unban = State()


@router.message(Step.admin_menu, F.text == "Назад в обычное меню")
async def exit(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu(
        message.from_user.id, "Вы вернулись в обычное меню", message
    )


@router.message(F.text == "Ⓜ️ Админ-меню")
async def exit(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await admin_check(user_id):
        user_role = translate((await get_user(user_id)).user_status)
        await return_to_user_menu(user_id, f"Ваша роль {user_role}", message)
    else:
        await state.set_state(Step.admin_menu)
        await message.answer(
            "Добро пожаловать в Админ-меню! Скоро здесь будет описание как всем этим пользоваться",
            reply_markup=admin_extended_reply,
        )
