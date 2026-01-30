from typing import Dict


class SessionStore:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}

    def get_or_create(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "conversation": [],
                "scam_detected": False,
                "intelligence": {},
                "state": "IDLE"
            }
        return self.sessions[session_id]
