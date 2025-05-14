# AIOGRAM
from aiogram import Bot, Dispatcher

# ОСТАЛЬНЫЕ ИМПОРТЫ
import asyncio, logging, sys
from database.models import async_main
from loaded_keys import TOKEN

# КЛАВИАТУРЫ
from user_interface.main_menu import router as main_menu_rt
from user_interface.admin_menu import router as admin_menu_rt
from user_interface.edit_place_menu import router as edit_place_menu_rt
from user_interface.event_menu import router as event_menu_rt
from user_interface.search_menu import router as search_menu_rt
from user_interface.ai_menu import router as ai_menu_rt
from user_interface.profile_menu import router as profile_menu_rt
from user_interface.feedback_menu import router as feedback_menu_rt
from user_interface.comments_menu import router as comments_menu_rt
from user_interface.main_menu import error_rt

# РОУТЕРЫ
dp = Dispatcher()
dp.include_router(main_menu_rt)
dp.include_router(edit_place_menu_rt)
dp.include_router(admin_menu_rt)
dp.include_router(search_menu_rt)
dp.include_router(event_menu_rt)
dp.include_router(ai_menu_rt)
dp.include_router(profile_menu_rt)
dp.include_router(comments_menu_rt)
dp.include_router(feedback_menu_rt)
dp.include_router(error_rt)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(TOKEN)

    try:
        logger.info("Starting bot...")
        await async_main()  # Запуск БД
        await dp.start_polling(bot)  # Запуск бота
    except asyncio.CancelledError:
        logger.info("Bot stopped by user request")
    except Exception as e:
        logger.exception(f"Bot stopped with error: {e}")
    finally:
        logger.info("Shutting down...")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
