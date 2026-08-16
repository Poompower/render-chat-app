import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from openai import OpenAI

app = FastAPI()

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
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    raw_base = os.getenv("OPENAI_BASE_URL", "").strip()
    if not raw_base or "api.openai.com" in raw_base:
        base_url = "https://llm.nat-d.uk/v1"
    else:
        base_url = raw_base

    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set in environment variables")

    client = OpenAI(api_key=api_key, base_url=base_url)

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
