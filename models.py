from typing import Annotated
from sqlalchemy import String, Integer, BigInteger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


DATABASE_URL = 'YOUR_DATABASE_URL'

engine = create_async_engine(url=DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


intpk = Annotated[int, mapped_column(primary_key=True)]
string = Annotated[str, mapped_column(String(125), nullable=False)]
warint = Annotated[int, mapped_column(Integer, nullable=False, default=0)]


class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users_moderations'
    
    id: Mapped[intpk]
    tg_id: Mapped[int] = mapped_column(BigInteger)
    warns: Mapped[warint]


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")