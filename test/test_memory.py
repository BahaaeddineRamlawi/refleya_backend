import asyncio
import uuid
from database import save_message
from memory.short_term import get_short_term_history
from utils.logger import logger

async def test_memory():
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    messages = [
        ("user", "Hello, I feel overwhelmed."),
        ("assistant", "Can you tell me more about what's overwhelming you?"),
        ("user", "Work and personal life are colliding."),
        ("assistant", "Let’s take a deep breath and unpack it one step at a time.")
    ]

    for role, msg in messages:
        await save_message(user_id, session_id, role, msg)

    history = await get_short_term_history(session_id)
    logger.info("--- Short-Term History ---")
    logger.info(history)


asyncio.run(test_memory())

