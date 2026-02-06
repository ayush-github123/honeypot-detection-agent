import requests
from typing import Dict, Optional
from app.agent.intelligence_extractor import IntelligenceExtractor


def generate_agent_notes(session: dict) -> str:
    """
    Generate human-readable summary of agent's interaction with scammer.
    
    Args:
        session: Session dictionary containing conversation and intelligence data
        
    Returns:
        Formatted string summarizing the engagement
    """
    scam_detected = session.get("scam_detected", False)
    confidence = session.get("scam_confidence", 0.0)
    intelligence = session.get("intelligence", {})
    state = session.get("state", "UNKNOWN")
    turn_count = len(session.get("conversation", [])) // 2
    
    if not scam_detected:
        return "No scam behavior detected during conversation."
    
    # Build notes
    notes_parts = []
    notes_parts.append(f"Scam detected with {confidence:.1%} confidence.")
    notes_parts.append(f"Agent progressed through state: {state}.")
    notes_parts.append(f"Total turns of engagement: {turn_count}.")
    
    # Summarize extracted intelligence
    intel_summary = []
    if intelligence.get("bank_accounts"):
        intel_summary.append(f"{len(intelligence['bank_accounts'])} bank account(s)")
    if intelligence.get("upi_ids"):
        intel_summary.append(f"{len(intelligence['upi_ids'])} UPI ID(s)")
    if intelligence.get("urls"):
        intel_summary.append(f"{len(intelligence['urls'])} phishing link(s)")
    if intelligence.get("phone_numbers"):
        intel_summary.append(f"{len(intelligence['phone_numbers'])} phone number(s)")
    
    if intel_summary:
        notes_parts.append(f"Successfully extracted: {', '.join(intel_summary)}.")
    else:
        notes_parts.append("Limited intelligence extracted before termination.")
    
    return " ".join(notes_parts)


def send_final_result(session_id: str, session: dict) -> bool:
    """
    Send final extracted intelligence to GUVI hackathon endpoint.
    
    This function is called once per session when the agent reaches TERMINATED state.
    
    Args:
        session_id: Unique session identifier
        session: Complete session dictionary with conversation and intelligence
        
    Returns:
        True if callback succeeded, False otherwise
    """
    # Format intelligence using existing extractor
    try:
        formatted_intel = IntelligenceExtractor.format_for_output(
            session.get("intelligence", {})
        )
    except Exception as e:
        print(f"[GUVI Callback] Intelligence formatting error: {str(e)}")
        formatted_intel = {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": []
        }
    
    # Generate agent notes
    try:
        agent_notes = generate_agent_notes(session)
    except Exception as e:
        print(f"[GUVI Callback] Agent notes generation error: {str(e)}")
        agent_notes = "Agent engagement completed."
    
    # Calculate total messages exchanged
    total_messages = len(session.get("conversation", []))
    
    # Build payload exactly as specified
    payload = {
        "sessionId": session_id,
        "scamDetected": session.get("scam_detected", False),
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "bankAccounts": formatted_intel.get("bankAccounts", []),
            "upiIds": formatted_intel.get("upiIds", []),
            "phishingLinks": formatted_intel.get("phishingLinks", []),
            "phoneNumbers": formatted_intel.get("phoneNumbers", []),
            "suspiciousKeywords": formatted_intel.get("suspiciousKeywords", [])
        },
        "agentNotes": agent_notes
    }
    
    # Send POST request to hackathon endpoint
    callback_url = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    try:
        print(f"[GUVI Callback] Sending final result for session {session_id}")
        print("Data sent: ", payload)
        response = requests.post(
            callback_url,
            json=payload,
            timeout=10,  # 10 second timeout
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"[GUVI Callback] ✓ Successfully sent for session {session_id}")
            return True
        else:
            print(f"[GUVI Callback] ✗ Failed with status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"[GUVI Callback] ✗ Timeout sending callback for session {session_id}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[GUVI Callback] ✗ Request error for session {session_id}: {str(e)}")
        return False
    except Exception as e:
        print(f"[GUVI Callback] ✗ Unexpected error for session {session_id}: {str(e)}")
        return False
