import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sarvamai import SarvamAI


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# ---------------------------------------------------------
# Initialize Sarvam client
# ---------------------------------------------------------

api_key = os.getenv("SARVAM_API_KEY")

if not api_key:
    raise ValueError(
        f"SARVAM_API_KEY is not configured. "
        f"Checked: {ENV_FILE}"
    )

client = SarvamAI(
    api_subscription_key=api_key
)


# ---------------------------------------------------------
# Model
# ---------------------------------------------------------

MODEL_NAME = "sarvam-105b-conversations"


# ---------------------------------------------------------
# System Prompt
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are Kshema, a multilingual AI voice assistant helping
Indian farmers understand crop insurance.

Your job in each conversation turn is to:

1. Understand the farmer's latest statement.
2. Extract any useful farmer information.
3. Look at the existing farmer profile.
4. Identify important information that is still missing.
5. Ask the most relevant next question.
6. Respond naturally in the farmer's CURRENT language.

IMPORTANT RULES:

- The farmer may change languages at any time.
- Always respond in the current language provided by the application.
- Do not force the farmer to follow a fixed questionnaire.
- Ask only one useful question at a time.
- Keep responses short and natural because this is a voice conversation.
- Do not invent farmer information.
- If information is not present, return null.
- Do not assume that the farmer will definitely purchase insurance.
- Insurance interest is only an estimate based on what the farmer says.
- Do not provide unsupported insurance facts.
- If the farmer asks for specific insurance policy information, that
  will later be handled using the RAG knowledge system.

The application will provide:

CURRENT LANGUAGE:
The language detected from the farmer's latest utterance.

CURRENT FARMER PROFILE:
Information already collected from previous turns.

LATEST FARMER MESSAGE:
The farmer's newest statement.

Return ONLY the requested JSON structure.
"""


# ---------------------------------------------------------
# JSON Schema
# ---------------------------------------------------------

PROFILE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "profile_updates": {
            "type": "object",
            "properties": {
                "name": {
                    "type": ["string", "null"]
                },
                "location": {
                    "type": ["string", "null"]
                },
                "crop": {
                    "type": ["string", "null"]
                },
                "land_area": {
                    "type": ["number", "null"]
                },
                "land_unit": {
                    "type": ["string", "null"]
                },
                "previous_crop_loss": {
                    "type": ["boolean", "null"]
                },
                "loss_reason": {
                    "type": ["string", "null"]
                },
                "previous_insurance": {
                    "type": ["boolean", "null"]
                },
                "insurance_claim_experience": {
                    "type": ["string", "null"]
                },
                "insurance_awareness": {
                    "type": ["string", "null"]
                },
                "premium_concern": {
                    "type": ["boolean", "null"]
                },
                "trust_concern": {
                    "type": ["boolean", "null"]
                },
                "insurance_interest": {
                    "type": ["string", "null"]
                },
                "additional_notes": {
                    "type": ["string", "null"]
                }
            },
            "required": [
                "name",
                "location",
                "crop",
                "land_area",
                "land_unit",
                "previous_crop_loss",
                "loss_reason",
                "previous_insurance",
                "insurance_claim_experience",
                "insurance_awareness",
                "premium_concern",
                "trust_concern",
                "insurance_interest",
                "additional_notes"
            ],
            "additionalProperties": False
        },
        "next_question": {
            "type": "string"
        },
        "response": {
            "type": "string"
        }
    },
    "required": [
        "profile_updates",
        "next_question",
        "response"
    ],
    "additionalProperties": False
}


# ---------------------------------------------------------
# LLM Profile Extraction
# ---------------------------------------------------------

def analyze_farmer_turn(
    transcript: str,
    language: str,
    profile: dict,
    conversation_history: list[dict],
) -> dict:
    """
    Send the farmer's latest message and current profile
    to Sarvam LLM.

    Returns structured profile updates and the next response.
    """

    profile_json = json.dumps(
        profile,
        ensure_ascii=False,
        indent=2,
    )

    history_json = json.dumps(
        conversation_history[-10:],
        ensure_ascii=False,
        indent=2,
    )

    user_prompt = f"""
CURRENT LANGUAGE:
{language}

CURRENT FARMER PROFILE:
{profile_json}

RECENT CONVERSATION:
{history_json}

LATEST FARMER MESSAGE:
{transcript}

Analyze the latest farmer message.

Extract ONLY information that is actually supported
by the conversation.

For every profile field:
- Return the newly extracted value if present.
- Otherwise return null.

Then decide the most useful next question based on
the information still missing.

The response should be natural and suitable for a
telephone voice conversation.

Return the required JSON structure.
"""

    response = client.chat.completions(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "farmer_conversation_analysis",
                "strict": True,
                "schema": PROFILE_RESPONSE_SCHEMA,
            },
        },
        temperature=0.2,
        reasoning_effort=None,
        max_tokens=600,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "Sarvam LLM returned an empty response."
        )

    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Sarvam LLM returned invalid JSON: {content}"
        ) from error

    return result