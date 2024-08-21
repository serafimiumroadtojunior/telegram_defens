from sqlalchemy.future import select
from sqlalchemy import update, and_, insert

from models import async_session, User

async def add_user(tg_id: int):
    """
    Функция для добавления нового пользователя по айди
    :param tg_id: Айди юзера
    """
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                insert(User)
                .values(tg_id=tg_id)
                .prefix_with("OR IGNORE"))
       
            
async def add_warn(user_id: int):
    """
    Функция для выдачи варна юзеру по айди
    :param user_id: Айди юзера
    :return: Количество варнов у юзера
    """
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(User)
                .where(and_(User.tg_id == user_id, User.warns < 3))
                .values(warns = User.warns + 1))


async def reset_warns(user_id: int):
    """
    Функция для сброса варнов у юзера по айди.
    :param user_id: Айди юзера.
    """
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(User)
                .where(User.tg_id == user_id)
                .values(warns=0))


async def check_warns(user_id: int) -> int:
    """
    Функция для проверки количества варнов у юзера по айди
    :param user_id: Айди юзера
    :return: Количество варнов у юзера
    """
    async with async_session() as session:
        result = await session.execute(
            select(User.warns)
            .where(User.tg_id == user_id))
        
        warns = result.scalar()
        return warns


async def del_warn(tg_id: int):
    """
    Функция для удаления варна у юзера по айди
    :param tg_id: Айди юзера
    """
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(User)
                .where(and_(User.tg_id == tg_id, User.warns > 0))
                .values(warns=User.warns - 1))
