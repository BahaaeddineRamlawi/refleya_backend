from utils.logger import logger

WARNING_MESSAGE = "I'm here to support your mental wellness. Please consult a mental health professional for clinical advice."

def safety_filter(response: str) -> str:
    try:
        if "diagnose" in response or "prescribe" in response:
            logger.warning("Filtered response due to medical terminology (diagnose/prescribe).")
            return WARNING_MESSAGE
        if contains_unsafe_advice(response):
            logger.warning("Filtered response due to unsafe advice.")
            return WARNING_MESSAGE
        return response
    except Exception as e:
        logger.error(f"Error during safety filter: {e}", exc_info=True)
        return WARNING_MESSAGE

def crisis_redirect(user_message: str) -> str | None:
    try:
        triggers = [
            "suicide", "kill myself", "end it all", "overdose", "self-harm", "cut myself", "i want to die",
            "jump off", "no reason to live", "can't go on", "ending my life", "hurt myself"
        ]
        if any(word in user_message.lower() for word in triggers):
            logger.warning("Crisis trigger detected in user message.")
            return ("If you're in distress, please reach out to a local crisis line or mental health professional. "
                    "You are not alone.")
        return None
    except Exception as e:
        logger.error(f"Error during crisis check: {e}", exc_info=True)
        return WARNING_MESSAGE

def contains_unsafe_advice(response: str) -> bool:
    try:
        unsafe_keywords = [
            "take drugs", "stop medication", "skip therapy", "refuse treatment",
            "ignore your doctor", "avoid therapy", "quit meds", "drop your pills", "no need for help"
        ]
        return any(kw in response.lower() for kw in unsafe_keywords)
    except Exception as e:
        logger.error(f"Error while checking for unsafe advice: {e}", exc_info=True)
        return True
