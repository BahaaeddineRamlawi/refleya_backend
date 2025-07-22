import asyncpg
import os
from dotenv import load_dotenv
from datetime import date
from utils.logger import logger
from config.wellness_constants import WELLNESS_QUESTIONS

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


async def get_db():
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}", exc_info=True)
        raise


async def has_checked_in_today(user_id: str) -> bool:
    conn = await get_db()
    try:
        result = await conn.fetchrow(
            "SELECT 1 FROM wellness_checkins WHERE user_id = $1 AND checkin_date = CURRENT_DATE",
            user_id
        )
        return result is not None
    finally:
        await conn.close()


async def has_all_answers_today(user_id: str) -> bool:
    conn = await get_db()
    try:
        result = await conn.fetchrow("""
            SELECT sleep_quality, mood, healthy_eating, physical_activity
            FROM wellness_checkins
            WHERE user_id = $1 AND checkin_date = CURRENT_DATE
        """, user_id)
        
        if not result:
            return False

        return all(result[field] and str(result[field]).strip() != "" for field, _ in WELLNESS_QUESTIONS)
    finally:
        await conn.close()


async def get_wellness_progress(user_id: str):
    conn = await get_db()
    try:
        return await conn.fetchrow("""
            SELECT current_question_index
            FROM wellness_checkin_progress 
            WHERE user_id = $1
        """, user_id)
    except Exception as e:
        logger.error(f"Error fetching wellness progress for user_id {user_id}: {e}", exc_info=True)
        return None
    finally:
        await conn.close()


async def ensure_wellness_progress_exists(user_id: str):
    progress = await get_wellness_progress(user_id)
    if progress:
        return

    conn = await get_db()
    try:
        await conn.execute("""
            INSERT INTO wellness_checkin_progress (user_id, current_question_index, last_prompted)
            VALUES ($1, 0, $2)
        """, user_id, date.today())
    except Exception as e:
        logger.error(f"Error ensuring wellness progress for user_id {user_id}: {e}", exc_info=True)
        raise
    finally:
        await conn.close()


async def update_wellness_progress(user_id: str, current_index: int):
    conn = await get_db()
    try:
        await conn.execute("""
            UPDATE wellness_checkin_progress 
            SET current_question_index = $1, last_prompted = CURRENT_DATE 
            WHERE user_id = $2
        """, current_index, user_id)
    finally:
        await conn.close()


async def delete_wellness_progress(user_id: str):
    conn = await get_db()
    try:
        await conn.execute("DELETE FROM wellness_checkin_progress WHERE user_id = $1", user_id)
    finally:
        await conn.close()


async def save_wellness_data(user_id: str, data: dict):
    conn = await get_db()
    try:
        await conn.execute("""
            INSERT INTO wellness_checkins (user_id, sleep_quality, mood, healthy_eating, physical_activity)
            VALUES ($1, $2, $3, $4, $5)
        """, user_id, data.get("sleep_quality"), data.get("mood"), data.get("healthy_eating"), data.get("physical_activity"))
    finally:
        await conn.close()


async def save_wellness_field_answer(user_id: str, field: str, answer: str):
    conn = await get_db()
    try:
        await conn.execute(f"""
            INSERT INTO wellness_checkins (user_id, checkin_date, {field})
            VALUES ($1, CURRENT_DATE, $2)
            ON CONFLICT (user_id, checkin_date)
            DO UPDATE SET {field} = EXCLUDED.{field}
        """, user_id, answer)
    finally:
        await conn.close()


async def save_message(user_id: str, session_id: str, role: str, message: str):
    conn = await get_db()
    try:
        await conn.execute("""
            INSERT INTO chat_history (user_id, session_id, role, message)
            VALUES ($1, $2, $3, $4)
        """, user_id, session_id, role, message)
    except Exception as e:
        logger.error(f"Error saving message for user_id {user_id}: {e}", exc_info=True)
    finally:
        await conn.close()


async def get_messages(user_id: str, session_id: str, limit: int = 20):
    conn = await get_db()
    try:
        rows = await conn.fetch("""
            SELECT role, message 
            FROM chat_history 
            WHERE user_id = $1 AND session_id = $2 
            ORDER BY created_at DESC 
            LIMIT $3
        """, user_id, session_id, limit)
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching messages for user_id {user_id}, session_id {session_id}: {e}", exc_info=True)
        return []
    finally:
        await conn.close()


async def get_messages_by_user_id(user_id: str, limit: int = 50):
    conn = await get_db()
    try:
        return await conn.fetch("""
            SELECT role, message, created_at AS timestamp
            FROM chat_history
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, user_id, limit)
    except Exception as e:
        logger.error(f"Error fetching messages for user_id {user_id}: {e}", exc_info=True)
        return []
    finally:
        await conn.close()


async def get_long_term_note(user_id: str):
    conn = await get_db()
    try:
        row = await conn.fetchrow("""
            SELECT memory, last_interaction_at 
            FROM long_term_memory 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT 1
        """, user_id)
        if row:
            return {"memory": row["memory"], "last_interaction_at": row["last_interaction_at"]}
        return None
    except Exception as e:
        logger.error(f"Error fetching long term note for user_id {user_id}: {e}", exc_info=True)
        return None
    finally:
        await conn.close()


async def save_long_term_note(user_id: str, memory: str, last_interaction_at):
    conn = await get_db()
    try:
        await conn.execute("""
            INSERT INTO long_term_memory (user_id, memory, last_interaction_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE
            SET memory = EXCLUDED.memory,
                last_interaction_at = EXCLUDED.last_interaction_at,
                created_at = NOW()
        """, user_id, memory, last_interaction_at)
    except Exception as e:
        logger.error(f"Error saving long term note for user_id {user_id}: {e}", exc_info=True)
    finally:
        await conn.close()
