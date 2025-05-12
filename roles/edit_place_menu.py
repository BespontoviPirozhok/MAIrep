from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardRemove,
)
from aiogram import Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from datetime import date
from roles.roles_main import user_check, manager_check
from database.requests import add_comment, get_comments, delete_comment, get_place
from keyboard_user.search_menu import place_view_smart_reply, get_place_info_text


router = Router()


class Step(StatesGroup):  # состояния
    place_view = State()
    edit_place = State()
    edit_place_confirm = State()


# "✏️ Изменить описание места"
