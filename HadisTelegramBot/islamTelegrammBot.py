
import asyncio
import os
import logging
import requests
from aiogram import Bot, Router  # !ВСЕ ИМОПРТЫ ЗДЕСЬ
from aiogram import Dispatcher
from aiogram import types
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv
from router import router as main_router

router = Router()
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
dp.include_router(main_router)


@dp.message(CommandStart())
async def command_start(message: types.Message):
    await message.answer(
        text="Ассаляму Алейкум \n Здесь вы можете изучать хадисы \n Аль-Бухари"
    )


async def main():  # !======================================================
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)  # !БАЗА ДЛЯ ЗАПУСКА ЦИКЛА
if __name__ == "__main__":
    asyncio.run(main())
    # !================================================================
