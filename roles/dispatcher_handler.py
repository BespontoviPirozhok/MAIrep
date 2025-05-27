from aiogram import Dispatcher, Bot
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.context import FSMContext


class DispatcherHandler:
    __dispatcher: Dispatcher = None
    __bot: Bot = None

    def __init__(self, *args, **kwargs):
        raise ValueError("You can't create instance of this class")

    @staticmethod
    async def send_message(chat_id: int, message: str, reply_markup=None):
        await DispatcherHandler.__bot.send_message(
            chat_id, message, reply_markup=reply_markup
        )

    @staticmethod
    def set_data(bot: Bot, dispatcher: Dispatcher):
        if DispatcherHandler.__bot or DispatcherHandler.__dispatcher:
            raise ValueError(
                "You can't change bot or dispatcher after they were created"
            )
        DispatcherHandler.__bot = bot
        DispatcherHandler.__dispatcher = dispatcher
