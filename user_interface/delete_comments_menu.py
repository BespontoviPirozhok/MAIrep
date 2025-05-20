# admin_comments.py
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from database.requests import (
    get_comments,
    delete_comment,
    get_full_comment_data_by_user,
)
from roles.roles_main import admin_check

router = Router()


class State(StatesGroup):
    admin_menu = State()
    viewing_comments = State()
    confirm_delete = State()


# Восстановленный обработчик входа
@router.message(F.text == "Удаление комментариев")
async def show_all_comments(message: Message, state: FSMContext):
    if not await admin_check(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return

    all_comments = await get_comments(load_place=True, filter_empty_text=True)
    await state.update_data(all_comments=all_comments, current_page=0)
    await state.set_state(State.viewing_comments)
    await display_comments_batch(message, state)


async def display_comments_batch(message: Message, state: FSMContext):
    data = await state.get_data()
    all_comments = data.get("all_comments", [])
    page = data.get("current_page", 0)

    start_idx = page * 3
    end_idx = start_idx + 3
    batch = all_comments[start_idx:end_idx]

    if not batch:
        await message.answer("📭 Нет комментариев для отображения")
        return

    for comment in batch:
        await message.answer(
            f"🏷 Место: {comment.place.name}\n"
            f"👤 Пользователь: {comment.commentator_tg_id}\n"
            f"⭐ Оценка: {comment.commentator_rating}/5\n"
            f"📝 Комментарий: {comment.comment_text}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="❌ Удалить",
                            callback_data=f"delete_{comment.commentator_tg_id}_{comment.place_id}",
                        )
                    ]
                ]
            ),
        )

    control_buttons = []
    if len(all_comments) > end_idx:
        control_buttons.append(
            InlineKeyboardButton(
                text="📜 Показать ещё", callback_data="next_comments_page"
            )
        )

    control_buttons.append(
        InlineKeyboardButton(text="🔙 Назад", callback_data="exit_comments")
    )

    await message.answer(
        f"📖 Страница {page + 1}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[control_buttons]),
    )


@router.callback_query(F.data.startswith("delete_"))
async def handle_delete_start(callback: CallbackQuery, state: FSMContext):
    _, tg_id, place_id = callback.data.split("_")
    tg_id = int(tg_id)
    place_id = int(place_id)

    # Получаем полные данные комментария
    comments = await get_comments(
        commentator_tg_id=tg_id, place_id=place_id, load_place=True
    )

    if not comments:
        await callback.answer("Комментарий не найден!")
        return

    comment = comments[0]

    await state.update_data(
        del_tg_id=tg_id,
        del_place_id=place_id,
        comment_text=comment.comment_text,
        place_name=comment.place.name,
    )

    preview_message = (
        "🗑 Вы собираетесь удалить комментарий:\n\n"
        f"🏷 Место: {comment.place.name}\n"
        f"📝 Текст: {comment.comment_text}\n\n"
        "❓ Подтвердите удаление:"
    )

    await callback.message.answer(
        preview_message,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить", callback_data="confirm_del"
                    ),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_del"),
                ]
            ]
        ),
    )
    await state.set_state(State.confirm_delete)
    await callback.answer()


@router.callback_query(State.confirm_delete, F.data == "confirm_del")
async def handle_confirm_delete(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await delete_comment(
        commentator_tg_id=data["del_tg_id"], place_id=data["del_place_id"]
    )

    await callback.message.answer("Комментарий удален")

    all_comments = await get_comments(load_place=True, filter_empty_text=True)
    await state.update_data(all_comments=all_comments, current_page=0)
    await state.set_state(State.viewing_comments)
    await display_comments_batch(callback.message, state)
    await callback.answer()


@router.callback_query(State.confirm_delete, F.data == "cancel_del")
async def handle_cancel_delete(callback: CallbackQuery, state: FSMContext):
    await state.set_state(State.viewing_comments)
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "next_comments_page")
async def next_page(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get("current_page", 0)
    await state.update_data(current_page=current_page + 1)
    await display_comments_batch(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "exit_comments")
async def exit_comments(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🏠 Возврат в главное меню")
    await callback.answer()
