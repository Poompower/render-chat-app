import os
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import MODEL_NAME, get_openai_client_and_base
from src.agent import run_agent_turn
from src.rag import get_rag_system
from src.database import get_db_connection
from eval.evaluate import run_evaluation

app = FastAPI(
    title="OmniTech Support AI",
    description="End-to-end Capstone LLM application with Agentic RAG, Text-to-SQL, and Quantitative Evaluation",
    version="1.0.0"
)

# Enable CORS for local testing / production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User question or query")
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Temperature (0.0 for deterministic tool execution)")
    history: Optional[List[ChatMessage]] = Field(default=[], description="Recent conversation turns")

class ChatResponse(BaseModel):
    reply: str
    tools_called: List[Dict[str, Any]]
    citations: List[str]
    sql_queries: List[str]
    steps: int
    latency_ms: int
    model: str

@app.get("/api/health")
def health():
    rag = get_rag_system()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM products;")
    product_count = cur.fetchone()[0]
    conn.close()
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "knowledge_chunks_loaded": len(rag.chunks),
        "products_in_db": product_count
    }

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    history_dicts = [{"role": m.role, "content": m.content} for m in req.history] if req.history else []
    result = run_agent_turn(
        user_message=req.message,
        conversation_history=history_dicts,
        temperature=req.temperature
    )

    if result.get("error"):
        # If upstream authentication/network error occurs
        if "API Key" in result["error"]:
            raise HTTPException(status_code=500, detail=result["reply"])
        raise HTTPException(status_code=502, detail=result["reply"])

    return ChatResponse(
        reply=result["reply"],
        tools_called=result.get("tools_called", []),
        citations=result.get("citations", []),
        sql_queries=result.get("sql_queries", []),
        steps=result.get("steps", 1),
        latency_ms=result.get("latency_ms", 0),
        model=MODEL_NAME
    )

@app.get("/api/evaluation")
def get_evaluation_results():
    results = run_evaluation()
    return results

@app.post("/api/evaluate")
def trigger_evaluation():
    results = run_evaluation()
    return results

@app.get("/api/sample-queries")
def get_sample_queries():
    return [
        {
            "category": "RAG (Unstructured Docs)",
            "query": "What is the return window for opened products, and does a restocking fee apply?",
            "desc": "Tests policy retrieval and citation generation"
        },
        {
            "category": "RAG (Troubleshooting)",
            "query": "How do I factory reset my AeroPulse ANC-X headphones if one ear is silent?",
            "desc": "Tests product manual step-by-step retrieval"
        },
        {
            "category": "SQL (Database Aggregation)",
            "query": "How many orders are currently in 'processing' status, and which products have stock under 10?",
            "desc": "Tests guarded SQL generation and database computation"
        },
        {
            "category": "SQL (Order Lookup)",
            "query": "What is the tracking number and customer name for order ORD-1001?",
            "desc": "Tests exact order lookup via SQL"
        },
        {
            "category": "Compound (RAG + SQL)",
            "query": "Can customer in order ORD-1002 still return their product under our warranty policy?",
            "desc": "Multi-hop: retrieves order delivery date from DB, then checks 30-day policy"
        },
        {
            "category": "Chit-chat (No Tool)",
            "query": "Hello! Thank you for the assistance.",
            "desc": "Tests agent routing decision: answers directly without wasteful retrieval"
        }
    ]

# Serve frontend from ./static
app.mount("/", StaticFiles(directory="static", html=True), name="static")
