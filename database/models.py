from sqlalchemy import Integer, Float, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from loaded_dotenv import DB

engine = create_async_engine(DB)

async_sessions = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, unique=True)
    tg_username: Mapped[str] = mapped_column(String(30), unique=True)
    regist_date = mapped_column(Date)
    user_status: Mapped[int] = mapped_column(Integer)


# статус 0 - ограниченный пользователь, 1 - обычный пользователь, 2 - менеджер, 3 - админ, 4 - владелец


class Place(Base):
    __tablename__ = "places"

    place_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(200))
    avg_comment: Mapped[str] = mapped_column(String(100))

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="place", lazy="raise"
    )


class Comment(Base):
    __tablename__ = "comments"

    comment_id: Mapped[int] = mapped_column(primary_key=True)
    commentator_tg_id = mapped_column(BigInteger)
    place_id: Mapped[int] = mapped_column(
        ForeignKey("places.place_id")
    )  # Явный ForeignKey
    comment_text: Mapped[str] = mapped_column(String(200))
    commentator_rating: Mapped[int] = mapped_column(Integer)

    place: Mapped["Place"] = relationship(back_populates="comments", lazy="raise")


class Events(Base):
    __tablename__ = "events"

    event_id: Mapped[int] = mapped_column(primary_key=True)
    user_tg_id: Mapped[int] = mapped_column(BigInteger)
    kudago_id: Mapped[int] = mapped_column(BigInteger)
    event_name: Mapped[str] = mapped_column(String(50))
    event_time: Mapped[str] = mapped_column(String(15))


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
