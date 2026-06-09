from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
from os import getenv
import asyncio

load_dotenv()
TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")

dp = Dispatcher()

@dp.message(CommandStart())
async def start_the_bot(message: Message) -> None:
    await message.answer("Hello there! I'm and interactive AI research assistant. You can message me any topic and I'll answer with .md file that contains your research about this topic!")

@dp.message()
async def start_research_handler(message: Message) -> None:
    await message.answer(f"Allright, starting research on the \"{message.text}\" topic.")

async def main() -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())