from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from .yandex_gpt import you_mean

from user_interface.aka_backend import *

smart_error_rt = Router()

COMMAND_HANDLERS = {
    "/search_locations": "search_places",
    "/search_events": "event_searching",
    "/profile": "profile",
    "/admins": "admin_menu",
    "/chat": "ai_chat",
}


@smart_error_rt.message()
async def route_ai_command(message: Message, state: FSMContext):
    ai_command = await you_mean(message.text)

    handler_name = COMMAND_HANDLERS.get(ai_command)
    handler = globals().get(handler_name)

    await handler(message, state)
