from typing import List

from aiogram import Dispatcher, Router

from .admin import setup_admin_router
from .common import setup_common_router
from .user import setup_user_router


def setup_routers(dispatcher: Dispatcher) -> None:
    main_router: Router = Router()
    setup_admin_router(router=main_router)
    setup_user_router(router=main_router)
    setup_common_router(router=main_router)
    dispatcher.include_router(main_router)

__all__: List[str] = ["setup_routers"]