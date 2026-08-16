import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import openai

app = FastAPI()

# Serve static files (index.html etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root returns the static index.html
@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse("static/index.html")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7

@app.post("/api/chat")
async def chat(request: ChatRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if not api_key or not base_url:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY or OPENAI_BASE_URL not set")
    openai.api_key = api_key
    openai.base_url = base_url
    try:
        response = await openai.ChatCompletion.acreate(
            model=request.model,
            messages=[msg.dict() for msg in request.messages],
            temperature=request.temperature,
        )
        return JSONResponse(content={"reply": response.choices[0].message.content})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
