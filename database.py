import asyncpg
import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def get_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}", exc_info=True)
        raise


async def save_message(user_id: str, session_id: str, role: str, message: str):
    conn = None
    try:
        conn = await get_db()
        await conn.execute(
            "INSERT INTO chat_history (user_id, session_id, role, message) VALUES ($1, $2, $3, $4)",
            user_id, session_id, role, message
        )
    except Exception as e:
        logger.error(f"Error saving message for user_id {user_id}: {e}", exc_info=True)
    finally:
        if conn:
            await conn.close()


async def get_messages(user_id: str, session_id: str, limit: int = 20):
    conn = None
    try:
        conn = await get_db()
        rows = await conn.fetch(
            """
            SELECT role, message 
            FROM chat_history 
            WHERE user_id = $1 AND session_id = $2 
            ORDER BY created_at DESC 
            LIMIT $3
            """,
            user_id, session_id, limit
        )
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching messages for user_id {user_id}, session_id {session_id}: {e}", exc_info=True)
        return []
    finally:
        if conn:
            await conn.close()


async def get_messages_by_user_id(user_id: str, limit: int = 50):
    conn = await get_db()
    try:
        rows = await conn.fetch(
            """
            SELECT role, message, created_at AS timestamp
            FROM chat_history
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id, limit
        )
        return rows
    except Exception as e:
        logger.exception(f"Error fetching messages for user_id {user_id}: {e}")
        return []
    finally:
        await conn.close()



async def get_long_term_note(user_id: str):
    conn = None
    try:
        conn = await get_db()
        row = await conn.fetchrow(
            "SELECT memory, last_interaction_at FROM long_term_memory WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
            user_id
        )
        if row:
            return {"memory": row["memory"], "last_interaction_at": row["last_interaction_at"]}
        return None
    except Exception as e:
        logger.error(f"Error fetching long term note for user_id {user_id}: {e}", exc_info=True)
        return None
    finally:
        if conn:
            await conn.close()


async def save_long_term_note(user_id: str, memory: str, last_interaction_at):
    conn = None
    try:
        conn = await get_db()
        await conn.execute(
            """
            INSERT INTO long_term_memory (user_id, memory, last_interaction_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE
            SET memory = EXCLUDED.memory,
                last_interaction_at = EXCLUDED.last_interaction_at,
                created_at = NOW()
            """,
            user_id, memory, last_interaction_at
        )
    except Exception as e:
        logger.error(f"Error saving long term note for user_id {user_id}: {e}", exc_info=True)
    finally:
        if conn:
            await conn.close()


async def save_wellness_data(user_id, data: dict):
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    await conn.execute("""
        INSERT INTO wellness_checkins (user_id, sleep_quality, mood, healthy_eating, physical_activity)
        VALUES ($1, $2, $3, $4, $5)
    """, user_id, data.get("sleep_quality"), data.get("mood"), data.get("healthy_eating"), data.get("physical_activity"))
    await conn.close()