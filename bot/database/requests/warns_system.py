from typing import List, Optional, Union

from sqlalchemy import Result, and_, delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

from database.models import Reasons, Warns
from database.session import async_session


async def add_user(tg_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            new_user = insert(Warns).values(tg_id=tg_id).on_conflict_do_nothing(
                index_elements=['tg_id']
            )
            await session.execute(new_user)


async def add_reason(tg_id: int, reason: str) -> None:
    async with async_session() as session:
        async with session.begin():
            new_reason = insert(Reasons).values(tg_id=tg_id, reasons=reason).on_conflict_do_nothing(
                index_elements=['tg_id', 'reasons']
            )
            await session.execute(new_reason)


async def get_user_reasons(tg_id: int) -> Union[List[str], str]:
    async with async_session() as session:
        result: Result = await session.execute(
            select(Reasons.reasons)
            .where(Reasons.tg_id == tg_id)
        )

        reasons: List[str] = [f"📝<b>Reason for warn: {reason}</b>" for reason in result.scalars()]
        
        if not reasons:
            return "<b>No reasons for warns found.</b>"
        return "\n".join(reasons)  


async def delete_user_reason(tg_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            subquery = select(Reasons.id).where(Reasons.tg_id == tg_id).order_by(Reasons.id.desc()).limit(1).scalar_subquery()
            await session.execute(
                delete(Reasons)
                .where(Reasons.id == subquery)
            )


async def delete_user_reasons(tg_id: int) -> None:
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                delete(Reasons)
                .where(Reasons.tg_id == tg_id) 
            )


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
                update(Warns)
                .where(Warns.tg_id == user_id)
                .values(warns=0)
            )


async def check_warns(user_id: int) -> int:
    async with async_session() as session:
        result: Result[tuple[int]] = await session.execute(
            select(Warns.warns)
            .where(Warns.tg_id == user_id)
        )

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
