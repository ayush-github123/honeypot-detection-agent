from fastapi import FastAPI, Depends, HTTPException
from config import settings
from models import MessageResponse, MessageRequest
from auth import verify_api_key
from session import SessionStore

app = FastAPI(title="Agentic HoneyPot Detection")


sessionStore = SessionStore()


@app.post("/message", response_model=MessageResponse)
def recieve_message(payload: MessageRequest, api_key: str = Depends(verify_api_key)):
    session = sessionStore.get_or_create(payload.sessionId)

    session["conversation"].append(payload.message.model_dump())

    dummy_reply = "Okay, I see. Can you explain more?"

    session["conversation"].append({
        "sender": "user",
        "text": dummy_reply,
        "timestamp": "now"
    })

    return MessageResponse(
        status="success",
        reply=dummy_reply
    )



@app.get("/health", response_model=MessageResponse)
def health_check():
    #backend-check only fn

    #check if agent is online 

    return MessageResponse(
        status="success",
        reply="Backend is working fine...!"
    )

