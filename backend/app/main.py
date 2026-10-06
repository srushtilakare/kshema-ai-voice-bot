from fastapi import FastAPI

app = FastAPI(
    title="Kshema AI Voice Bot API",
    description="Backend API for the Kshema multilingual crop-insurance voice bot.",
    version="0.1.0",
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