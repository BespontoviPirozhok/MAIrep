from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import joinedload
from datetime import date
from typing import List, Optional
from dataclasses import dataclass


from .models import async_sessions
from .models import User, Place, Comment, VisitedEvents


# два класса ниже я не думаю, что нужны, но пока оставлю
@dataclass
class Place_Class:
    name: str
    description: str
    rating: float


@dataclass
class UserInfo:
    comments: List[str]
    places: List[Place_Class]
    reg_date: date


# таблица пользователей - нужно указать статус, типа 0 - обычный пользователь, 1 - менеджер, 2 - админ
async def set_user(tg_id: int, regist_date: date) -> None:
    async with async_sessions() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id, regist_date=regist_date))
            await session.commit()


async def get_user(tg_id: int) -> Optional[User]:
    async with async_sessions() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


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
    place_name: str,
    text: str,
    rating: int,
) -> None:
    async with async_sessions() as session:
        session.add(
            Comment(
                commentator_tg_id=commentator_tg_id,
                comment_text=text,
                place_name=place_name,
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


# тут надо конкретно переделывать функцию получения статистики, а может полностью ее убирать
async def get_user_stats(
    tg_id: int,
) -> "UserInfo":  # перепиши, чтобы можно было получать дату регистрации
    async with async_sessions() as session:
        user = await session.scalar(
            select(User)
            .where(User.tg_id == tg_id)
            .options(joinedload(User.comment), joinedload(User.visited_places))
        )
        if user:
            comments = [comment.text for comment in user.comments]
            places = [visit.place for visit in user.visited_places]
            return UserInfo(
                comments=comments, places=places, reg_date=user.registration_date
            )
        return UserInfo(comments=[], places=[], reg_date=None)


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
