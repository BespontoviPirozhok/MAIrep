# admin_comments.py
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from database.requests import get_comments, delete_comment
from roles.roles_main import admin_check, get_user_status_text
from .admin_menu import admin_extended_reply
from .ui_main import return_to_user_menu

router = Router()


class Step(StatesGroup):
    admin_menu = State()
    comment_delete_list = State()
    confirm_delete = State()


confirm_delete_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Удалить")],
        [
            KeyboardButton(text="Отмена"),
        ],
    ],
    resize_keyboard=True,
)


@router.message(Step.admin_menu, F.text == "Удаление комментариев")
async def show_all_comments(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    if not await admin_check(tg_id):
        await return_to_user_menu(
            "У вас нет права удалять комменатрии!", message, tg_id
        )
        return

    all_comments = await get_comments(load_place=True, filter_empty_text=True)
    await state.set_state(Step.comment_delete_list)
    await state.update_data(all_comments=all_comments, current_page=0)
    await display_comments_batch(message, state)


async def display_comments_batch(message: Message, state: FSMContext):
    data = await state.get_data()
    all_comments = data.get("all_comments", [])[::-1]
    page = data.get("current_page", 0)

    # Корректируем номер страницы если он превышает максимум
    max_page = max(0, (len(all_comments) - 1) // 3)
    if page > max_page:
        page = max_page
        await state.update_data(current_page=page)

    total_comments = len(all_comments)
    start_idx = page * 3
    end_idx = start_idx + 3
    batch = all_comments[start_idx:end_idx]

    # Если комментариев нет вообще
    if not batch and page == 0:
        await message.answer("Комментариев нет", reply_markup=admin_extended_reply)
        await state.set_state(Step.admin_menu)
        return
    elif not batch:  # Если страница пуста, но есть предыдущие
        await state.update_data(current_page=page - 1)
        await display_comments_batch(message, state)
        return

    # Отображение комментариев
    for comment in batch:
        try:
            status = await get_user_status_text(comment.commentator_tg_id)
        except Exception:
            status = "Неизвестный статус"
        await message.answer(
            f"Место: <b>{comment.place.name}</b>\n"
            f"TG_ID: <code>{comment.commentator_tg_id}</code> ({status})\n\n"
            f"{comment.comment_text}",
            parse_mode="HTML",
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

    # Управление пагинацией
    control_buttons = []
    if len(all_comments) > end_idx:
        control_buttons.append([KeyboardButton(text="Показать ещё")])

    control_buttons.append([KeyboardButton(text="Назад")])

    # Текст с прогрессом
    shown_comments = min(end_idx, total_comments)
    progress_text = f"Показано {shown_comments} из {total_comments} комментариев"

    await message.answer(
        text=progress_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=control_buttons,
            input_field_placeholder=f"Страница {page + 1}",
            resize_keyboard=True,
        ),
    )


@router.callback_query(Step.comment_delete_list, F.data.startswith("delete_"))
async def handle_delete_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Step.confirm_delete)
    _, tg_id, place_id = callback.data.split("_")

    # Используем данные из callback_data без запроса к БД
    await state.update_data(
        del_tg_id=int(tg_id),
        del_place_id=int(place_id),
    )

    # Получаем текст комментария из state (если требуется)
    data = await state.get_data()
    all_comments = data.get("all_comments", [])

    # Ищем комментарий в локальном кэше
    target_comment = next(
        (
            c
            for c in all_comments
            if c.commentator_tg_id == int(tg_id) and c.place_id == int(place_id)
        ),
        None,
    )

    try:
        status = await get_user_status_text(target_comment.commentator_tg_id)
    except Exception:
        status = "Неизвестный статус"
    preview_message = (
        "Вы собираетесь удалить комментарий:\n\n"
        f"Место: <b>{target_comment.place.name}</b>\n"
        f"TG_ID: <code>{tg_id}</code> ({status})\n\n"
        f"{target_comment.comment_text}"
    )

    await callback.message.answer(
        preview_message, parse_mode="HTML", reply_markup=confirm_delete_reply
    )
    await callback.answer()


@router.message(Step.confirm_delete, F.text == "Удалить")
async def handle_confirm_delete(message: Message, state: FSMContext):
    data = await state.get_data()

    await delete_comment(
        commentator_tg_id=data["del_tg_id"], place_id=data["del_place_id"]
    )

    await message.answer("Комментарий удален, возращаемся к просмотру комментариев")

    all_comments = await get_comments(load_place=True, filter_empty_text=True)
    await state.update_data(all_comments=all_comments)
    await state.set_state(Step.comment_delete_list)
    await display_comments_batch(message, state)


@router.message(Step.confirm_delete, F.text == "Отмена")
async def handle_cancel_delete(message: Message, state: FSMContext):
    await state.set_state(Step.comment_delete_list)
    await display_comments_batch(message, state)


@router.message(Step.comment_delete_list, F.text == "Показать ещё")
async def next_page(message: Message, state: FSMContext):
    data = await state.get_data()
    current_page = data.get("current_page", 0)
    await state.update_data(current_page=current_page + 1)
    await display_comments_batch(message, state)


@router.message(Step.comment_delete_list, F.text == "Назад")
async def exit_delete_comments(message: Message, state: FSMContext):
    await state.set_state(Step.admin_menu)
    await message.answer("Возвращаемся к Админ-меню", reply_markup=admin_extended_reply)
