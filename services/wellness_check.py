from database import (
    get_wellness_progress,
    has_all_answers_today,
    save_wellness_field_answer,
    update_wellness_progress,
    delete_wellness_progress
)
from models import get_model_llm
from utils.logger import logger
from config.wellness_constants import WELLNESS_QUESTIONS


async def rephrase_question(field: str, base_question: str) -> str:
    try:
        llm = await get_model_llm()
        prompt = (
            f"You're a friendly wellness coach. Rephrase the following question in a natural, slightly different way. "
            f"Make it casual and concise, but still ask about the same topic: '{field}'.\n\n"
            f"Original: {base_question}\n\n"
            f"Rephrased:"
        )
        response = await llm.ainvoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        result = text.strip().strip('"').strip("'")
        logger.debug(f"Rephrased question for '{field}': {result}")
        return result
    except Exception as e:
        logger.error(f"Error rephrasing question for field '{field}': {e}", exc_info=True)
        return base_question  # Fallback to original


async def extract_answer_from_input(user_message: str, field: str) -> str | None:
    try:
        llm = await get_model_llm()
        prompt = (
            f"You are helping log a user's daily wellness check-in.\n"
            f"Your job is to extract a **concise answer** (e.g., 'good', 'bad', 'yes', 'no', 'I ate well') "
            f"that corresponds to the wellness field: '{field}'.\n"
            f"If you can't find any meaningful answer, return an empty string.\n\n"
            f"Examples:\n"
            f"Field: mood | Input: 'I'm feeling okay today' | Answer: 'okay'\n"
            f"Field: sleep_quality | Input: 'I slept well, thank you' | Answer: 'slept well'\n"
            f"\nNow:\nUser: {user_message}\nAnswer:"
        )
        response = await llm.ainvoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        text = text.strip()

        logger.debug(f"Extracted answer for '{field}': '{text}' (raw response)")

        if not text or text.lower() in ["none", "no", "n/a", ""]:
            return None
        return text
    except Exception as e:
        logger.error(f"Error extracting answer from input '{user_message}' for field '{field}': {e}", exc_info=True)
        return None


async def handle_wellness_check(user_id: str, user_input: str = "") -> str | None:
    try:
        if await has_all_answers_today(user_id):
            if not user_input.strip():
                return "You've already completed today's wellness check-in. 🎉"
            return None

        progress = await get_wellness_progress(user_id)
        if not progress:
            return None

        current_index = progress["current_question_index"]
        field, question_text = WELLNESS_QUESTIONS[current_index]

        if not user_input.strip():
            rephrased_question = await rephrase_question(field, question_text)
            return rephrased_question

        # Extract and store answer
        # answer = await extract_answer_from_input(user_input, field)
        # if not answer:
        #     return "I couldn't quite understand your response. Could you please answer the question again?"

        await save_wellness_field_answer(user_id, field, user_input)
        current_index += 1

        if current_index >= len(WELLNESS_QUESTIONS):
            await delete_wellness_progress(user_id)
            return "Thanks! You've completed today's wellness check-in. 😊"

        await update_wellness_progress(user_id, current_index)
        _, next_base_question = WELLNESS_QUESTIONS[current_index]
        rephrased_next = await rephrase_question(WELLNESS_QUESTIONS[current_index][0], next_base_question)
        return rephrased_next

    except Exception as e:
        logger.error(f"Wellness check error for user {user_id}: {e}", exc_info=True)
        return None
