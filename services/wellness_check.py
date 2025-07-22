from datetime import date
from database import get_db
from models import get_model_llm
from utils.logger import logger

WELLNESS_QUESTIONS = [
    ("sleep_quality", "How well did you sleep last night?"),
    ("mood", "How was your mood today?"),
    ("healthy_eating", "Did you eat healthy today?"),
    ("physical_activity", "Did you do any physical activity today?")
]

async def rephrase_question(field: str, base_question: str) -> str:
    llm = await get_model_llm()
    prompt = (
        f"You're a friendly wellness coach. Rephrase the following question in a natural, slightly different way. "
        f"Make it casual and concise, but still ask about the same topic: '{field}'.\n\n"
        f"Original: {base_question}\n\n"
        f"Rephrased:"
    )
    response = await llm.ainvoke(prompt)
    text = response.content if hasattr(response, "content") else str(response)
    return text.strip().strip('"').strip("'")


async def has_checked_in_today(user_id: str) -> bool:
    conn = await get_db()
    try:
        result = await conn.fetchrow(
            "SELECT 1 FROM wellness_checkins WHERE user_id = $1 AND checkin_date = CURRENT_DATE",
            user_id
        )
        return result is not None
    finally:
        await conn.close()

async def has_all_answers_today(user_id: str) -> bool:
    conn = await get_db()
    try:
        result = await conn.fetchrow("""
            SELECT sleep_quality, mood, healthy_eating, physical_activity
            FROM wellness_checkins
            WHERE user_id = $1 AND checkin_date = CURRENT_DATE
        """, user_id)

        if not result:
            return False

        return all(result[field] and str(result[field]).strip() != "" for field, _ in WELLNESS_QUESTIONS)

    finally:
        await conn.close()

async def extract_answer_from_input(user_message: str, field: str) -> str | None:
    llm = await get_model_llm()
    prompt = (
        f"You're helping log a user's daily wellness check-in.\n"
        f"Extract a short answer (one phrase or sentence) related to the field '{field}' "
        f"from the user input below. If nothing clear is found, respond with an empty string.\n\n"
        f"User: {user_message}\n\nAnswer:"
    )
    response = await llm.ainvoke(prompt)
    text = response.content if hasattr(response, "content") else str(response)
    text = text.strip()
    if not text or text.lower() in ["none", "no", "n/a", ""]:
        return None
    return text

async def handle_wellness_check(user_id: str, user_input: str = "") -> str | None:
    conn = await get_db()

    try:
        if await has_all_answers_today(user_id):
            if not user_input.strip():
                return "You've already completed today's wellness check-in. 🎉"
            return None  # Allow normal conversation to continue


        # 2. Get or initialize progress
        progress = await conn.fetchrow("""
            SELECT current_question_index, last_prompted 
            FROM wellness_checkin_progress 
            WHERE user_id = $1
        """, user_id)

        if not progress or progress["last_prompted"] != date.today():
            # First interaction of the day: reset
            await conn.execute("""
                INSERT INTO wellness_checkin_progress (user_id, current_question_index, last_prompted)
                VALUES ($1, 0, CURRENT_DATE)
                ON CONFLICT (user_id) DO UPDATE
                SET current_question_index = 0, last_prompted = CURRENT_DATE
            """, user_id)
            current_index = 0
            _, base_question = WELLNESS_QUESTIONS[0]
            rephrased = await rephrase_question(WELLNESS_QUESTIONS[0][0], base_question)
            return rephrased


        current_index = progress["current_question_index"]
        field, question_text = WELLNESS_QUESTIONS[current_index]

        if not user_input.strip():
            rephrased_question = await rephrase_question(field, question_text)
            return rephrased_question


        # 4. Try extracting an answer
        answer = await extract_answer_from_input(user_input, field)
        if not answer:
            return "I couldn't quite understand your response. Could you please answer the question again?"

        # 5. Save the answer into the database (upsert)
        await conn.execute(f"""
            INSERT INTO wellness_checkins (user_id, checkin_date, {field})
            VALUES ($1, CURRENT_DATE, $2)
            ON CONFLICT (user_id, checkin_date)
            DO UPDATE SET {field} = EXCLUDED.{field}
        """, user_id, answer)

        # 6. Advance to next question
        current_index += 1

        if current_index >= len(WELLNESS_QUESTIONS):
            await conn.execute("DELETE FROM wellness_checkin_progress WHERE user_id = $1", user_id)
            return "Thanks! You've completed today's wellness check-in. 😊"

        # 7. Save new progress
        await conn.execute("""
            UPDATE wellness_checkin_progress 
            SET current_question_index = $1, last_prompted = CURRENT_DATE 
            WHERE user_id = $2
        """, current_index, user_id)

        _, next_base_question = WELLNESS_QUESTIONS[current_index]
        rephrased_next = await rephrase_question(WELLNESS_QUESTIONS[current_index][0], next_base_question)
        return rephrased_next


    except Exception as e:
        logger.error(f"Wellness check error for user {user_id}: {e}", exc_info=True)
        return None

    finally:
        await conn.close()
