from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, BufferedInputFile
from dotenv import load_dotenv
from os import getenv
import asyncio
import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from app.research.graphs import topic_assignment_builder, graph
from app.research.models import renumber_report_citations


load_dotenv()
TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")
DB_URL = getenv("DB_URL")

dp = Dispatcher()

def reserve_daily_research(user_id: int) -> bool:
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telegram_daily_research_limits (
                    telegram_user_id BIGINT NOT NULL,
                    research_date DATE NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (telegram_user_id, research_date)
                )
            """)
            cursor.execute("""
                INSERT INTO telegram_daily_research_limits (telegram_user_id, research_date)
                VALUES (%s, (NOW() AT TIME ZONE 'UTC')::date)
                ON CONFLICT DO NOTHING
                RETURNING research_date
            """, (user_id,))

            return cursor.fetchone() is not None

def release_daily_research(user_id: int) -> None:
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM telegram_daily_research_limits
                WHERE telegram_user_id = %s
                AND research_date = (NOW() AT TIME ZONE 'UTC')::date
            """, (user_id,))

@dp.message(CommandStart())
async def start_the_bot(message: Message) -> None:
    await message.answer("Hello there! I'm and interactive AI research assistant. You can message me any topic and I'll answer with .md file that contains your research about this topic!")

@dp.message()
async def start_research_handler(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id

    with PostgresSaver.from_conn_string(DB_URL) as checkpointer:
        checkpointer.setup()
        topic_graph = topic_assignment_builder.compile(checkpointer)
        result = topic_graph.invoke({"messages": [message.text], "message": message}, {"configurable": {"thread_id": user_id}})

        if not result["topic"]:
            await message.answer(result["clarification"])
            return

        if not reserve_daily_research(user_id):
            checkpointer.delete_thread(user_id)
            await message.answer("You have already started one research today. Please try again tomorrow. The daily limit resets at midnight UTC.")
            return
        
        await message.answer("Starting your research, please wait.")
        checkpointer.delete_thread(user_id)

        try:
            research = graph.invoke({"topic": result["topic"]})
        except Exception as error:
            release_daily_research(user_id)
            print(f"Research failed for user {user_id}: {type(error).__name__}: {error}")
            await message.answer("Sorry, the research failed because one of the data providers returned an error. Your daily research slot was not used, so you can try again.")
            return

        introduction = research["introduction"].strip()
        report_body = research["report_body"].strip()
        conclusion = research["conclusion"].strip()
        introduction, report_body, conclusion, sources = renumber_report_citations(
            introduction,
            report_body,
            conclusion,
            research.get("sources", []),
        )

        research_text = f"""# Research report

## Introduction

{introduction}

## Main body

{report_body}

## Conclusion

{conclusion}

## Sources

{sources}
"""
        
        file = BufferedInputFile(file=research_text.encode("utf-8"), filename="research_report.md")

        await message.answer_document(document=file, caption="Your research is ready.")

async def main() -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
