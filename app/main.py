from fastapi import FastAPI, Depends
import random
import time

from app.config import settings
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

# llm = LLMClient()

PRIMARY_LLM = LLMClient("llama-3.3-70b-versatile")
FALLBACK_LLM = LLMClient("llama-3.1-8b-instant")


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

    session.setdefault("conversation", [])
    session.setdefault("intelligence", {})
    session.setdefault("use_fallback_model", False)
    session.setdefault("callback_sent", False)

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
                session["intelligence"], new_intel
            )
            session["last_intel_turn"] = len(session["conversation"]) // 2
            print(session["intelligence"])
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
    
    #Generate Response
    if state != "TERMINATED":
        system_prompt = build_prompt(state, session)

        try:
            if session["use_fallback_model"]:
                reply = FALLBACK_LLM.generate(system_prompt, session["conversation"])
            else:
                reply = PRIMARY_LLM.generate(system_prompt, session["conversation"])

        except Exception as e:
            err = str(e).lower()

            # Switch ONLY on rate-limit / quota errors
            if "429" in err or "rate limit" in err or "tokens per day" in err:
                print("[LLM] Primary model rate-limited → switching to fallback")
                session["use_fallback_model"] = True
                reply = FALLBACK_LLM.generate(system_prompt, session["conversation"])
            else:
                print(f"[LLM] Generation error: {e}")
                reply = "Can you explain what this is about?"
    else:
        reply = random.choice(TERMINATION_RESPONSES)


    # Save response
    session["conversation"].append({
        "sender": "assistant",
        "text": reply,
        "timestamp": int(time.time() * 1000)
    })


    if state == "TERMINATED" and not session.get("callback_sent", False):
        try:
            send_final_result(payload.sessionId, session)
            session["callback_sent"] = True
            print(f"[Main] Callback marked as sent for session {payload.sessionId}")
        except Exception as e:
            print(f"[Main] Callback execution error: {str(e)}")
    
    
    # Return response
    return MessageResponse(
        status="success",
        reply=reply
    )