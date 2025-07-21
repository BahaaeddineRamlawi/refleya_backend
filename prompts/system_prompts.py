from utils.logger import logger

def get_persona_prompt(mode="cbt", job="supporter"):
    try:
        job_instruction = {
            "supporter": "Your tone is empathetic, gentle, and uplifting.",
            "challenger": "Your tone is constructive, direct, and helps the user challenge their thoughts.",
        }.get(job, "Your tone is supportive by default.")

        prompts = {
            "cbt": f"You are a friendly, Socratic coach using CBT techniques. Avoid medical advice. {job_instruction}",
            "journaling": f"You are a gentle journaling companion. Encourage, don’t analyze. {job_instruction}",
            "coaching": f"You are a motivational coach. Focus on actionable goals and encouragement. {job_instruction}",
        }

        return prompts.get(mode, prompts["cbt"])

    except Exception as e:
        logger.error(f"Error generating persona prompt: {e}", exc_info=True)
        return "You are a helpful assistant."