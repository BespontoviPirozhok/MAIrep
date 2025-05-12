from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import joinedload
from datetime import date
from typing import List, Optional
from dataclasses import dataclass


from .models import async_sessions
from .models import User, Place, Comment, VisitedEvents


# таблица пользователей - статус 0 - ограниченный пользователь, 1 - обычный пользователь, 2 - менеджер, 3 - админ
async def set_user(
    tg_id: int, regist_date: date, user_status: Optional[int] = 1
) -> None:
    async with async_sessions() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(
                User(tg_id=tg_id, regist_date=regist_date, user_status=user_status)
            )
            await session.commit()


async def get_user(
    tg_id: int = None,
    username: Optional[str] = None,
    regist_date: Optional[date] = None,
    user_status: Optional[int] = None,
) -> Optional[User]:
    async with async_sessions() as session:
        query = select(User)

        if tg_id:
            query = query.where(User.tg_id == tg_id)
        if username:
            query = query.where(User.username == username)
        if regist_date:
            query = query.where(User.regist_date == regist_date)
        if user_status:
            query = query.where(User.user_status == user_status)

        result = await session.scalars(query)
        return result.first()


# таблица мест
async def add_place(
    name: str,
    category: str,
    address: str,
    description: Optional[str] = "",
) -> None:
    async with async_sessions() as session:
        session.add(
            Place(
                name=name,
                category=category,
                address=address,
                description=description,
            )
        )
        await session.commit()


async def get_place(
    place_id: Optional[int] = None,
    name: Optional[str] = None,
    address: Optional[str] = None,
) -> Optional[Place]:
    async with async_sessions() as session:
        query = select(Place)  # Ищем места, а не комментарии

        if place_id:
            query = query.where(Place.place_id == place_id)
        if name:
            query = query.where(Place.name == name)
        if address:
            query = query.where(Place.address == address)

        result = await session.scalars(query)
        return (
            result.first()
        )  # функция раньше возвращала список мест, но де-факто каждое место уникально => сейчас функция выводит первое место из списка


# Таблица комментариев
async def add_comment(
    commentator_tg_id: int,
    place_id: int,
    text: str,
    rating: int,
) -> None:
    async with async_sessions() as session:
        session.add(
            Comment(
                commentator_tg_id=commentator_tg_id,
                comment_text=text,
                place_id=place_id,
                commentator_rating=rating,
            )
        )
        await session.commit()


async def delete_comment(commentator_tg_id: int, place_id: int) -> None:
    async with async_sessions() as session:
        await session.execute(
            delete(Comment).where(
                and_(
                    Comment.commentator_tg_id == commentator_tg_id,
                    Comment.place_id == place_id,
                )
            )
        )
        await session.commit()


async def get_comments(
    place_id: Optional[int] = None, commentator_tg_id: Optional[int] = None
) -> List[Comment]:
    async with async_sessions() as session:
        query = select(Comment)
        if place_id:
            query = query.where(Comment.place_id == place_id)
        if commentator_tg_id:
            query = query.where(Comment.commentator_tg_id == commentator_tg_id)
        result = await session.scalars(query)
        return result.all()


# тут надо конкретно переделывать функцию получения статистики, а может полностью ее убирать P.S - я удалил ненужные классы в начале кода и эта функция сломалась, так что я ее закомментировал
# async def get_user_stats(
#     tg_id: int,
# ) -> "UserInfo":  # перепиши, чтобы можно было получать дату регистрации
#     async with async_sessions() as session:
#         user = await session.scalar(
#             select(User)
#             .where(User.tg_id == tg_id)
#             .options(joinedload(User.comment), joinedload(User.visited_places))
#         )
#         if user:
#             comments = [comment.text for comment in user.comments]
#             places = [visit.place for visit in user.visited_places]
#             return UserInfo(
#                 comments=comments, places=places, reg_date=user.registration_date
#             )
#         return UserInfo(comments=[], places=[], reg_date=None)


# таблица мероприятий
async def get_visits(user_tg_id: int) -> List[VisitedEvents]:
    async with async_sessions() as session:
        query = select(VisitedEvents).where(VisitedEvents.user_tg_id == user_tg_id)
        result = await session.scalars(query.order_by(VisitedEvents.visit_id.desc()))
        return result.all()


async def add_visit(user_tg_id: int, review_text: str) -> None:
    async with async_sessions() as session:
        session.add(VisitedEvents(user_tg_id=user_tg_id, review_text=review_text))
        await session.commit()


async def delete_visit(user_tg_id: int, visit_id: int) -> None:
    """Удалить визит по ID, только если он принадлежит указанному пользователю"""
    async with async_sessions() as session:
        await session.execute(
            delete(VisitedEvents).where(
                and_(
                    VisitedEvents.user_tg_id == user_tg_id,
                    VisitedEvents.visit_id == visit_id,
                )
            )
        )
        await session.commit()
