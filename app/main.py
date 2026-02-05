from fastapi import FastAPI, Depends, HTTPException
from app.config import settings
import random
import time
from app.models import MessageResponse, MessageRequest
from app.auth import verify_api_key
from app.session import SessionStore
from app.scam_detector import ScamDetector
from app.agent.prompts import build_prompt
from app.agent.llm_client import LLMClient
from app.agent.state_management import AgentStateMachine
from app.agent.intelligence_extractor import IntelligenceExtractor
from app.callback import send_final_result

app = FastAPI(title="Agentic HoneyPot Detection")

sessionStore = SessionStore()
state_machine = AgentStateMachine()
llm = LLMClient()


TERMINATION_RESPONSES = [
    "Okay, I understand.",
    "Alright, thanks for the information.",
    "Noted, I'll check on that.",
    "Got it, thanks for letting me know.",
    "Okay, I will look into this."
]


@app.post("/message", response_model=MessageResponse)
def recieve_message(payload: MessageRequest, api_key: str = Depends(verify_api_key)):
    session = sessionStore.get_or_create(payload.sessionId)
    
    # Merge history + new message
    # if payload.conversationHistory:
    #     session["conversation"] = [
    #         msg.model_dump() for msg in payload.conversationHistory
    #     ]

    if payload.conversationHistory and not session["conversation"]:
        session["conversation"] = [
            msg.model_dump() for msg in payload.conversationHistory
        ]

    
    msg = payload.message.model_dump()
    session["conversation"].append(msg)
    
    # Scam detection
    try:
        is_scam, confidence = ScamDetector.analyze(payload.message.text)
        if is_scam:
            session["scam_detected"] = True
            session["scam_confidence"] = max(session.get("scam_confidence", 0.0), confidence)
    except Exception as e:
        print(f"Scam detection error: {str(e)}")
        pass
    
    # INTELLIGENCE EXTRACTION
    try:
        new_intel = IntelligenceExtractor.extract_from_message(payload.message.text)
        if new_intel:
            session["intelligence"] = IntelligenceExtractor.merge_intelligence(
                session.get("intelligence", {}),
                new_intel
            )
    except Exception as e:
        print(f"Intelligence extraction error: {str(e)}")
        pass
    
    # State management
    try:
        next_state = state_machine.next_state(session)
        session["state"] = next_state
        state = session["state"]
    except Exception as e:
        print(f"State management error: {str(e)}")
        state = session.get("state", "IDLE")
    
    # Generate response
    if state != "TERMINATED":
        try:
            system_prompt = build_prompt(state, session)
            reply = llm.generate(system_prompt, session["conversation"])
        except Exception as e:
            print(f"LLM generation error: {str(e)}")
            # Fallback response
            reply = "Can you explain what this is about?"
    else:
        reply = random.choice(TERMINATION_RESPONSES)


    if state == "TERMINATED" and not session.get("callback_sent", False):
        try:
            # success = send_final_result(payload.sessionId, session)
            # if success:
            #     session["callback_sent"] = True
            send_final_result(payload.sessionId, session)
            session["callback_sent"] = True
            print(f"[Main] Callback marked as sent for session {payload.sessionId}")
        except Exception as e:
            # Never let callback errors crash the endpoint
            print(f"[Main] Callback execution error: {str(e)}")
    
    
    # Save response
    session["conversation"].append({
        "sender": "assistant",
        "text": reply,
        "timestamp": int(time.time() * 1000)
    })
    
    # Return response (unchanged format)
    return MessageResponse(
        status="success",
        reply=reply
    )