from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import joinedload, selectinload, relationship
from datetime import date
from typing import List, Optional
from dataclasses import dataclass


from .models import async_sessions
from .models import User, Place, Comment, VisitedEvents


# таблица пользователей - статус 0 - ограниченный пользователь, 1 - обычный пользователь, 2 - менеджер, 3 - админ
async def add_user(
    tg_id: int, regist_date: date, user_status: Optional[int] = 1
) -> None:
    async with async_sessions() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(
                User(tg_id=tg_id, regist_date=regist_date, user_status=user_status)
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
    regist_date: Optional[date] = None,
    user_status: Optional[int] = None,
) -> Optional[User]:
    async with async_sessions() as session:
        query = select(User)

        if tg_id:
            query = query.where(User.tg_id == tg_id)
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
) -> None:
    async with async_sessions() as session:
        place = await session.get(Place, place_id)
        if new_category:
            place.category = new_category
        if new_description:
            place.description = new_description
        await session.commit()


@dataclass
class FullCommentData:
    name: str
    address: str
    comment_text: str
    commentator_rating: int


# async def get_full_comment_data_by_user(tg_id: int) -> List[FullCommentData]:
#     all_comments = await get_comments(commentator_tg_id=tg_id)
#     place_ids = {comment.place_id for comment in all_comments}

#     # Получаем все места, связанные с этими place_id
#     places_dict = {}
#     async with async_sessions() as session:
#         query = select(Place).where(Place.place_id.in_(place_ids))
#         result = await session.scalars(query)
#         for place in result.all():
#             places_dict[place.place_id] = place

#     # Собираем итоговые данные
#     full_data_list = []
#     for comment in all_comments:
#         place = places_dict.get(comment.place_id)
#         if place:
#             full_data_list.append(
#                 FullCommentData(
#                     name=place.name,
#                     address=place.address,
#                     comment_text=comment.comment_text,
#                     commentator_rating=comment.commentator_rating,
#                 )
#             )
#     return full_data_list


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
    load_place: bool = False,  # Новая опция загрузки
) -> List[Comment]:
    async with async_sessions() as session:
        query = select(Comment)

        if load_place:
            query = query.options(selectinload(Comment.place))

        if place_id:
            query = query.where(Comment.place_id == place_id)
        if commentator_tg_id:
            query = query.where(Comment.commentator_tg_id == commentator_tg_id)

        result = await session.scalars(query)
        return result.all()


# async def get_comments(
#     place_id: Optional[int] = None, commentator_tg_id: Optional[int] = None
# ) -> List[Comment]:
#     async with async_sessions() as session:
#         query = select(Comment)
#         if place_id:
#             query = query.where(Comment.place_id == place_id)
#         if commentator_tg_id:
#             query = query.where(Comment.commentator_tg_id == commentator_tg_id)
#         result = await session.scalars(query)
#         return result.all()


async def delete_comment(
    commentator_tg_id: int, place_id: Optional[int] = None
) -> None:
    async with async_sessions() as session:
        conditions = [Comment.commentator_tg_id == commentator_tg_id]
        if place_id is not None:
            conditions.append(Comment.place_id == place_id)

        await session.execute(delete(Comment).where(and_(*conditions)))
        await session.commit()


async def print_comments_details(
    place_id: Optional[int] = None, commentator_tg_id: Optional[int] = None
) -> None:
    comments = await get_comments(place_id, commentator_tg_id)

    if not comments:
        print("No comments found")
        return

    for idx, comment in enumerate(comments, 1):
        print(f"\n=== Comment {idx} ===")

        # Выводим все атрибуты модели через рефлексию
        for attr_name in dir(comment):
            if not attr_name.startswith("_") and not callable(
                getattr(comment, attr_name)
            ):
                attr_value = getattr(comment, attr_name)
                print(f"{attr_name}:")
                print(f"  Value: {repr(attr_value)}")
                print(f"  Type:  {type(attr_value).__name__}")


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
async def get_events(user_tg_id: int) -> List[VisitedEvents]:
    async with async_sessions() as session:
        query = select(VisitedEvents).where(VisitedEvents.user_tg_id == user_tg_id)
        result = await session.scalars(query.order_by(VisitedEvents.visit_id.desc()))
        return result.all()


async def add_event(user_tg_id: int, review_text: str) -> None:
    async with async_sessions() as session:
        session.add(VisitedEvents(user_tg_id=user_tg_id, review_text=review_text))
        await session.commit()


async def delete_event(user_tg_id: int, visit_id: int) -> None:
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
