from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.sarvam_service import transcribe_audio
from app.services.conversation_service import get_or_create_conversation


# =========================================================
# FastAPI Application
# =========================================================

app = FastAPI(
    title="Kshema AI Voice Bot API",
    description="Backend API for the Kshema multilingual crop-insurance voice bot.",
    version="0.1.0",
)


# =========================================================
# CORS Configuration
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Request Models
# =========================================================

class ConversationTurnRequest(BaseModel):
    session_id: str
    transcript: str
    language: str


# =========================================================
# Response Models
# =========================================================

class ConversationTurnResponse(BaseModel):
    session_id: str
    language: str
    profile: dict
    profile_updates: dict
    message: str
    next_question: str


# =========================================================
# Basic Routes
# =========================================================

@app.get("/")
def root():
    return {
        "message": "Kshema AI Voice Bot API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# =========================================================
# Speech-to-Text Endpoint
# =========================================================

@app.post("/api/voice/transcribe")
async def transcribe_voice(
    audio: UploadFile = File(...)
):
    """
    Receive an audio file from the frontend,
    send it to Sarvam Saaras STT,
    and return:

    - transcript
    - detected language
    - language probability
    """

    audio_bytes = await audio.read()

    result = transcribe_audio(
        audio_bytes=audio_bytes,
        filename=audio.filename or "audio.webm",
    )

    return result


# =========================================================
# Conversation Endpoint
# =========================================================

@app.post(
    "/api/conversation/turn",
    response_model=ConversationTurnResponse,
)
async def conversation_turn(
    request: ConversationTurnRequest
):
    """
    Process one farmer conversation turn.

    Flow:

    Farmer transcript
        ↓
    Conversation state
        ↓
    Profile extraction
        ↓
    Sarvam LLM
        ↓
    Profile update
        ↓
    Next question / response
    """

    # -----------------------------------------------------
    # 1. Get existing conversation or create a new one
    # -----------------------------------------------------

    conversation = get_or_create_conversation(
        request.session_id
    )

    # -----------------------------------------------------
    # 2. Add farmer's latest message
    # -----------------------------------------------------

    rule_based_updates = conversation.add_farmer_turn(
        transcript=request.transcript,
        language=request.language,
    )

    # -----------------------------------------------------
    # 3. Analyze the farmer's message using Sarvam LLM
    # -----------------------------------------------------

    llm_result = conversation.analyze_with_llm(
        transcript=request.transcript
    )

    # -----------------------------------------------------
    # 4. Get LLM profile updates
    # -----------------------------------------------------

    llm_profile_updates = llm_result.get(
        "profile_updates",
        {},
    )

    # -----------------------------------------------------
    # 5. Apply LLM profile updates
    #
    # Only update fields when the LLM actually provides
    # a value. This prevents existing information from
    # being overwritten by null.
    # -----------------------------------------------------

    for field_name, value in llm_profile_updates.items():

        if (
            value is not None
            and hasattr(conversation.profile, field_name)
        ):
            setattr(
                conversation.profile,
                field_name,
                value,
            )

    # -----------------------------------------------------
    # 6. Get LLM-generated response
    # -----------------------------------------------------

    response_text = llm_result.get(
        "response",
        "Thank you. Please tell me a little more about your farm.",
    )

    # -----------------------------------------------------
    # 7. Get next question
    # -----------------------------------------------------

    next_question = llm_result.get(
        "next_question",
        "",
    )

    # -----------------------------------------------------
    # 8. Store Kshema's response
    # -----------------------------------------------------

    conversation.add_bot_turn(
        transcript=response_text,
        language=conversation.profile.current_language,
    )

    # -----------------------------------------------------
    # 9. Combine rule-based + LLM updates
    #
    # This is useful during development so we can compare
    # the old extractor with the LLM extractor.
    # -----------------------------------------------------

    combined_updates = {
        **rule_based_updates,
        **{
            key: value
            for key, value in llm_profile_updates.items()
            if value is not None
        },
    }

    # -----------------------------------------------------
    # 10. Return complete conversation result
    # -----------------------------------------------------

    return {
        "session_id": conversation.session_id,
        "language": conversation.profile.current_language,
        "profile": conversation.profile.to_dict(),
        "profile_updates": combined_updates,
        "message": response_text,
        "next_question": next_question,
    }