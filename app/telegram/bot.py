from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, BufferedInputFile
from dotenv import load_dotenv
from os import getenv
import asyncio
from langgraph.checkpoint.postgres import PostgresSaver
from app.research.graphs import topic_assignment_builder, graph


load_dotenv()
TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")
DB_URL = getenv("DB_URL")

dp = Dispatcher()

@dp.message(CommandStart())
async def start_the_bot(message: Message) -> None:
    await message.answer("Hello there! I'm and interactive AI research assistant. You can message me any topic and I'll answer with .md file that contains your research about this topic!")

@dp.message()
async def start_research_handler(message: Message) -> None:
    with PostgresSaver.from_conn_string(DB_URL) as checkpointer:
        checkpointer.setup()
        topic_graph = topic_assignment_builder.compile(checkpointer)
        result = topic_graph.invoke({"messages": [message.text], "message": message}, {"configurable": {"thread_id": message.from_user.id}})

        if not result["topic"]:
            await message.answer(result["clarification"])
            return
        
        await message.answer("Starting your research, please wait.")
        checkpointer.delete_thread(message.from_user.id)
        research = graph.invoke({"topic": result["topic"]})

        research_text = f"""# Research report

        ## Introduction

        {research["introduction"]}

        ## Main body

        {research["report_body"]}

        ## Conclusion

        {research["conclusion"]}
"""
        
        file = BufferedInputFile(file=research_text.encode("utf-8"), filename="research_report.md")

        await message.answer_document(document=file, caption="Your research is ready.")

async def main() -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())