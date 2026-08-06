from fastapi import FastAPI

app = FastAPI(
    title="Willovate AI Automation Engine",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Willovate AI Automation Engine is Running"
    }