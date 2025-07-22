from models import get_model_llm
from database import save_message
from utils.logger import logger
from safety.filters import crisis_redirect, safety_filter
from context_builder import build_context
from services.wellness_check import handle_wellness_check, has_all_answers_today

async def run_wellness_check_flow(user_id, session_id, user_message: str):
    wellness_reply = await handle_wellness_check(user_id, user_message)
    if wellness_reply:
        if user_message.strip():
            await save_message(user_id, session_id, "user", user_message)
        await save_message(user_id, session_id, "assistant", wellness_reply)
    return wellness_reply

async def process_user_message(user_id, session_id, user_message, mode="cbt", job="supporter", trigger_wellness=False):
    # Crisis check
    crisis_msg = crisis_redirect(user_message)
    if crisis_msg:
        await save_message(user_id, session_id, "user", user_message)
        await save_message(user_id, session_id, "assistant", crisis_msg)
        return crisis_msg

    # Trigger wellness check based on flag or missing answers
    if trigger_wellness or not await has_all_answers_today(user_id) or not user_message.strip():
        return await run_wellness_check_flow(user_id, session_id, user_message)

    # Otherwise, fallback to main LLM conversation
    context_prompt = await build_context(user_id, session_id, user_message, mode, job)
    llm = await get_model_llm()

    try:
        response = await llm.ainvoke(context_prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        final_response = safety_filter(response_text)

        await save_message(user_id, session_id, "user", user_message)
        await save_message(user_id, session_id, "assistant", final_response)

        return final_response

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        error_msg = "Sorry, there was an error processing your request. Please try again."
        await save_message(user_id, session_id, "assistant", error_msg)
        return error_msg
