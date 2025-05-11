# AIOGRAM
from aiogram import Bot, Dispatcher

# ОСТАЛЬНЫЕ МОДУЛИ
from dotenv import load_dotenv
import os
import asyncio
import logging
import sys
from database.models import async_main

# КЛАВИАТУРЫ
from keyboard_user.main_menu import router as main_menu_rt
from keyboard_user.help_menu import router as help_menu_rt
from keyboard_user.search_menu import router as search_menu_rt
from keyboard_user.ai_menu import router as ai_menu_rt
from keyboard_user.profile_menu import router as profile_menu_rt
from keyboard_user.feedback_menu import router as feedback_menu_rt

# from keyboard_user.comments_menu import router as comments_menu_rt
from keyboard_user.main_menu import error_rt

# ТОКЕН И БД
load_dotenv()
TOKEN = os.getenv("TOKEN")

# РОУТЕРЫ
dp = Dispatcher()
dp.include_router(main_menu_rt)
dp.include_router(search_menu_rt)
dp.include_router(help_menu_rt)
dp.include_router(ai_menu_rt)
dp.include_router(profile_menu_rt)
# dp.include_router(comments_menu_rt)
dp.include_router(feedback_menu_rt)
dp.include_router(error_rt)


async def main() -> None:
    await async_main()  # Запуск БД
    bot = Bot(TOKEN)
    await dp.start_polling(bot)  # Запуск бота


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
