from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import joinedload
from datetime import date
from typing import List, Optional
from dataclasses import dataclass


from .models import async_sessions
from .models import User, Place, Comment, VisitedPlace


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


async def set_user(tg_id: int, regist_date: date) -> None:
    async with async_sessions() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id, regist_date=regist_date))
            await session.commit()


async def get_user(tg_id: int) -> Optional[User]:
    async with async_sessions() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


async def get_places() -> List[Place]:
    async with async_sessions() as session:
        result = await session.scalars(select(Place))
        return result.all()


async def get_current_place(place_name: str) -> Optional[Place]:
    async with async_sessions() as session:
        return await session.scalar(select(Place).where(Place.name == place_name))


async def get_place_by_id(
    place_id: int,
) -> Optional[Place]:  # синий кент зачем-то написал и такую функцию
    async with async_sessions() as session:
        return await session.scalar(select(Place).where(Place.place_id == place_id))


async def add_place(name: str, description: str, summary_rating: float) -> None:
    async with async_sessions() as session:
        session.add(
            Place(name=name, description=description, summary_rating=summary_rating)
        )
        await session.commit()


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


async def delete_comment(commentator_tg_id: int, place_name: str) -> None:
    async with async_sessions() as session:
        await session.execute(
            delete(Comment).where(
                and_(
                    Comment.commentator_tg_id == commentator_tg_id,
                    Comment.place_name == place_name,
                )
            )
        )
        await session.commit()


async def has_comment(commentator_tg_id: int, place_name: str) -> bool:
    async with async_sessions() as session:
        result = await session.scalar(
            select(Comment).where(
                and_(
                    Comment.commentator_tg_id == commentator_tg_id,
                    Comment.place_name == place_name,
                )
            )
        )
        return result is not None


async def get_comments(
    place_name: Optional[str] = None, commentator_tg_id: Optional[int] = None
) -> List[Comment]:
    async with async_sessions() as session:
        query = select(Comment)
        if place_name:
            query = query.where(Comment.place_name == place_name)
        if commentator_tg_id:
            query = query.where(Comment.commentator_tg_id == commentator_tg_id)
        result = await session.scalars(query)
        return result.all()


async def get_visits(user_id: Optional[int] = None) -> List[VisitedPlace]:
    async with async_sessions() as session:
        query = select(VisitedPlace).where(VisitedPlace.user_id == user_id)
        result = await session.scalars(query.order_by(VisitedPlace.visit_date.desc()))
        return result.all()


async def add_visit(user_id: int, place_id: int, visit_date: date) -> None:
    async with async_sessions() as session:
        session.add(
            VisitedPlace(user_id=user_id, place_id=place_id, visit_date=visit_date)
        )
        await session.commit()


async def has_visited(user_id: int, place_id: int) -> bool:
    async with async_sessions() as session:
        result = await session.scalar(
            select(VisitedPlace).where(
                and_(VisitedPlace.user_id == user_id, VisitedPlace.place_id == place_id)
            )
        )
        return result is not None


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


async def search_places(query: str) -> List[Place]:
    async with async_sessions() as session:
        result = await session.scalars(
            select(Place).where(func.lower(Place.name).contains(func.lower(query)))
        )
        return result.all()
