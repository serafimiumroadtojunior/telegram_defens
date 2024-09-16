from sqlalchemy.future import select
from sqlalchemy import update, and_, insert

from models import async_session, User

async def add_user(tg_id: int):
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                insert(User)
                .values(tg_id=tg_id)
                .prefix_with("OR IGNORE"))
       
            
async def add_warn(user_id: int):
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(User)
                .where(and_(User.tg_id == user_id, User.warns < 3))
                .values(warns = User.warns + 1))


async def reset_warns(user_id: int):
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(User)
                .where(User.tg_id == user_id)
                .values(warns=0))


async def check_warns(user_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(User.warns)
            .where(User.tg_id == user_id))
        
        warns = result.scalar_one_or_none()
        return warns if warns else 0


async def del_warn(tg_id: int):
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(User)
                .where(and_(User.tg_id == tg_id, User.warns > 0))
                .values(warns=User.warns - 1))
