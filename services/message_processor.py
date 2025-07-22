from models import get_model_llm
from database import save_message, get_wellness_progress
from utils.logger import logger
from safety.filters import crisis_redirect, safety_filter
from context_builder import build_context
from services.wellness_check import handle_wellness_check


async def run_wellness_check_flow(user_id, session_id, user_message: str):
    try:
        wellness_reply = await handle_wellness_check(user_id, user_message)
        if wellness_reply:
            if user_message.strip():
                await save_message(user_id, session_id, "user", user_message)
            await save_message(user_id, session_id, "assistant", wellness_reply)
        return wellness_reply
    except Exception as e:
        logger.error(f"run_wellness_check_flow failed for user {user_id}: {e}", exc_info=True)
        return "Sorry, there was an error during the wellness check-in."


async def should_trigger_wellness_check(user_id: str, user_message: str, trigger: bool = False) -> bool:
    try:
        if trigger:
            return True

        if not user_message.strip():
            return True

        progress = await get_wellness_progress(user_id)
        if progress:
            return True

        return False
    except Exception as e:
        logger.error(f"should_trigger_wellness_check error for user {user_id}: {e}", exc_info=True)
        return False


async def process_user_message(user_id, session_id, user_message, mode="cbt", job="supporter", trigger_wellness=False):
    # Crisis check
    crisis_msg = crisis_redirect(user_message)
    if crisis_msg:
        await save_message(user_id, session_id, "user", user_message)
        await save_message(user_id, session_id, "assistant", crisis_msg)
        return crisis_msg

    try:
        if await should_trigger_wellness_check(user_id, user_message, trigger_wellness):
            return await run_wellness_check_flow(user_id, session_id, user_message)
    except Exception as e:
        logger.error(f"Wellness check triggering failed for user {user_id}: {e}", exc_info=True)

    # Otherwise, fallback to main LLM conversation
    try:
        context_prompt = await build_context(user_id, session_id, user_message, mode, job)
        llm = await get_model_llm()

        response = await llm.ainvoke(context_prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        final_response = safety_filter(response_text)

        await save_message(user_id, session_id, "user", user_message)
        await save_message(user_id, session_id, "assistant", final_response)

        return final_response

    except Exception as e:
        logger.error(f"LLM call failed for user {user_id}: {e}", exc_info=True)
        error_msg = "Sorry, there was an error processing your request. Please try again."
        await save_message(user_id, session_id, "assistant", error_msg)
        return error_msg
