import os
from dotenv import load_dotenv
from utils.logger import logger
from prompts.system_prompts import get_persona_prompt
from memory.short_term import get_short_term_history, format_short_term_history
from memory.long_term import get_long_term_history
from safety.filters import safety_filter

load_dotenv()

MAX_TOKENS = int(os.getenv("FULL_CONTEXT_MAX_TOKENS", 4000))
TOKEN_BUFFER = 200
MAX_CONTEXT_TOKENS = MAX_TOKENS - TOKEN_BUFFER
APPROX_TOKEN_CHAR_RATIO = 4
MAX_CONTEXT_CHARS = MAX_CONTEXT_TOKENS * APPROX_TOKEN_CHAR_RATIO

def approx_token_count(text: str) -> int:
    return len(text) // APPROX_TOKEN_CHAR_RATIO

async def build_context(user_id: str, session_id: str, user_message: str, mode="cbt") -> str:
    try:
        logger.info(f"Building context for user_id: {user_id}, session_id: {session_id}")

        system_prompt = get_persona_prompt(mode)
        system_part = f"System: {system_prompt.strip()}"

        # --- Short-Term Memory ---
        try:
            short_term_history = await get_short_term_history(user_id, session_id)
            formatted_short_history = format_short_term_history(short_term_history)
        except Exception as e:
            logger.error(f"Failed to load short-term memory for user_id {user_id}: {e}", exc_info=True)
            formatted_short_history = "Short-term memory unavailable."

        short_term_lines = formatted_short_history.strip().split("\n")
        short_term_part = "Conversation History:\n" + "\n".join(short_term_lines).strip()

        # --- Long-Term Memory ---
        try:
            long_term_memory = await get_long_term_history(user_id)
        except Exception as e:
            logger.error(f"Failed to load long-term memory for user_id {user_id}: {e}", exc_info=True)
            long_term_memory = "Long-term memory unavailable."

        long_term_lines = long_term_memory.strip().split("\n")
        long_term_part = "Long-term Memory:\n" + "\n".join(long_term_lines).strip()

        user_part = f"User: {user_message.strip()}"

        context_parts = [system_part, long_term_part, short_term_part, user_part]
        full_context = "\n\n".join(context_parts)

        while approx_token_count(full_context) > MAX_CONTEXT_TOKENS:
            if len(short_term_lines) > 2:
                short_term_lines = short_term_lines[:-2]
                short_term_part = "Conversation History:\n" + "\n".join(short_term_lines).strip()
            elif len(long_term_lines) > 1:
                long_term_lines = long_term_lines[:-1]
                long_term_part = "Long-term Memory:\n" + "\n".join(long_term_lines).strip()
            else:
                logger.warning("Exceeded context limit — removing long-term memory entirely.")
                long_term_part = "Long-term Memory:\n"
                context_parts = [system_part, long_term_part, short_term_part, user_part]
                full_context = "\n\n".join(context_parts)
                break

            context_parts = [system_part, long_term_part, short_term_part, user_part]
            full_context = "\n\n".join(context_parts)

        filtered_context = safety_filter(full_context)
        logger.info(f"Context built successfully for user_id: {user_id}")
        return filtered_context

    except Exception as e:
        logger.critical(f"Unexpected error while building context for user_id {user_id}: {e}", exc_info=True)
        return "An internal error occurred while building your conversation context."
