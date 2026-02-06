import re
from typing import Dict, List
from datetime import datetime

class IntelligenceExtractor:
    """
    Extracts and tracks actionable intelligence from scammer messages.
    """
    
    # Regex patterns for entity extraction
    PATTERNS = {
        "upi_id": r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9]{2,}\b',
        "phone": r'\b(?:\+?\d{1,3}[-\s]?)?\d{10}\b',
        "bank_account": r'\b\d{9,18}\b',
        "ifsc": r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
        "url": r'https?://[^\s]+',
        "crypto_wallet": r'\b(?:0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})\b',
        "email": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
        "amount": r'(?:Rs\.?|₹|INR|rupees?)\s*(\d+(?:,\d+)*(?:\.\d{2})?)',
    }

    SUSPICIOUS_KEYWORDS = [
        "urgent",
        "verify now",
        "account blocked",
        "account will be blocked",
        "otp",
        "upi pin",
        "send otp",
        "immediately",
        "within minutes",
        "fraud team",
        "security team",
        "limited time",
        "suspend",
        "blocked",
        "transfer now",
        "pay now"
    ]

    
    INTELLIGENCE_CATEGORIES = [
        "upi_id",
        "bank_account",
        "ifsc",
        "url",
        "phone",
        "crypto_wallet",
        "email",
        "amount",
        "suspicious_keywords"
    ]
    
    @staticmethod
    def extract_from_message(text: str) -> Dict[str, List[Dict]]:
        """
        Extract all intelligence entities from a single message.
        Returns dict with categorized findings and confidence scores.
        """
        if not text or not text.strip():
            return {}
            
        findings = {}
        
        for category, pattern in IntelligenceExtractor.PATTERNS.items():
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if category == "bank_account":
                    matches = [
                        m for m in matches
                        if not re.fullmatch(r'(?:\+?\d{1,3}[-\s]?)?\d{10}', m)
                    ]
                if matches:
                    unique_matches = list(set([m for m in matches if m and str(m).strip()]))     # Remove duplicates and empty matches
                    
                    if unique_matches:
                        findings[category] = [
                            {
                                "value": str(match).strip(),
                                "confidence": IntelligenceExtractor._calculate_confidence(category, str(match), text),
                                "timestamp": datetime.utcnow().isoformat(),
                                "source_text": text[:100]  # Context snippet
                            }
                            for match in unique_matches
                        ]
            except Exception as e:
                print(f"Error extracting {category}: {str(e)}")
                continue

        found_keywords = []
        text_lower = text.lower()

        # Sort keywords by length
        for keyword in sorted(IntelligenceExtractor.SUSPICIOUS_KEYWORDS, key=len, reverse=True):
            if keyword in text_lower:
                found_keywords.append(keyword)
                text_lower = text_lower.replace(keyword, "")  # prevent sub-match

        if found_keywords:
            findings["suspicious_keywords"] = [
                {
                    "value": kw,
                    "confidence": 0.6, 
                    "timestamp": datetime.utcnow().isoformat(),
                    "source_text": text[:100]
                }
                for kw in set(found_keywords)
            ]

        return findings
    
    @staticmethod
    def _calculate_confidence(category: str, value: str, context: str) -> float:
        """
        Calculate confidence score for extracted entity.
        """
        confidence = 0.7  # Base confidence
        
        try:
            # UPI ID validation
            if category == "upi_id":
                if "@" in value and len(value) > 5:
                    upi_handles = ['paytm', 'ybl', 'okicici', 'okhdfcbank', 'okaxis', 'oksbi']
                    if any(handle in value.lower() for handle in upi_handles):
                        confidence = 0.95
                    else:
                        confidence = 0.85
            
            # Bank account validation
            elif category == "bank_account":
                if 9 <= len(value) <= 18 and value.isdigit():
                    confidence = 0.85
                    # Higher confidence if mentioned with IFSC or bank name
                    if re.search(r'(account|IFSC|bank)', context, re.IGNORECASE):
                        confidence = 0.95
            
            # URL validation
            elif category == "url":
                if any(suspicious in value.lower() for suspicious in ['bit.ly', 'tinyurl', 'short', '.tk', '.ml', '.ga']):
                    confidence = 0.95  # Shortened URLs = high scam confidence
                else:
                    confidence = 0.80
            
            # Phone validation
            elif category == "phone":
                # if len(value) == 10 or (value.startswith('+91') and len(value) == 13):
                #     confidence = 0.9
                digits = re.sub(r"\D", "", value)
                if 10 <= len(digits) <= 13:
                    confidence = 0.9
            
            # IFSC validation
            elif category == "ifsc":
                if len(value) == 11:
                    confidence = 0.95
            
            # Amount validation
            elif category == "amount":
                if value.replace(',', '').isdigit():
                    confidence = 0.85
            
            # Email validation
            elif category == "email":
                if "@" in value and "." in value:
                    confidence = 0.85
        
        except Exception:
            confidence = 0.7  
        
        return min(confidence, 1.0)
    
    @staticmethod
    def merge_intelligence(session_intel: Dict, new_intel: Dict) -> Dict:
        """
        Merge new findings into existing session intelligence.
        Deduplicates and keeps highest confidence scores.
        """
        if not session_intel:
            session_intel = {}
            
        merged = session_intel.copy()
        
        for category, findings in new_intel.items():
            if category not in merged:
                merged[category] = []
            
            for new_finding in findings:
                # Check if this value already exists
                existing = next(
                    (item for item in merged[category] if item["value"] == new_finding["value"]),
                    None
                )
                
                if existing:
                    if new_finding["confidence"] > existing["confidence"]:
                        existing["confidence"] = new_finding["confidence"]
                        existing["timestamp"] = new_finding["timestamp"]
                else:
                    merged[category].append(new_finding)  # Add new finding
        
        return merged
    
    @staticmethod
    def get_missing_categories(intelligence: Dict) -> List[str]:
        """
        Identify which intelligence categories are still missing.
        Used to guide agent's next questions.
        """
        missing = []
        
        for category in IntelligenceExtractor.INTELLIGENCE_CATEGORIES:
            if category not in intelligence or not intelligence[category]:
                missing.append(category)
        
        return missing
    
    @staticmethod
    def calculate_completeness_score(intelligence: Dict) -> float:
        """
        Calculate how complete the intelligence collection is (0.0 - 1.0).
        Used for evaluation metrics.
        """
        if not intelligence:
            return 0.0
        
        # Weighted scoring (critical intel gets higher weight)
        weights = {
            "upi_id": 0.25,
            "bank_account": 0.25,
            "url": 0.20,
            "phone": 0.15,
            "ifsc": 0.10,
            "suspicious_keywords": 0.05,
            "amount": 0.03,
            "email": 0.02,
        }
        
        score = 0.0
        for category, weight in weights.items():
            if category in intelligence and intelligence[category]:
                # Factor in confidence of extracted data
                avg_confidence = sum(item["confidence"] for item in intelligence[category]) / len(intelligence[category])
                score += weight * avg_confidence
        
        return min(score, 1.0)
    
    @staticmethod
    def format_for_output(intelligence: Dict) -> Dict:
        """
        Format intelligence for API response output.
        """
        formatted = {}
        
        for category, findings in intelligence.items():
            if findings:
                formatted[category] = [
                    {
                        "value": item["value"],
                        "confidence": round(item["confidence"], 2)
                    }
                    for item in findings
                ]
        
        return formatted