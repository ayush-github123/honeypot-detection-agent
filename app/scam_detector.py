import re
from typing import Tuple

SCAM_KEYWORDS = [
    # Account threats
    "account blocked", "account suspended", "account freeze", "account lock",
    "suspension", "blocked", "deactivated", "terminated",
    
    # Verification/KYC scams
    "verify immediately", "verify now", "verification required", "verification pending",
    "kyc expired", "kyc pending", "kyc update", "update kyc", "renew kyc",
    "kyc is expired", "expired kyc", "kyc has expired",
    "kyc", "verification", "update now", "renew",
    
    # Urgency tactics
    "urgent", "immediately", "right now", "do it fast", "hurry",
    "limited time", "expires today", "last chance", "final notice",
    "within 24 hours", "before midnight", "deadline",
    
    # Payment requests
    "processing fee", "clearance fee", "registration fee", "activation charge",
    "pay now", "payment required", "send payment", "transfer amount",
    "processing charge", "service charge", "pay via", "send to",
    
    # Links and actions
    "click link", "click here", "open link", "visit link",
    "share otp", "send otp", "provide otp", "enter otp",
    "share password", "share pin", "share cvv",
    
    # UPI/Payment specific
    "send to upi", "pay via upi", "upi payment", "share upi", "via upi",
    "paytm", "phonepe", "googlepay", "gpay",
    
    # Prize/lottery scams
    "you won", "congratulations", "selected for", "lottery winner",
    "claim prize", "prize money", "tax payment",
    
    # Authority impersonation
    "bank account", "government mandate", "rbi order", "legal action",
    "police case", "arrest warrant", "court notice", "no choice",
    
    # Parcel/courier scams
    "customs clearance", "parcel held", "delivery pending", "courier charge",
    
    # Job scams
    "work from home", "selected for job", "job offer", "joining fee"
]

SAFE_PHRASES = [
    "do not share", "never share", "bank will never ask",
    "we will not ask", "do not disclose", "beware of fraud",
    "avoid sharing", "do not respond", "ignore such messages",
    "verify before sharing"
]

# Enhanced regex patterns
UPI_REGEX = r"\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9]{2,}\b"
URL_REGEX = r"https?://[^\s]+"
AMOUNT_REGEX = r"(?:Rs\.?|₹|INR|rupees?)\s*(\d+(?:,\d+)*)"
PHONE_REGEX = r"\b(?:\+91|0)?[6-9]\d{9}\b"

class ScamDetector:
    """
    Enhanced rule-based scam intent detector with flexible matching.
    """
    
    @staticmethod
    def analyze(text: str) -> Tuple[bool, float]:
        if not text or not text.strip():
            return False, 0.0
            
        text_lower = text.lower()
        score = 0.0
        
        # Check for safe phrases first (override scam detection)
        for safe in SAFE_PHRASES:
            if safe in text_lower:
                return False, 0.0
        
        # Flexible keyword matching (partial match allowed)
        matched_keywords = 0
        for keyword in SCAM_KEYWORDS:
            if keyword in text_lower:
                score += 0.15
                matched_keywords += 1
        
        # Bonus for multiple keyword matches (indicates higher scam probability)
        if matched_keywords >= 3:
            score += 0.2
        elif matched_keywords >= 2:
            score += 0.1
        
        # Pattern detection (high-value indicators)
        has_upi = bool(re.search(UPI_REGEX, text))
        has_url = bool(re.search(URL_REGEX, text))
        has_amount = bool(re.search(AMOUNT_REGEX, text, re.IGNORECASE))
        has_phone = bool(re.search(PHONE_REGEX, text))
        
        if has_upi:
            score += 0.35  # UPI in unsolicited message is highly suspicious
        if has_url:
            score += 0.35  # URLs in scam context
        if has_amount:
            score += 0.20  # Payment amounts
        if has_phone:
            score += 0.15  # Phone numbers
        
        # Combination bonuses (scammers often include multiple elements)
        if has_upi and has_amount:
            score += 0.15  # Payment request with amount
        if has_url and matched_keywords > 0:
            score += 0.10  # Link with urgency
        
        # Cap the score
        confidence = min(score, 1.0)
        
        # Lower threshold for detection (0.3 for early detection)
        # Even weak signals should trigger SUSPICIOUS state
        is_scam = confidence >= 0.3
        
        return is_scam, confidence