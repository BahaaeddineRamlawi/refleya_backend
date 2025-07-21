from database import get_messages
from utils.logger import logger

async def get_short_term_history(user_id: str, session_id: str, interactions_limit: int = 5) -> list[tuple[str, str]]:
    logger.info(f"[Short-term memory] Fetching messages for user_id: {user_id}, session_id: {session_id}")
    
    messages = await get_messages(user_id, session_id, limit=interactions_limit * 2)
    messages = list(reversed(messages))

    history = []
    user_msg = None

    for msg in messages:
        if msg['role'] == "user":
            user_msg = msg['message']
        elif msg['role'] == "assistant" and user_msg is not None:
            history.append((user_msg, msg['message']))
            user_msg = None

    return history

def format_short_term_history(history_pairs):
    lines = []
    for user_msg, assistant_msg in history_pairs:
        lines.append(f"User: {user_msg}")
        lines.append(f"Assistant: {assistant_msg}")
    return "\n".join(lines)

