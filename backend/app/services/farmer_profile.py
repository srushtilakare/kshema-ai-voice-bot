from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FarmerProfile:
    """
    Stores structured information collected during a conversation
    with a farmer.
    """

    name: Optional[str] = None

    preferred_language: Optional[str] = None
    current_language: Optional[str] = None
    language_history: list[str] = field(default_factory=list)

    location: Optional[str] = None

    crop: Optional[str] = None

    land_area: Optional[float] = None
    land_unit: Optional[str] = None

    previous_crop_loss: Optional[bool] = None
    loss_reason: Optional[str] = None

    previous_insurance: Optional[bool] = None
    insurance_claim_experience: Optional[str] = None

    insurance_awareness: Optional[str] = None
    premium_concern: Optional[bool] = None
    trust_concern: Optional[bool] = None

    insurance_interest: Optional[str] = None

    additional_notes: Optional[str] = None

    def update_language(self, language_code: str):
        """
        Update the current language after every farmer utterance.
        """

        if not language_code:
            return

        self.current_language = language_code

        if language_code not in self.language_history:
            self.language_history.append(language_code)

        if self.preferred_language is None:
            self.preferred_language = language_code

    def to_dict(self):
        """
        Convert the farmer profile into a dictionary.
        """

        return {
            "name": self.name,
            "preferred_language": self.preferred_language,
            "current_language": self.current_language,
            "language_history": self.language_history,
            "location": self.location,
            "crop": self.crop,
            "land_area": self.land_area,
            "land_unit": self.land_unit,
            "previous_crop_loss": self.previous_crop_loss,
            "loss_reason": self.loss_reason,
            "previous_insurance": self.previous_insurance,
            "insurance_claim_experience": self.insurance_claim_experience,
            "insurance_awareness": self.insurance_awareness,
            "premium_concern": self.premium_concern,
            "trust_concern": self.trust_concern,
            "insurance_interest": self.insurance_interest,
            "additional_notes": self.additional_notes,
        }