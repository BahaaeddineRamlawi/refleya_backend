from models import get_model_llm
from database import save_message
from utils.logger import logger
from safety.filters import crisis_redirect, safety_filter
from context_builder import build_context

async def process_user_message(user_id, session_id, user_message, mode="cbt", job="supporter"):

    crisis_msg = crisis_redirect(user_message)
    if crisis_msg:
        await save_message(user_id, session_id, "user", user_message)
        await save_message(user_id, session_id, "assistant", crisis_msg)
        return crisis_msg

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
