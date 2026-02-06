from app.agent.intelligence_extractor import IntelligenceExtractor
from app.agent.states import AgentState
import os

class AgentStateMachine:
    """
    State machine with decision-driven termination.
    """

    HIGH_SCAM_CONFIDENCE = 0.7
    INTELLIGENCE_COMPLETENESS_THRESHOLD = os.environ.get("INTELLIGENCE_COMPLETENESS_THRESHOLD", 0.5)
    MAX_TURNS_EXTRACTING = 12
    MIN_TURNS_FOR_TERMINATION = 5       # Minimum turns to justify a final report
    STAGNATION_TURNS = 2                # How many turns without new intel = stagnation


    def next_state(self, session: dict) -> str:
        current_state = session.get("state", AgentState.IDLE)
        scam_confidence = session.get("scam_confidence", 0.0)
        intelligence = session.get("intelligence", {})
        conversation = session.get("conversation", [])

        turn_count = len(conversation) // 2

        # Already terminated → stay terminated
        if current_state == AgentState.TERMINATED:
            return AgentState.TERMINATED

        #IF Intelligence completeness reached
        completeness = IntelligenceExtractor.calculate_completeness_score(intelligence)
        if completeness >= self.INTELLIGENCE_COMPLETENESS_THRESHOLD:
            return AgentState.TERMINATED

        #IF Scam confirmed + minimum engagement done
        # if (
        #     session.get("scam_detected")
        #     and scam_confidence >= self.HIGH_SCAM_CONFIDENCE
        #     and turn_count >= self.MIN_TURNS_FOR_TERMINATION
        # ):
        #     return AgentState.TERMINATED

        #IF Scam confirmed + stagnation (no new intel recently)
        if session.get("scam_detected") and turn_count >= self.MIN_TURNS_FOR_TERMINATION:
            last_intel_turn = session.get("last_intel_turn", -1)
            if last_intel_turn != -1 and (turn_count - last_intel_turn) >= self.STAGNATION_TURNS:
                return AgentState.TERMINATED

        #IF Hard safety cap
        if turn_count >= self.MAX_TURNS_EXTRACTING:
            return AgentState.TERMINATED

        # EARLY TERMINATION
        if session["scam_detected"]:
            intelligence = session.get("intelligence", {})

            critical_intel_found = any(
                key in intelligence and intelligence[key]
                for key in ["upi_id", "bank_account", "phone", "url"]
            )

            # At least 5 turns to avoid 1-shot termination
            if critical_intel_found and turn_count >= 6:
                return AgentState.TERMINATED

    
        if not session.get("scam_detected"):
            return AgentState.IDLE

        if scam_confidence < self.HIGH_SCAM_CONFIDENCE:
            return AgentState.SUSPICIOUS

        if scam_confidence >= self.HIGH_SCAM_CONFIDENCE and not intelligence:
            return AgentState.ENGAGING

        if scam_confidence >= self.HIGH_SCAM_CONFIDENCE and intelligence:
            return AgentState.EXTRACTING

        return current_state

    def get_next_target(self, session: dict) -> str:
        """
        Determine what intelligence to target next.
        """
        missing = IntelligenceExtractor.get_missing_categories(
            session.get("intelligence", {})
        )

        priority = ["upi_id", "bank_account", "url", "phone", "ifsc"]

        for target in priority:
            if target in missing:
                return target

        return "general"
