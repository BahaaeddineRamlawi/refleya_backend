import asyncio
from memory.long_term import get_long_term_history
from utils.logger import logger

async def test_get_long_term(user_id: str):
    try:
        logger.info(f"Fetching long-term memory for user_id: {user_id}")
        summary = await get_long_term_history(user_id)
        
        if summary:
            logger.info("Long-term memory summary retrieved successfully.")
            print("\n--- Long Term Memory ---\n")
            print(summary)
        else:
            logger.warning("No long-term memory found for this user.")
    
    except Exception as e:
        logger.exception(f"Error while fetching long-term memory: {e}")

if __name__ == "__main__":
    user_id = "test_user_1"
    asyncio.run(test_get_long_term(user_id))
