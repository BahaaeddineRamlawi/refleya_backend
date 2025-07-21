import asyncio
from memory.short_term import get_short_term_history, format_short_term_history
from utils.logger import logger

async def test_get_short_term(user_id: str, session_id: str, limit: int = 5):
    try:
        logger.info(f"Fetching short-term memory for user_id: {user_id}, session_id: {session_id}")
        history_pairs = await get_short_term_history(user_id, session_id, interactions_limit=limit)

        if history_pairs:
            logger.info("Short-term memory history retrieved successfully.")
            print("\n--- Short Term Memory ---\n")
            print(format_short_term_history(history_pairs))
        else:
            logger.warning("No short-term memory found for this session.")
    
    except Exception as e:
        logger.exception(f"Error while fetching short-term memory: {e}")

if __name__ == "__main__":
    user_id = "f1a09f41-b1e7-4fcd-b869-95cf12434ed0"
    session_id = "1ee601de-4c44-4218-ba49-3d70d0cabf04"
    asyncio.run(test_get_short_term(user_id, session_id))
