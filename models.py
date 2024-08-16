import os
from typing import Annotated

from sqlalchemy import Integer, BigInteger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_async_engine(url=DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

intpk = Annotated[int, mapped_column(primary_key=True)]
warint = Annotated[int, mapped_column(Integer, nullable=False, default=0)]

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users_moderations'
    
    id: Mapped[intpk]
    tg_id: Mapped[BigInteger] = mapped_column(BigInteger, unique=True)
    warns: Mapped[warint]
