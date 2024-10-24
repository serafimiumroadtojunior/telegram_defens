from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import and_, delete, func, select, Result
from sqlalchemy.dialects.postgresql import insert

from ..models import AntiSpam
from ..session import async_session


async def add_message(user_id: int) -> None:
    date_range: datetime = datetime.now() - timedelta(seconds=10)

    async with async_session() as session:
        async with session.begin():
            await session.execute(
                delete(AntiSpam).where(and_(
                    AntiSpam.user_id == user_id,
                    AntiSpam.created_at <= date_range
                    )
                )
            )

            await session.execute(
                insert(AntiSpam)
                .values(user_id=user_id)
            )


async def count_messages(user_id: int) -> int:
    async with async_session() as session:
        result: Result[Tuple[int]] = await session.execute(
            select(func.count(AntiSpam.id))
            .where(AntiSpam.user_id == user_id)
        )

        counts: Optional[int] = result.scalar()

        return counts if counts else 0