import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = "7361559221:AAFqDqzF0ZDOgzLS3nTva84JCo90b-UT_oE"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Заготовка для бота")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
