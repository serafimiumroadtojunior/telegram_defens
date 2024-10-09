from typing import List

from aiogram import Router

from .admin_handlers import admin_router


def setup_admin_router(router: Router) -> None:
    router.include_router(admin_router)

__all__: List[str] = ["setup_admin_router", 
                      "admin_router"
]