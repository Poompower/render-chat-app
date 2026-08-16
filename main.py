import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from openai import OpenAI

app = FastAPI()

# Read OPENAI_API_KEY and OPENAI_BASE_URL with course proxy default fallback
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://llm.nat-d.uk/v1")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

MODEL = "gemma-4-E4B-it"

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)

class ChatResponse(BaseModel):
    reply: str
    model: str

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=req.temperature,
            messages=[
                {"role": "system", "content": "You are a helpful, terse assistant."},
                {"role": "user", "content": req.message},
            ],
        )
    except Exception as e:
        print(f"Error calling upstream model: {e}", flush=True)
        raise HTTPException(status_code=502, detail=f"upstream model error: {str(e)}")
    return ChatResponse(reply=resp.choices[0].message.content, model=MODEL)

# Serve the web page from ./static at "/". Mount LAST so /api/* routes match first.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
