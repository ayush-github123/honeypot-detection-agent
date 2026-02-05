from fastapi import FastAPI, Depends, HTTPException
from config import settings
from models import MessageResponse, MessageRequest
from auth import verify_api_key
from session import SessionStore
from agent.prompts import build_prompt
from agent.llm_client import LLMClient
from agent.state_management import AgentStateMachine
from agent.intelligence_extractor import IntelligenceExtractor
from scam_detector import ScamDetector

app = FastAPI(title="Agentic HoneyPot Detection")

sessionStore = SessionStore()
state_machine = AgentStateMachine()
llm = LLMClient()

@app.post("/message", response_model=MessageResponse)
def recieve_message(payload: MessageRequest, api_key: str = Depends(verify_api_key)):
    session = sessionStore.get_or_create(payload.sessionId)
    
    # Merge history + new message
    if payload.conversationHistory:
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
        # Don't fail the request, just log and continue
        pass
    
    #INTELLIGENCE EXTRACTION
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
        reply = "Okay, got it. Thanks!"
    
    # Save response
    session["conversation"].append({
        "sender": "assistant",
        "text": reply,
        "timestamp": "now"
    })
    
    #Calculate metrics
    try:
        completeness = IntelligenceExtractor.calculate_completeness_score(
            session.get("intelligence", {})
        )
    except Exception as e:
        print(f"Completeness calculation error: {str(e)}")
        completeness = 0.0
    
    # Format intelligence for output
    try:
        formatted_intel = IntelligenceExtractor.format_for_output(session.get("intelligence", {}))
    except Exception as e:
        print(f"Intelligence formatting error: {str(e)}")
        formatted_intel = {}
    
    return MessageResponse(
        status="success",
        reply=reply,
        scam_detected=session.get("scam_detected", False),
        intelligence=formatted_intel,
        completeness_score=round(completeness, 2),
        turn_count=len(session["conversation"]) // 2
    )