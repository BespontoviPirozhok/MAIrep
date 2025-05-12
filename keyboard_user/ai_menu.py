from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import Router
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, F

from .main_menu import return_to_user_menu

router = Router()


class Step(StatesGroup):
    ai_chat = State()
    ai_advice = State()


ai_chat_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Маршрут построен 😎")],
        [KeyboardButton(text="Назад")],
    ],
    input_field_placeholder="Выберите пункт",
    resize_keyboard=True,
    is_persistent=True,
)

ai_advice_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Другая рекомендация")],
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
)


@router.message(F.text == "🤖 Чат с ИИ")
async def help(message: Message, state: FSMContext):
    await state.set_state(Step.ai_chat)
    await message.answer(
        """Добро пожаловать в чат с ИИ, вот что он умеет:
- Вы можете поболтать с нашим ИИ ассистентом на любые темы, просто набрав сообщение сюда ⬇️
- С опцией "Маршрут построен 😎" ассистент порекомендует вам новые интересные места на основании 5-ти последних посещенных"
        """,
        reply_markup=ai_chat_keyboard,
    )


@router.message(Step.ai_chat, F.text == "Назад")
async def exit(message: Message, state: FSMContext):
    await state.clear()
    await return_to_user_menu(message.from_user.id, "Операция отменена", message)


@router.message(Step.ai_chat, F.text == "Маршрут построен 😎")
async def ai_advice_request(message: Message, state: FSMContext):
    await state.set_state(Step.ai_advice)
    await message.answer(
        "Здесь должны быть рекомендации",
        reply_markup=ai_advice_keyboard,
    )


@router.message(Step.ai_advice, F.text == "Назад")
async def ai_advice_back(message: Message, state: FSMContext):
    await state.set_state(Step.ai_chat)
    await message.answer(
        "Хотите поболтать? Просто напишите сообщение и ассистент на него ответит",
        reply_markup=ai_chat_keyboard,
    )


@router.message(Step.ai_advice, F.text == "Другая рекомендация")
async def ai_advice_back(message: Message, state: FSMContext):
    await message.answer(
        "Тут должная быть другая рекомендация",
        reply_markup=ai_advice_keyboard,
    )


@router.message(Step.ai_chat)
async def sending_message_to_ai(message: Message, state: FSMContext):
    request_to_ai = message.text
    print(request_to_ai)
    await message.answer_sticker(
        r"CAACAgIAAxkBAAEOZD9oEnDFvWYOx4FG4HSPqijWCx8iPwACqGAAAn_xWUq5KNvV3mYaEDYE"
    )
