from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, F

from .main_menu import return_to_user_menu

router = Router()


class Step(StatesGroup):
    help_menu = State()
    help_input = State()


@router.message(F.text == "❓ Помощь")
async def help(message: Message, state: FSMContext):
    await state.set_state(Step.help_menu)
    await message.answer(
        """Функции бота:
🔍 Поиск мест - поиск интересующих вас мест
💬 Чат с ИИ - возможность по душам поболтать с искусственным интеллектом
🪪 Профиль - информация о ваших посещенных местах, отзывах и комментариях
❓ Помощь - вывод данной справки еще раз или отправка сообщения о неполадке бота службе поддержки""",
        reply_markup=help_reply_keyboard,
    )


help_reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Задать вопрос поддержке")],
        [KeyboardButton(text="Назад")],
    ],
    input_field_placeholder="Выберите пункт",
    resize_keyboard=True,
)

help_input_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
)


@router.message(Step.help_menu, F.text == "Назад")
async def exit(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu("Операция отменена", message)


@router.message(Step.help_menu)
async def help_input_request(message: Message, state: FSMContext):
    await state.set_state(Step.help_input)
    await message.answer(
        "Опишите ваш вопрос или проблему 👇",
        reply_markup=help_input_keyboard,
    )


@router.message(Step.help_input, F.text == "Назад")
async def help_input_back(message: Message, state: FSMContext):
    await state.set_state(Step.help_menu)
    await message.answer(
        "Выберите действие:",
        reply_markup=help_reply_keyboard,
    )


@router.message(Step.help_input)
async def process_support_question(message: Message, state: FSMContext):
    user_question = message.text
    await return_to_user_menu(
        "Спасибо за ваше сообщение! Мы скоро свяжемся с вами.", message
    )
    print(user_question)
    await state.clear()
