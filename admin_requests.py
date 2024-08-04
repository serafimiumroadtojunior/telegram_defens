from sqlalchemy.future import select
from models import async_session, User

# Функция для добавления предупреждений
async def add_warn(user_id: int) -> int:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.tg_id == user_id))
            user = result.scalars().first()
            if user:
                user.warns += 1
            await session.commit()
            return user.warns

# Функция для сброса предупреждений
async def reset_warns(user_id: int):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.tg_id == user_id))
            user = result.scalars().first()
            if user:
                user.warns = 0
            await session.commit()

# Функция для проверки количества предупреждений
async def check_warns(user_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalars().first()
        return user.warns if user else 0

# Функция для добавления нового пользователя
async def add_user(tg_id: int):
    async with async_session() as session:
        async with session.begin():
            user = User(tg_id=tg_id)
            session.add(user)
            await session.commit()
            print(f"User with tg_id {tg_id} created.")

# Проверка существования пользователя
async def check_user(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalars().first()  # Извлекаем первый результат, если есть

        if user is None:
            await add_user(tg_id=tg_id)  # Добавляем пользователя, если не найден
        else:
            print(f"User with tg_id {tg_id} already exists.")