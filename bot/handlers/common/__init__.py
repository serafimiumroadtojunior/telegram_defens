from typing import List

from aiogram import Router

from .common_handlers import common_router


def setup_common_router(router: Router) -> None:
    router.include_router(common_router)

__all__: List[str] = ["setup_common_router"]