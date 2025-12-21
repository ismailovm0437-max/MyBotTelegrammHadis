__all__ = ("router")
from aiogram import Router
from.comand_hadis import router as command_hadis_router
router=Router(name=__name__)
router.include_router(command_hadis_router)