import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, or_f
from aiogram import F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7361559221:AAFqDqzF0ZDOgzLS3nTva84JCo90b-UT_oE"

DATA_FILE = "locals.json"

def load_locals():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_locals():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(locals_dict, f, ensure_ascii=False, indent=2)

locals_dict = load_locals()

locals_dict.setdefault("Парк Горького", {
    "rating": 4.5,
    "votes": 2,
    "comments": ["Красивое место!", "Советую для прогулок"],
    "visited": False
})

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

class NewLocalForm(StatesGroup):
    waiting_for_place_name = State()
    waiting_for_new_note = State()
    waiting_for_new_comment = State()
    waiting_for_searching = State()
    waiting_for_mark_visited = State()

def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=" Добавить место"), KeyboardButton(text=" Оценить")],
            [KeyboardButton(text=" Комментарий"), KeyboardButton(text=" Поиск")],
            [KeyboardButton(text="Посетил"), KeyboardButton(text=" Помощь")]
        ],
        resize_keyboard=True
    )

def get_cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать! Я помогу вам работать с местами для досуга.\n"
        "Выберите действие:",
        reply_markup=get_main_kb()
    )

@dp.message(or_f(Command("help"), F.text.lower() == "помощь"))
async def cmd_help(message: types.Message):
    help_text = """
<b> Доступные команды:</b>

 Добавить место - создать новую локацию
Оценить - поставить оценку месту (1-5)
Комментарий - оставить отзыв
Поиск - найти информацию о месте
Посетил - отметить место как посещённое

В любой момент можно нажать ❌ Отмена
"""
    await message.answer(help_text, reply_markup=get_main_kb())

@dp.message(or_f(Command("newlocals"), F.text.lower().contains("добавить место")))
async def cmd_newlocals(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название нового места:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(NewLocalForm.waiting_for_place_name)

@dp.message(NewLocalForm.waiting_for_place_name)
async def process_place_name(message: types.Message, state: FSMContext):
    if message.text.lower() in ["отмена", "❌ отмена"]:
        await message.answer("❌ Действие отменено", reply_markup=get_main_kb())
        await state.clear()
        return

    place_name = message.text.strip()
    if not place_name:
        await message.answer("❌ Название не может быть пустым!", reply_markup=get_cancel_kb())
        return

    locals_dict[place_name] = {
        'rating': 0,
        'votes': 0,
        'comments': [],
        'visited': False
    }
    save_locals()
    await message.answer(
        f"✅ Место <b>'{place_name}'</b> успешно добавлено!",
        reply_markup=get_main_kb()
    )
    await state.clear()

@dp.message(or_f(Command("note"), F.text.lower().contains("оценить")))
async def cmd_note(message: types.Message, state: FSMContext):
    await message.answer(
        "⭐ Введите название места и оценку (от 1 до 5) в формате:\n"
        "<code>Название места - 4</code>",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(NewLocalForm.waiting_for_new_note)

@dp.message(NewLocalForm.waiting_for_new_note)
async def process_new_note(message: types.Message, state: FSMContext):
    if message.text.lower() in ["отмена", "❌ отмена"]:
        await message.answer("❌ Действие отменено", reply_markup=get_main_kb())
        await state.clear()
        return

    try:
        name, note = message.text.split('-', 1)
        name = name.strip()
        note = int(note.strip())

        if name not in locals_dict:
            await message.answer(f"❌ Место <b>'{name}'</b> не найдено!", reply_markup=get_main_kb())
            return

        if note < 1 or note > 5:
            await message.answer("❌ Оценка должна быть от 1 до 5!", reply_markup=get_cancel_kb())
            return

        place = locals_dict[name]
        new_rating = (place['rating'] * place['votes'] + note) / (place['votes'] + 1)
        place['rating'] = round(new_rating, 1)
        place['votes'] += 1
        save_locals()

        await message.answer(
            f"✅ Оценка для места <b>'{name}'</b> обновлена!\n"
            f"📊 Текущий рейтинг: {place['rating']} ({place['votes']} оценок)",
            reply_markup=get_main_kb()
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Используйте:\n<code>Название места - 4</code>",
            reply_markup=get_cancel_kb()
        )
    finally:
        await state.clear()

@dp.message(or_f(Command("comment"), F.text.lower().contains("комментарий")))
async def cmd_comment(message: types.Message, state: FSMContext):
    await message.answer(
        "💬 Введите название места и комментарий в формате:\n"
        "<code>Название места - Ваш текст</code>",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(NewLocalForm.waiting_for_new_comment)

@dp.message(NewLocalForm.waiting_for_new_comment)
async def process_new_comment(message: types.Message, state: FSMContext):
    if message.text.lower() in ["отмена", "❌ отмена"]:
        await message.answer("❌ Действие отменено", reply_markup=get_main_kb())
        await state.clear()
        return

    try:
        name, comment = message.text.split('-', 1)
        name = name.strip()
        comment = comment.strip()

        if not name or not comment:
            raise ValueError

        if name not in locals_dict:
            await message.answer(f"❌ Место <b>'{name}'</b> не найдено!", reply_markup=get_main_kb())
            return

        locals_dict[name]['comments'].append(comment)
        save_locals()
        await message.answer(
            f"✅ Ваш комментарий к месту <b>'{name}'</b> сохранён!",
            reply_markup=get_main_kb()
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Используйте:\n<code>Название места - Ваш текст</code>",
            reply_markup=get_cancel_kb()
        )
    finally:
        await state.clear()

@dp.message(or_f(Command("search"), F.text.lower().contains("поиск")))
async def cmd_search(message: types.Message, state: FSMContext):
    await message.answer(
        "🔍 Введите название места, о котором хотите узнать:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(NewLocalForm.waiting_for_searching)

@dp.message(NewLocalForm.waiting_for_searching)
async def process_search(message: types.Message, state: FSMContext):
    if message.text.lower() in ["отмена", "❌ отмена"]:
        await message.answer("❌ Действие отменено", reply_markup=get_main_kb())
        await state.clear()
        return

    name = message.text.strip()
    if name in locals_dict:
        place = locals_dict[name]
        comments = "\n".join([f"• {c}" for c in place['comments']]) if place['comments'] else "пока нет комментариев"
        visited_status = "✅ Да" if place.get("visited") else "❌ Нет"

        info = (
            f"📌 <b>{name}</b>\n\n"
            f"⭐ Рейтинг: {place['rating']}/5 (на основе {place['votes']} оценок)\n"
            f"🚶 Посещено: {visited_status}\n\n"
            f"💬 Комментарии:\n{comments}"
        )
        await message.answer(info, reply_markup=get_main_kb())
    else:
        await message.answer(f"❌ Место <b>'{name}'</b> не найдено!", reply_markup=get_main_kb())
    await state.clear()

@dp.message(or_f(Command("visited"), F.text.lower().contains("посетил")))
async def cmd_visited(message: types.Message, state: FSMContext):
    await message.answer(
        "✅ Введите название места, которое вы посетили:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(NewLocalForm.waiting_for_mark_visited)

@dp.message(NewLocalForm.waiting_for_mark_visited)
async def process_visited(message: types.Message, state: FSMContext):
    if message.text.lower() in ["отмена", "❌ отмена"]:
        await message.answer("❌ Действие отменено", reply_markup=get_main_kb())
        await state.clear()
        return

    name = message.text.strip()
    if name in locals_dict:
        locals_dict[name]['visited'] = True
        save_locals()
        await message.answer(f"✅ Место <b>'{name}'</b> отмечено как посещённое!", reply_markup=get_main_kb())
    else:
        await message.answer(f"❌ Место <b>'{name}'</b> не найдено!", reply_markup=get_main_kb())
    await state.clear()

@dp.message(or_f(F.text.lower() == "отмена", F.text.lower() == "❌ отмена"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("ℹ️ Нет активных действий для отмены", reply_markup=get_main_kb())
        return

    await state.clear()
    await message.answer("❌ Действие отменено", reply_markup=get_main_kb())

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="newlocals", description="Добавить место"),
        BotCommand(command="note", description="Оценить место"),
        BotCommand(command="comment", description="Оставить комментарий"),
        BotCommand(command="search", description="Поиск места"),
        BotCommand(command="visited", description="Отметить как посещённое")
    ]
    await bot.set_my_commands(commands)

async def on_startup(bot: Bot):
    save_locals()
    await set_bot_commands(bot)
    logger.info("Бот успешно запущен!")

async def main():
    dp.startup.register(on_startup)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
