from typing import Optional

from sqlalchemy import Result, and_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

from database.models import Warns
from database.session import async_session


async def add_user(tg_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            stmt = insert(Warns).values(tg_id=tg_id).on_conflict_do_nothing(
                index_elements=['tg_id']
            )
            await session.execute(stmt)


async def add_warn(user_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(Warns)
                .where(and_(Warns.tg_id == user_id, Warns.warns < 3))
                .values(warns=Warns.warns + 1)
            )


async def reset_warns(user_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(Warns).where(Warns.tg_id == user_id).values(warns=0)
            )


async def check_warns(user_id: int) -> int:
    async with async_session() as session:
        result: Result[tuple[int]] = await session.execute(select(Warns.warns).where(Warns.tg_id == user_id))

        warns: Optional[int] = result.scalar_one_or_none()
        return warns if warns else 0


async def delete_warn(tg_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(Warns)
                .where(and_(Warns.tg_id == tg_id, Warns.warns > 0))
                .values(warns=Warns.warns - 1)
            )