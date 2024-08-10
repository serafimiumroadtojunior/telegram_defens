from sqlalchemy.future import select

from models import async_session, User

async def add_warn(user_id: int) -> int:
    """
    Функция для выдачи варна юзеру по айди
    :param user_id: Айди юзера
    :return: Количество варнов у юзера
    """
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.tg_id == user_id))
            user = result.scalars().first()
            if user:
                user.warns += 1
            await session.commit()

async def reset_warns(user_id: int):
    """
    Функция для сброса варнов у юзера по айди
    :param user_id: Айди юзера
    """
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.tg_id == user_id))
            user = result.scalars().first()
            if user:
                user.warns = 0
            await session.commit()

async def check_warns(user_id: int) -> int:
    """
    Функция для проверки количества варнов у юзера по айди
    :param user_id: Айди юзера
    :return: Количество варнов у юзера
    """
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalars().first()
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
            await session.commit()

async def check_user(tg_id: int):
    """
    Функция для проверки существования пользователя по айди
    :param tg_id: Айди юзера
    """
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalars().first()  

        if user is None:
            await add_user(tg_id=tg_id)

async def del_warn(tg_id: int):
    """
    Функция для удаления варна у юзера по айди
    :param tg_id: Айди юзера
    """
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.tg_id == tg_id))
            user = result.scalars().first()
            if user.warns > 0:
                user.warns -= 1
            await session.commit()
