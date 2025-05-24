from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from .yandex_gpt import you_mean

from user_interface.ui_main import *
from database.requests import get_user

smart_error_rt = Router()

COMMAND_HANDLERS = {
    "/search_locations": "search_places",
    "/search_events": "event_searching",
    "/profile": "profile",
    "/admins": "admin_menu",
    "/chat": "ai_chat",
    "/error": "return_to_user_menu",
}


@smart_error_rt.message()
async def route_ai_command(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    if await get_user(tg_id):
        ai_command = await you_mean(message.text)
        handler_name = COMMAND_HANDLERS.get(ai_command)

        if handler_name == "return_to_user_menu":
            # Обрабатываем /error отдельно с нужными аргументами
            await return_to_user_menu(
                "Увы, мне не понятны ваши слова, и потому я вынужден вернуть вас в главное меню",
                message,
            )
            return

        handler = globals().get(handler_name)
        if handler:
            await handler(message, state)
        else:
            # Если обработчик не найден, также возвращаем в меню
            await return_to_user_menu(
                "Команда не распознана, возвращаю в главное меню", message
            )
    else:
        await message.answer(
            "Вы еще не пользуетесь данным ботом. Чтобы это исправить, нажмите на /start"
        )
