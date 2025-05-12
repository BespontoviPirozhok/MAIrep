from sqlalchemy import Integer, Float, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from dotenv import load_dotenv
import os

load_dotenv()
DB = os.getenv("DATABASE")
engine = create_async_engine(DB)

async_sessions = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, unique=True)
    regist_date = mapped_column(Date)
    user_status: Mapped[int] = mapped_column(Integer)


# статус 0 - ограниченный пользователь, 1 - обычный пользователь, 2 - менеджер, 3 - админ


class Place(Base):
    __tablename__ = "places"

    place_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(200))


class Comment(Base):
    __tablename__ = "comments"

    comment_id: Mapped[int] = mapped_column(primary_key=True)
    commentator_tg_id = mapped_column(BigInteger)
    place_id: Mapped[int] = mapped_column(Integer)
    comment_text: Mapped[str] = mapped_column(String(200))
    commentator_rating: Mapped[int] = mapped_column(Integer)


class VisitedEvents(Base):
    __tablename__ = "visited_events"

    visit_id: Mapped[int] = mapped_column(primary_key=True)
    user_tg_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    review_text: Mapped[str] = mapped_column(String(200))


async def get_db():
    async with async_sessionmaker() as session:
        yield session


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
