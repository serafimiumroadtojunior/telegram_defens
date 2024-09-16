import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from admin_handlers import admin_router
from midlewares import (AdminCheckerMiddleware, CallbackAdminCheckerMiddleware,
                        ForbiddenWordsMiddleware, AntiFloodMiddleware)
from models import engine, Base
from other import forbidden_words


load_dotenv()

async def main():
    bot = Bot(token=os.getenv('TOKEN'))
    dp = Dispatcher()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    dp.include_router(admin_router)
    admin_router.message.middleware(AdminCheckerMiddleware(bot))
    admin_router.callback_query.middleware(CallbackAdminCheckerMiddleware(bot))
    admin_router.message.outer_middleware(ForbiddenWordsMiddleware(bot, forbidden_words))
    admin_router.message.middleware(AntiFloodMiddleware())

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped')
