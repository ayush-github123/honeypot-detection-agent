from agent.states import AgentState
from agent.intelligence_extractor import IntelligenceExtractor

class AgentStateMachine:
    """
    Enhanced state machine with intelligence-driven transitions.
    """
    
    HIGH_SCAM_CONFIDENCE = 0.7
    INTELLIGENCE_COMPLETENESS_THRESHOLD = 0.6
    MAX_TURNS_EXTRACTING = 15
    
    def next_state(self, session: dict) -> str:
        current_state = session["state"]
        scam_confidence = session.get("scam_confidence", 0.0)
        intelligence = session.get("intelligence", {})
        turn_count = len(session.get("conversation", [])) // 2  # Approximate turns
        
        if current_state == AgentState.TERMINATED:
            return AgentState.TERMINATED
        
        # Check if we should terminate
        completeness = IntelligenceExtractor.calculate_completeness_score(intelligence)
        if completeness >= self.INTELLIGENCE_COMPLETENESS_THRESHOLD:
            return AgentState.TERMINATED
        
        # Check if we've exceeded max turns (safety limit)
        if turn_count > self.MAX_TURNS_EXTRACTING:
            return AgentState.TERMINATED
        
        # If no scam detected - stay idle
        if not session["scam_detected"]:
            return AgentState.IDLE
        
        # Low confidence scam - be suspicious
        if scam_confidence < self.HIGH_SCAM_CONFIDENCE:
            return AgentState.SUSPICIOUS
        
        # High confidence scam with no intel - start engaging
        if scam_confidence >= self.HIGH_SCAM_CONFIDENCE and not intelligence:
            return AgentState.ENGAGING
        
        # High confidence + some intel - extraction mode
        if scam_confidence >= self.HIGH_SCAM_CONFIDENCE and intelligence:
            return AgentState.EXTRACTING
        
        return current_state
    
    def get_next_target(self, session: dict) -> str:
        """
        Determine what intelligence to target next.
        """
        missing = IntelligenceExtractor.get_missing_categories(session.get("intelligence", {}))
        
        # Priority order for extraction
        priority = ["upi_id", "bank_account", "url", "phone", "ifsc"]
        
        for target in priority:
            if target in missing:
                return target
        
        return "general"  # Fallback