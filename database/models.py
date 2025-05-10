from sqlalchemy import Integer, Float, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_async_engine(os.getenv("DATABASE"))

async_sessions = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger, primary_key=True)
    regist_date = mapped_column(Date)
    # comments = relationship("Comment", back_populates="user")
    # visited_places = relationship("VisitedPlace", back_populates="user")


class Place(Base):
    __tablename__ = "places"

    place_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    adress: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(200))
    summary_rating: Mapped[float] = mapped_column(Float)
    # comments = relationship("Comment", back_populates="place")


class Comment(Base):
    __tablename__ = "comments"

    comment_id: Mapped[int] = mapped_column(primary_key=True)
    commentator_tg_id = mapped_column(BigInteger)
    place_name: Mapped[str] = mapped_column(String(30))
    comment_text: Mapped[str] = mapped_column(String(200))
    commentator_rating: Mapped[int] = mapped_column(Integer)
    # user = relationship("User", back_populates="comments")
    # place = relationship("Place", back_populates="comments")


class VisitedPlace(Base):
    __tablename__ = "visited_places"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    place_id: Mapped[int] = mapped_column(
        ForeignKey("places.place_id"), primary_key=True
    )
    visit_date = mapped_column(Date)
    # user = relationship("User", back_populates="visited_places")
    # place = relationship("Place", back_populates="visited_places")


async def get_db():
    async with async_sessionmaker() as session:
        yield session


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
