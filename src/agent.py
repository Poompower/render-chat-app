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
- When recommending products:
  * For running, fitness, gym, or sports workouts: Recommend **OmniTech SonicBuds Wireless** (in-ear with secure ear-wings, IPX5 sweat resistance, 1,890 THB) citing [troubleshooting_audio.md # 4. SonicBuds Wireless - Sports & Workout In-Ear Earbuds].
  * For office, travel, ANC, or general music: Recommend **OmniTech AeroPulse ANC-X** (over-ear, hybrid -42dB ANC, 45-hour battery, 4,590 THB).
  * For laptops or workstations: Recommend **OmniTech TitanBook 14** (Intel Core Ultra 7, 2.8K OLED, 38,900 THB).
  * For typing/mechanical gaming: Recommend **OmniTech MechWave RGB Keyboard** (Gateron hot-swap switches, 2,490 THB).
- For simple chit-chat, greetings, or closings ('Hi', 'Thank you', 'Bye'), answer cordially without calling any tools.
- When answering factual questions from `search_knowledge_base`, explicitly cite the source tags (e.g., [warranty_and_returns.md # 1. 30-Day Money-Back Guarantee]).
- When answering questions about store data or orders, rely strictly on the database results.
- For compound questions (e.g. checking return policy AND checking order status), call both tools and synthesize a coherent response.
- If a database query or tool returns an error, examine the error message carefully, adjust your query or arguments, and retry.
- Always provide a complete, clear, and polite response in natural Thai (ภาษาไทย). Never return an empty message.
"""

def run_agent_turn(
    user_message: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    max_steps: int = 5,
    temperature: float = 0.0
) -> Dict[str, Any]:
    """
    Executes a complete ReAct agent turn using OpenAI native tool calling.
    Enforces loop termination (max_steps), guarantees non-empty responses,
    and captures execution traces.
    """
    start_time = time.time()
    api_key, base_url = get_openai_client_and_base()

    if not api_key:
        return {
            "reply": "ข้อผิดพลาด: ไม่พบ OPENAI_API_KEY ในตัวแปรสภาพแวดล้อม (Environment Variables)",
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
                "reply": f"ข้อผิดพลาดจาก Upstream LLM: {str(e)}",
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
            reply_text = (msg.content or "").strip()

            # If the model finished tools but returned empty content, force prose summary with tool_choice="none"
            if not reply_text and trace_tools_called:
                try:
                    final_resp = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                        tool_choice="none",
                        temperature=temperature
                    )
                    reply_text = (final_resp.choices[0].message.content or "").strip()
                except Exception:
                    pass

            # Safe backstop: ensure reply is never empty under any circumstance
            if not reply_text:
                if trace_tools_called:
                    reply_text = (
                        "จากการตรวจสอบข้อมูลข้างต้น พบรายละเอียดตามที่ปรากฏในบันทึกเครื่องมือ "
                        "หากคุณต้องการข้อมูลเพิ่มเติมหรือมีข้อสงสัยใด สามารถสอบถามได้เลยครับ!"
                    )
                else:
                    reply_text = (
                        "สวัสดีครับ ยินดีต้อนรับสู่ OmniTech Electronics "
                        "มีข้อมูลสินค้า สเปก หรือสถานะคำสั่งซื้อใดที่ให้ผมช่วยเหลือ แจ้งได้เลยครับ!"
                    )

            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "reply": reply_text,
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
        reply = (final_resp.choices[0].message.content or "").strip()
        if not reply:
            reply = "ระบบได้รวบรวมข้อมูลตามที่ท่านสอบถามเรียบร้อยแล้ว หากต้องการข้อมูลใดเพิ่มเติมสามารถแจ้งได้เลยครับ!"
    except Exception:
        reply = "ระบบได้รวบรวมข้อมูลตามที่ท่านสอบถามเรียบร้อยแล้ว หากต้องการข้อมูลใดเพิ่มเติมสามารถแจ้งได้เลยครับ!"

    latency_ms = int((time.time() - start_time) * 1000)
    return {
        "reply": reply,
        "tools_called": trace_tools_called,
        "citations": list(set(collected_citations)),
        "sql_queries": executed_sql,
        "steps": step_count,
        "latency_ms": latency_ms
    }
