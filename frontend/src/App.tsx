import { useRef, useState } from "react";
import "./App.css";

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState("Ready to talk");
  const [transcript, setTranscript] = useState("");
  const [language, setLanguage] = useState("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstart = () => {
        setIsRecording(true);
        setStatus("Listening...");
        setTranscript("");
        setLanguage("");
      };

      mediaRecorder.onstop = async () => {
        setIsRecording(false);
        setStatus("Processing your voice...");

        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType,
        });

        try {
          const formData = new FormData();

          formData.append(
            "audio",
            audioBlob,
            "farmer_voice.webm"
          );

          const response = await fetch(
            "http://127.0.0.1:8000/api/voice/transcribe",
            {
              method: "POST",
              body: formData,
            }
          );

          if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
          }

          const result = await response.json();

          console.log("Sarvam response:", result);

          setTranscript(result.transcript || "");
          setLanguage(result.language_code || "");
          setStatus("Transcription completed");
        } catch (error) {
          console.error("Transcription error:", error);
          setStatus("Something went wrong. Please try again.");
        }
      };

      mediaRecorder.start();
    } catch (error) {
      console.error("Microphone error:", error);
      setStatus("Microphone permission is required.");
    }
  };

  const stopRecording = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }
  };

  return (
    <div className="app">

      {/* Header */}
      <header className="header">
        <div className="brand">
          <div className="brand-icon">K</div>

          <div>
            <h1>Kshema</h1>
            <span>AI Voice Assistant</span>
          </div>
        </div>

        <div className="online-status">
          <span className="status-dot"></span>
          Online
        </div>
      </header>

      {/* Main */}
      <main className="main">

        {/* Welcome */}
        <section className="welcome">
          <div className="welcome-badge">
            🌾 Crop Insurance Assistant
          </div>

          <h2>
            Your voice.
            <br />
            <span>Your insurance assistant.</span>
          </h2>

          <p>
            Speak naturally in your preferred Indian language.
            Kshema will listen, understand and help you with
            crop insurance.
          </p>
        </section>

        {/* Voice Card */}
        <section className="voice-card">

          <div className="voice-card-header">
            <div>
              <span className="small-label">VOICE ASSISTANT</span>
              <h3>Talk to Kshema</h3>
            </div>

            <div className="language-pill">
              🌐 {language || "Auto detect"}
            </div>
          </div>

          {/* Voice animation */}
          <div
            className={`voice-circle ${
              isRecording ? "recording" : ""
            }`}
          >
            <div className="voice-ring ring-one"></div>
            <div className="voice-ring ring-two"></div>

            <button
              className="mic-button"
              onClick={
                isRecording ? stopRecording : startRecording
              }
              aria-label={
                isRecording
                  ? "Stop recording"
                  : "Start recording"
              }
            >
              {isRecording ? "■" : "🎙"}
            </button>
          </div>

          <div className="voice-status">
            <span
              className={`status-indicator ${
                isRecording ? "active" : ""
              }`}
            ></span>

            {status}
          </div>

          <p className="voice-hint">
            {isRecording
              ? "Speak clearly. Tap the button when you are finished."
              : "Tap the microphone and start speaking."}
          </p>

        </section>

        {/* Conversation */}
        <section className="conversation-card">

          <div className="section-heading">
            <div>
              <span className="small-label">
                CONVERSATION
              </span>

              <h3>What you said</h3>
            </div>

            {transcript && (
              <span className="detected-language">
                {language}
              </span>
            )}
          </div>

          {!transcript ? (
            <div className="empty-conversation">
              <div className="empty-icon">💬</div>

              <p>Your conversation will appear here.</p>

              <span>
                Try saying: “मला पीक विम्याबद्दल माहिती पाहिजे.”
              </span>
            </div>
          ) : (
            <div className="transcript-box">
              <div className="farmer-avatar">👨‍🌾</div>

              <div className="transcript-content">
                <span>Farmer</span>
                <p>{transcript}</p>
              </div>
            </div>
          )}

        </section>

        {/* Supported languages */}
        <section className="languages">

          <span className="small-label">
            MULTILINGUAL SUPPORT
          </span>

          <div className="language-list">
            <span>मराठी</span>
            <span>हिन्दी</span>
            <span>English</span>
            <span>தமிழ்</span>
            <span>తెలుగు</span>
            <span>ಕನ್ನಡ</span>
            <span>বাংলা</span>
            <span>+ more</span>
          </div>

        </section>

      </main>

      {/* Footer */}
      <footer>
        <span>🌾 Kshema AI</span>
        <span>Crop Insurance Assistance</span>
      </footer>

    </div>
  );
}

export default App;