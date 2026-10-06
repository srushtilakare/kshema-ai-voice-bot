import os
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv("backend/.env")

api_key = os.getenv("SARVAM_API_KEY")

if not api_key:
    raise ValueError("SARVAM_API_KEY not found in backend/.env")

client = SarvamAI(
    api_subscription_key=api_key
)

audio_file = "ml/sarvam_test/marathi_test.wav"

with open(audio_file, "rb") as f:
    response = client.speech_to_text.transcribe(
        file=f,
        model="saaras:v4",
        language_code="mr-IN",
        mode="transcribe"
    )

print("\n--- Sarvam STT Result ---")
print("Transcript:", response.transcript)
print("Language:", response.language_code)