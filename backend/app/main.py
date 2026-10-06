from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from app.services.sarvam_service import transcribe_audio


app = FastAPI(
    title="Kshema AI Voice Bot API",
    description="Backend API for the Kshema multilingual crop-insurance voice bot.",
    version="0.1.0",
)


# Allow the React frontend to communicate with FastAPI
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


@app.post("/api/voice/transcribe")
async def transcribe_voice(
    audio: UploadFile = File(...)
):
    audio_bytes = await audio.read()

    result = transcribe_audio(
        audio_bytes=audio_bytes,
        filename=audio.filename or "audio.webm",
    )

    return result