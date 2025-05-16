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
    async def set_state(chat_id: int, new_state: State) -> None:
        storage = DispatcherHandler.__dispatcher.storage
        user_storage = StorageKey(DispatcherHandler.__bot.id, chat_id, chat_id)
        new_context = FSMContext(storage=storage, key=user_storage)
        await new_context.set_state(new_state)

    @staticmethod
    def set_data(bot: Bot, dispatcher: Dispatcher):
        if DispatcherHandler.__bot or DispatcherHandler.__dispatcher:
            raise ValueError(
                "You can't change bot or dispatcher after they were created"
            )
        DispatcherHandler.__bot = bot
        DispatcherHandler.__dispatcher = dispatcher
