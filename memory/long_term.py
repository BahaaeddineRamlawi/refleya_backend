from database import (
    get_messages_by_user_id,
    get_long_term_note,
    save_long_term_note,
)
from dotenv import load_dotenv
import os
from models import get_model_llm
from utils.logger import logger
import datetime

load_dotenv()
LONG_TERM_MEMORY_MAX_TOKENS = int(os.getenv("LONG_TERM_MEMORY_MAX_TOKENS"))


def count_tokens(text: str) -> int:
    return len(text) // 4


async def get_user_assistant_pairs(user_id: str, limit: int = 40) -> list[dict]:
    messages = await get_messages_by_user_id(user_id, limit=limit)
    messages = list(reversed(messages))

    pairs = []
    user_msg = None

    for msg in messages:
        if msg["role"] == "user":
            user_msg = msg
        elif msg["role"] == "assistant" and user_msg:
            pairs.append({
                "user_message": user_msg["message"],
                "assistant_message": msg["message"],
                "timestamp": msg["timestamp"]
            })
            user_msg = None

    return pairs


def format_pairs(pairs: list[dict]) -> str:
    lines = []
    for pair in pairs:
        lines.append(f"User: {pair['user_message']}")
        lines.append(f"Assistant: {pair['assistant_message']}")
    return "\n".join(lines)


async def generate_history_summary(user_id: str, formatted_text: str) -> str:
    try:
        llm = await get_model_llm()
        prompt = (
            "Summarize the following conversation history to capture important events, user goals, and key facts having less that {LONG_TERM_MEMORY_MAX_TOKENS} Tokens.\n\n"
            f"{formatted_text}\n\nSummary:"
        )
        result = await llm.ainvoke(prompt)

        if hasattr(result, "content"):
            summary_text = result.content.strip()
        elif isinstance(result, dict):
            summary_text = result.get("response", "").strip()
            if not summary_text:
                for v in result.values():
                    if isinstance(v, str):
                        summary_text = v.strip()
                        break
        else:
            summary_text = str(result).strip()

        pairs = await get_user_assistant_pairs(user_id)
        last_interaction_at = pairs[-1]["timestamp"] if pairs else datetime.datetime.utcnow()

        await save_long_term_note(user_id, summary_text, last_interaction_at)
        logger.info(f"[Long-term memory] Saved summarized history for user_id: {user_id}")
        return summary_text
    except Exception as e:
        logger.error(f"[Long-term memory] Failed to summarize history for user_id {user_id}: {e}", exc_info=True)
        return formatted_text


async def get_long_term_history(user_id: str) -> str:
    try:
        logger.info(f"[Long-term memory] Fetching existing history for user_id: {user_id}")
        existing_history = await get_long_term_note(user_id)
        logger.debug(f"[Long-term memory] Existing history: {existing_history}")

        pairs = await get_user_assistant_pairs(user_id)
        logger.debug(f"[Long-term memory] Retrieved {len(pairs)} message pairs.")

        if not pairs:
            logger.warning(f"[Long-term memory] No recent interactions found for user_id: {user_id}")
            return existing_history or "No conversation history available."

        last_pair = pairs[-1]
        last_timestamp = last_pair["timestamp"]

        if existing_history and str(last_timestamp) in existing_history:
            logger.info(f"[Long-term memory] Existing history already up-to-date for user_id: {user_id}")
            return existing_history

        full_text = format_pairs(pairs)

        if count_tokens(full_text) > LONG_TERM_MEMORY_MAX_TOKENS:
            logger.info(f"[Long-term memory] History too large, summarizing again for user_id: {user_id}")
            return await generate_history_summary(user_id, full_text)
        else:
            await save_long_term_note(user_id, full_text, last_timestamp)
            logger.info(f"[Long-term memory] Updated full history for user_id: {user_id}")
            return full_text

    except Exception as e:
        logger.error(f"[Long-term memory] Failed to load or update history for user_id {user_id}: {e}", exc_info=True)
        return "Long-term memory is temporarily unavailable."
