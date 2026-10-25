import time
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from src.config import MODEL_NAME, get_openai_client_and_base
from src.tools import get_tool_definitions, dispatch_tool

SYSTEM_PROMPT = """You are OmniTech Support AI, an expert technical and customer support assistant for OmniTech Electronics.
You have access to three tools:
1. `search_knowledge_base`: Use for product specs, troubleshooting steps, warranty, return policies, and shipping details. Always cite the document title/section when referencing facts.
2. `query_database`: Use for exact arithmetic, inventory counts, looking up orders, customer information, or returns. Always write valid, single-statement read-only SELECT queries.
3. `get_order_status`: Quick lookup for a specific order by order_id (e.g., ORD-1001).

Guidelines:
- For simple chit-chat, greetings, or closings ('Hi', 'Thank you', 'Bye'), answer cordially without calling any tools.
- When answering factual questions from `search_knowledge_base`, explicitly cite the source tags (e.g., [warranty_and_returns.md # 1. 30-Day Money-Back Guarantee]).
- When answering questions about store data or orders, rely strictly on the database results.
- For compound questions (e.g. checking return policy AND checking order status), call both tools and synthesize a coherent response.
- If a database query or tool returns an error, examine the error message carefully, adjust your query or arguments, and retry.
- Be concise, polite, professional, and accurate.
- Reply in polite, fluent, natural Thai (ภาษาไทย) when addressed in Thai or when assisting Thai customers, while preserving technical terms, order IDs, and exact citations.
"""

def run_agent_turn(
    user_message: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    max_steps: int = 5,
    temperature: float = 0.0
) -> Dict[str, Any]:
    """
    Executes a complete ReAct agent turn using OpenAI native tool calling.
    Enforces loop termination (max_steps) and captures execution traces.
    """
    start_time = time.time()
    api_key, base_url = get_openai_client_and_base()

    if not api_key:
        return {
            "reply": "Error: OPENAI_API_KEY is not configured in environment variables.",
            "tools_called": [],
            "citations": [],
            "sql_queries": [],
            "steps": 0,
            "latency_ms": 0,
            "error": "Missing API Key"
        }

    client = OpenAI(api_key=api_key, base_url=base_url)
    tools = get_tool_definitions()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if conversation_history:
        # Append recent conversation turns (skip system messages)
        for msg in conversation_history[-6:]:
            if msg.get("role") in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg.get("content", "")})

    messages.append({"role": "user", "content": user_message})

    trace_tools_called = []
    collected_citations = []
    executed_sql = []
    step_count = 0

    while step_count < max_steps:
        step_count += 1
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "reply": f"Upstream LLM Error: {str(e)}",
                "tools_called": trace_tools_called,
                "citations": list(set(collected_citations)),
                "sql_queries": executed_sql,
                "steps": step_count,
                "latency_ms": latency_ms,
                "error": str(e)
            }

        msg = response.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        # 1. Natural termination: model emits content with no tool calls
        if not tool_calls:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "reply": msg.content or "",
                "tools_called": trace_tools_called,
                "citations": list(set(collected_citations)),
                "sql_queries": executed_sql,
                "steps": step_count,
                "latency_ms": latency_ms
            }

        # 2. Model requested one or more tool calls: append assistant turn
        messages.append(msg)

        # 3. Execute all tool calls in this turn and feed results back as role: 'tool'
        for call in tool_calls:
            call_id = call.id
            tool_name = call.function.name
            tool_args_raw = call.function.arguments

            # Dispatch tool execution defensively
            res = dispatch_tool(tool_name, tool_args_raw)

            # Record citations & sql for trace
            if "citations" in res:
                collected_citations.extend(res["citations"])
            if "query" in res:
                executed_sql.append(res["query"])

            trace_tools_called.append({
                "step": step_count,
                "tool": tool_name,
                "args": tool_args_raw,
                "success": res.get("success", False),
                "summary": res.get("content", "")[:160] + "..." if len(res.get("content", "")) > 160 else res.get("content", "")
            })

            # Append tool message (Lecture 10 & 11)
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": res.get("content", "")
            })

    # If max_steps is hit without natural stop, force a final summary answer with tool_choice="none"
    try:
        final_resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tool_choice="none",
            temperature=temperature
        )
        reply = final_resp.choices[0].message.content or "Completed with maximum step limit reached."
    except Exception:
        reply = "I retrieved the relevant data but reached the execution step limit. Please review the details above."

    latency_ms = int((time.time() - start_time) * 1000)
    return {
        "reply": reply,
        "tools_called": trace_tools_called,
        "citations": list(set(collected_citations)),
        "sql_queries": executed_sql,
        "steps": step_count,
        "latency_ms": latency_ms
    }
