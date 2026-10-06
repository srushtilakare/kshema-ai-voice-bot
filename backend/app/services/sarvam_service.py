import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from sarvamai import SarvamAI


# Load .env from the backend directory
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def transcribe_audio(audio_bytes: bytes, filename: str):
    api_key = os.getenv("SARVAM_API_KEY")

    if not api_key:
        raise ValueError(
            f"SARVAM_API_KEY is not configured. "
            f"Checked: {ENV_FILE}"
        )

    client = SarvamAI(
        api_subscription_key=api_key
    )

    file_extension = os.path.splitext(filename)[1]

    if not file_extension:
        file_extension = ".webm"

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        with open(temp_path, "rb") as audio_file:
            response = client.speech_to_text.transcribe(
                file=audio_file,
                model="saaras:v4",
                mode="transcribe",
                language_code="unknown",
            )

        return {
            "transcript": response.transcript,
            "language_code": response.language_code,
            "language_probability": response.language_probability,
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)