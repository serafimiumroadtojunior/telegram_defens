from typing import List

from aiogram import Router

from .user_handlers import user_router


def setup_user_router(router: Router) -> None:
    router.include_router(user_router)

__all__: List[str] = ["setup_user_router",
                      "user_router"]