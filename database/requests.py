from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import joinedload, selectinload, relationship
from datetime import date
from typing import List, Optional
from dataclasses import dataclass


from .models import async_sessions
from .models import User, Place, Comment, Events


# таблица пользователей - статус 0 - ограниченный пользователь, 1 - обычный пользователь, 2 - менеджер, 3 - админ
async def add_user(
    tg_id: int, tg_username: str, regist_date: date, user_status: Optional[int] = 1
) -> None:
    async with async_sessions() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(
                User(
                    tg_id=tg_id,
                    tg_username=tg_username,
                    regist_date=regist_date,
                    user_status=user_status,
                )
            )
            await session.commit()


async def change_status_user(tg_id: int, user_status: Optional[int] = 1) -> None:
    async with async_sessions() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            user.user_status = user_status

        await session.commit()


async def get_user(
    tg_id: int = None,
    tg_username: Optional[str] = None,
    regist_date: Optional[date] = None,
    user_status: Optional[int] = None,
) -> Optional[User]:
    async with async_sessions() as session:
        query = select(User)

        if tg_id:
            query = query.where(User.tg_id == tg_id)
        if tg_username:
            query = query.where(User.tg_username == tg_username)
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
    avg_comment: Optional[str] = "",
) -> None:
    async with async_sessions() as session:
        session.add(
            Place(
                name=name,
                category=category,
                address=address,
                description=description,
                avg_comment=avg_comment,
            )
        )
        await session.commit()


async def get_place(
    place_id: Optional[int] = None,
    name: Optional[str] = None,
    address: Optional[str] = None,
) -> Optional[Place]:
    async with async_sessions() as session:
        query = select(Place)

        if place_id:
            query = query.where(Place.place_id == place_id)
        if name:
            query = query.where(Place.name == name)
        if address:
            query = query.where(Place.address == address)

        result = await session.scalars(query)
        return result.first()


async def update_place(
    place_id: int,
    new_category: Optional[str] = None,
    new_description: Optional[str] = None,
    new_avg_comment: Optional[str] = None,
) -> None:
    async with async_sessions() as session:
        place = await session.get(Place, place_id)
        if new_category:
            place.category = new_category
        if new_description:
            place.description = new_description
        if new_avg_comment:
            place.avg_comment = new_avg_comment
        await session.commit()


@dataclass
class FullCommentData:
    name: str
    address: str
    comment_text: str
    commentator_rating: int
    place_id: int


async def get_full_comment_data_by_user(tg_id: int):
    async with async_sessions() as session:
        # Загрузка комментариев с местами в одном запросе
        query = (
            select(Comment)
            .options(selectinload(Comment.place))  # Жадная загрузка
            .where(Comment.commentator_tg_id == tg_id)
        )

        result = await session.scalars(query)
        comments = result.all()

        return [
            FullCommentData(
                name=comment.place.name,
                address=comment.place.address,
                comment_text=comment.comment_text,
                commentator_rating=comment.commentator_rating,
                place_id=comment.place_id,
            )
            for comment in comments
        ]


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


from sqlalchemy.orm import selectinload


async def get_comments(
    place_id: Optional[int] = None,
    commentator_tg_id: Optional[int] = None,
    load_place: bool = False,
    filter_empty_text: bool = False,
) -> List[Comment]:
    async with async_sessions() as session:
        query = select(Comment).join(Place)

        if load_place:
            query = query.options(joinedload(Comment.place))

        # Собираем условия фильтрации
        conditions = []
        if place_id:
            conditions.append(Comment.place_id == place_id)
        if commentator_tg_id:
            conditions.append(Comment.commentator_tg_id == commentator_tg_id)
        if filter_empty_text:
            conditions.append(Comment.comment_text != "")

        if conditions:
            query = query.where(and_(*conditions))

        result = await session.scalars(query)
        return result.all()


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


async def delete_all_user_non_empty_comments(commentator_tg_id: int) -> None:
    async with async_sessions() as session:
        await session.execute(
            delete(Comment).where(
                and_(
                    Comment.commentator_tg_id == commentator_tg_id,
                    Comment.commentator_rating != 0,
                )
            )
        )
        await session.commit()


# таблица мероприятий
async def add_event(
    user_tg_id: int,
    kudago_id: int,
    event_name: str,
    event_time: str,
) -> None:
    async with async_sessions() as session:
        session.add(
            Events(
                user_tg_id=user_tg_id,
                kudago_id=kudago_id,
                event_name=event_name,
                event_time=event_time,
            )
        )
        await session.commit()


async def get_events(tg_id: int, kudago_id: Optional[int] = None) -> List[Events]:
    async with async_sessions() as session:
        query = select(Events).where(Events.user_tg_id == tg_id)

        if kudago_id is not None:
            query = query.where(Events.kudago_id == kudago_id)

        result = await session.scalars(query)
        return result.all()


async def delete_event(tg_id: int, kudago_id: int) -> None:
    async with async_sessions() as session:
        await session.execute(
            delete(Events).where(
                and_(Events.user_tg_id == tg_id, Events.kudago_id == kudago_id)
            )
        )
        await session.commit()
