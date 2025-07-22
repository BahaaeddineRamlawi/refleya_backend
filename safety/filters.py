import json
import os
from utils.logger import logger

WARNING_MESSAGE = (
    "I'm here to support your mental wellness. Please consult a mental health professional for clinical advice."
)

def load_safety_keywords():
    try:
        file_path = os.path.join(os.path.dirname(__file__), "safety_keywords.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["crisis_triggers"], data["unsafe_keywords"]
    except Exception as e:
        logger.error(f"Failed to load safety keywords: {e}", exc_info=True)
        return [], []

CRISIS_TRIGGERS, UNSAFE_KEYWORDS = load_safety_keywords()

def safety_filter(response: str) -> str:
    try:
        if "diagnose" in response.lower() or "prescribe" in response.lower():
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
        if any(trigger in user_message.lower() for trigger in CRISIS_TRIGGERS):
            logger.warning("Crisis trigger detected in user message.")
            return (
                "If you're in distress, please reach out to a local crisis line or mental health professional. "
                "You are not alone."
            )
        return None
    except Exception as e:
        logger.error(f"Error during crisis check: {e}", exc_info=True)
        return WARNING_MESSAGE

def contains_unsafe_advice(response: str) -> bool:
    try:
        return any(kw in response.lower() for kw in UNSAFE_KEYWORDS)
    except Exception as e:
        logger.error(f"Error while checking for unsafe advice: {e}", exc_info=True)
        return True
