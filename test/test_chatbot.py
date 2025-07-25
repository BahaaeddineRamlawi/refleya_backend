import asyncio
import uuid
import os
from dotenv import load_dotenv

from services.message_processor import process_user_message

load_dotenv()
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH"))

async def chat():
    user_id = "test_user_2"
    session_id = str(uuid.uuid4())

    print("Chatbot started. Type 'exit' to quit.")

    while True:
        user_message = input("You: ").strip()

        if user_message.lower() in ("exit", "quit"):
            break

        if len(user_message) > MAX_INPUT_LENGTH:
            print(f"⚠️ Your message is too long ({len(user_message)} characters). "
                  f"Please limit input to {MAX_INPUT_LENGTH} characters.")
            continue

        response = await process_user_message(user_id, session_id, user_message)

        print(f"Model: {response}")

if __name__ == "__main__":
    asyncio.run(chat())
