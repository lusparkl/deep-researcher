import asyncio
import logging
import os

import psycopg
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import BufferedInputFile, Message
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver

from app.research.models import renumber_report_citations


load_dotenv()

logger = logging.getLogger(__name__)
dp = Dispatcher()

DAILY_LIMIT_TABLE = """
    CREATE TABLE IF NOT EXISTS telegram_daily_research_limits (
        telegram_user_id BIGINT NOT NULL,
        research_date DATE NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (telegram_user_id, research_date)
    )
"""


def get_settings() -> tuple[str, str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    database_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL")

    missing = [
        name
        for name in ("TELEGRAM_BOT_TOKEN", "HACK_AI_API_KEY", "OPENAI_API_KEY", "EXA_API_KEY")
        if not os.getenv(name)
    ]
    if not database_url:
        missing.append("DB_URL or DATABASE_URL")

    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return token, database_url


def initialize_database(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(DAILY_LIMIT_TABLE)

    with PostgresSaver.from_conn_string(database_url) as checkpointer:
        checkpointer.setup()


def reserve_daily_research(user_id: int, database_url: str) -> bool:
    with psycopg.connect(database_url) as connection:
        result = connection.execute(
            """
            INSERT INTO telegram_daily_research_limits (telegram_user_id, research_date)
            VALUES (%s, (NOW() AT TIME ZONE 'UTC')::date)
            ON CONFLICT DO NOTHING
            RETURNING research_date
            """,
            (user_id,),
        ).fetchone()

    return result is not None


def release_daily_research(user_id: int, database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            DELETE FROM telegram_daily_research_limits
            WHERE telegram_user_id = %s
              AND research_date = (NOW() AT TIME ZONE 'UTC')::date
            """,
            (user_id,),
        )


def assign_topic(user_id: int, text: str, database_url: str) -> dict:
    from app.research.graphs import topic_assignment_builder

    with PostgresSaver.from_conn_string(database_url) as checkpointer:
        topic_graph = topic_assignment_builder.compile(checkpointer=checkpointer)
        return topic_graph.invoke(
            {"messages": [text]},
            {"configurable": {"thread_id": str(user_id)}},
        )


def clear_topic_history(user_id: int, database_url: str) -> None:
    with PostgresSaver.from_conn_string(database_url) as checkpointer:
        checkpointer.delete_thread(str(user_id))


def run_research(topic: str) -> dict:
    from app.research.graphs import graph

    return graph.invoke({"topic": topic})


def create_research_file(research: dict) -> BufferedInputFile:
    introduction, report_body, conclusion, sources = renumber_report_citations(
        research["introduction"].strip(),
        research["report_body"].strip(),
        research["conclusion"].strip(),
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
    return BufferedInputFile(
        file=research_text.encode("utf-8"),
        filename="research_report.md",
    )


@dp.message(CommandStart())
async def start_the_bot(message: Message) -> None:
    await message.answer(
        "Hello there! I'm an interactive AI research assistant. Send me a topic, "
        "and I'll return a Markdown file containing the research report."
    )


@dp.message()
async def start_research_handler(message: Message, database_url: str) -> None:
    if not message.text:
        await message.answer("Please send your research topic as text.")
        return

    user_id = message.from_user.id if message.from_user else message.chat.id
    slot_reserved = False

    try:
        topic_result = await asyncio.to_thread(
            assign_topic,
            user_id,
            message.text,
            database_url,
        )

        topic = topic_result.get("topic")
        if not topic:
            clarification = topic_result.get("clarification") or (
                "Please provide a little more detail about what you want to research."
            )
            await message.answer(clarification)
            return

        slot_reserved = await asyncio.to_thread(
            reserve_daily_research,
            user_id,
            database_url,
        )
        await asyncio.to_thread(clear_topic_history, user_id, database_url)

        if not slot_reserved:
            await message.answer(
                "You have already started one research today. Please try again tomorrow. "
                "The daily limit resets at midnight UTC."
            )
            return

        await message.answer("Starting your research, please wait.")
        research = await asyncio.to_thread(run_research, topic)
        await message.answer_document(
            document=create_research_file(research),
            caption="Your research is ready.",
        )
    except Exception:
        logger.exception("Research failed for Telegram user %s", user_id)

        slot_released = False
        if slot_reserved:
            try:
                await asyncio.to_thread(
                    release_daily_research,
                    user_id,
                    database_url,
                )
                slot_released = True
            except Exception:
                logger.exception("Could not restore the daily slot for user %s", user_id)

        retry_note = (
            " Your daily research slot was restored, so you can try again."
            if slot_released
            else " Please try again later."
        )
        await message.answer(f"Sorry, the research could not be completed.{retry_note}")


async def main() -> None:
    token, database_url = get_settings()
    await asyncio.to_thread(initialize_database, database_url)

    async with Bot(token=token) as bot:
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot, database_url=database_url)
