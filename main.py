from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from openai import OpenAI

app = FastAPI()
client = OpenAI()  # reads OPENAI_API_KEY + OPENAI_BASE_URL from the environment
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
    except Exception:
        raise HTTPException(status_code=502, detail="upstream model error")
    return ChatResponse(reply=resp.choices[0].message.content, model=MODEL)

# Serve the web page from ./static at "/". Mount LAST so /api/* routes match first.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
