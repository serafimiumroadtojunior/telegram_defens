from sqlalchemy.future import select
from sqlalchemy import update

from models import async_session, User

async def add_warn(user_id: int):
    """
    Функция для выдачи варна юзеру по айди
    :param user_id: Айди юзера
    :return: Количество варнов у юзера
    """
    async with async_session() as session:
        async with session.begin():
            await session.execute(update(User).where(User.tg_id == user_id).values(warns = User.warns + 1))

async def reset_warns(user_id: int):
    """
    Функция для сброса варнов у юзера по айди.
    :param user_id: Айди юзера.
    """
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(User).where(User.tg_id == user_id).values(warns=0)
            )

async def check_warns(user_id: int) -> int:
    """
    Функция для проверки количества варнов у юзера по айди
    :param user_id: Айди юзера
    :return: Количество варнов у юзера
    """
    async with async_session() as session:
        warn = await session.execute(select(User).where(User.tg_id == user_id))
        user = warn.scalar_one()
        return user.warns if user else 0

async def add_user(tg_id: int):
    """
    Функция для добавления нового пользователя по айди
    :param tg_id: Айди юзера
    """
    async with async_session() as session:
        async with session.begin():
            user = User(tg_id=tg_id)
            session.add(user)

async def check_user(tg_id: int):
    """
    Функция для проверки существования пользователя по айди
    :param tg_id: Айди юзера
    """
    async with async_session() as session:
        check = await session.execute(select(User).where(User.tg_id == tg_id))
        user = check.scalar_one_or_none()

        if user is None:
            await add_user(tg_id=tg_id)

async def del_warn(tg_id: int):
    """
    Функция для удаления варна у юзера по айди
    :param tg_id: Айди юзера
    """
    async with async_session() as session:
        async with session.begin():
            check_warn = await session.execute(select(User.warns).where(User.tg_id == tg_id))
            current_warns = check_warn.scalar_one_or_none()
            
            if current_warns is not None and current_warns > 0:
                await session.execute(
                    update(User)
                    .where(User.tg_id == tg_id)
                    .values(warns=User.warns - 1)
                )
