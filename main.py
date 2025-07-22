import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from enum import Enum

from services.message_processor import process_user_message

load_dotenv()
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", 500))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Role(str, Enum):
    supporter = "supporter"
    challenger = "challenger"

class ChatRequest(BaseModel):
    message: str
    role: Role = Role.supporter 

class WellnessRequest(BaseModel):
    pass

# class WellnessRequest(BaseModel):
#     user_id: str | None = None
#     session_id: str | None = None

DEFAULT_USER_ID = "test_user_4"
DEFAULT_SESSION_ID = "session_4"

@app.post("/api/chat")
async def chat_endpoint(chat_req: ChatRequest):
    user_message = chat_req.message.strip()
    role = chat_req.role.value

    if not user_message:
        raise HTTPException(status_code=400, detail="Empty message is not allowed.")
    if len(user_message) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Message too long. Max {MAX_INPUT_LENGTH} characters allowed.",
        )

    try:
        response = await process_user_message(
            user_id="default_user", 
            session_id="default_session",
            user_message=user_message,
            job=role,
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

    

@app.post("/api/wellness-check")
async def trigger_wellness_check():
    """
    Triggers the wellness check as if the user provided an empty message.
    """
    try:
        response = await process_user_message(
            DEFAULT_USER_ID, DEFAULT_SESSION_ID, "", trigger_wellness=True
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wellness error: {str(e)}")


# run server uvicorn main:app --reload --port 8000
