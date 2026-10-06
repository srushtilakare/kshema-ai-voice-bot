from datetime import datetime, timezone
from typing import Optional
from app.services.profile_extractor import extract_profile_updates
from app.services.farmer_profile import FarmerProfile

from app.services.llm_service import analyze_farmer_turn

class ConversationTurn:
    """
    Represents one turn in the conversation.
    """

    def __init__(
        self,
        speaker: str,
        transcript: str,
        language: Optional[str] = None,
    ):
        self.speaker = speaker
        self.transcript = transcript
        self.language = language
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            "speaker": self.speaker,
            "transcript": self.transcript,
            "language": self.language,
            "timestamp": self.timestamp,
        }


class ConversationState:
    """
    Temporary in-memory state for one farmer conversation.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.profile = FarmerProfile()
        self.turns: list[ConversationTurn] = []

    def add_farmer_turn(
    self,
    transcript: str,
    language: Optional[str],
    ):
        """
        Add a farmer utterance and extract profile information.
        """

        turn = ConversationTurn(
            speaker="farmer",
            transcript=transcript,
            language=language,
        )

        self.turns.append(turn)

        # Update current language.
        if language:
            self.profile.update_language(language)

        # Keep the old rule-based extractor for now.
        rule_based_updates = extract_profile_updates(
            transcript=transcript,
            language=language,
        )

        for field_name, value in rule_based_updates.items():
            if hasattr(self.profile, field_name):
                setattr(
                    self.profile,
                    field_name,
                    value,
                )

        return rule_based_updates

    def add_bot_turn(
        self,
        transcript: str,
        language: Optional[str],
    ):
        """
        Add a Kshema response to the conversation.
        """

        turn = ConversationTurn(
            speaker="bot",
            transcript=transcript,
            language=language,
        )

        self.turns.append(turn)

    def analyze_with_llm(self, transcript: str):
        """
        Analyze the latest farmer message using Sarvam LLM.
        """

        history = [
            turn.to_dict()
            for turn in self.turns
        ]

        result = analyze_farmer_turn(
            transcript=transcript,
            language=self.profile.current_language or "en-IN",
            profile=self.profile.to_dict(),
            conversation_history=history,
        )

        return result

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "profile": self.profile.to_dict(),
            "turns": [
                turn.to_dict()
                for turn in self.turns
            ],
        }


# Temporary in-memory conversation storage.
#
# Later this will be replaced by MongoDB.
conversation_store: dict[str, ConversationState] = {}


def get_or_create_conversation(session_id: str) -> ConversationState:
    """
    Get an existing conversation or create a new one.
    """

    if session_id not in conversation_store:
        conversation_store[session_id] = ConversationState(
            session_id=session_id
        )

    return conversation_store[session_id]