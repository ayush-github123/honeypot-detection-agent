from pydantic import BaseModel
from typing import List, Optional, Dict

class ChatMessage(BaseModel):
    sender: str  # "scammer" or "user"
    text: str
    timestamp: str

class Metadata(BaseModel):
    channel: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None

class MessageRequest(BaseModel):
    sessionId: str
    message: ChatMessage
    conversationHistory: List[ChatMessage] = []
    metadata: Optional[Metadata] = None

class MessageResponse(BaseModel):
    status: str
    reply: str
    scam_detected: Optional[bool] = False
    intelligence: Optional[Dict] = {}
    completeness_score: Optional[float] = 0.0
    turn_count: Optional[int] = 0