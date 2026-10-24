import json
from typing import Dict, Any, List
from src.database import get_schema_prompt, execute_guarded_sql, get_order_by_id
from src.rag import get_rag_system

def get_tool_definitions() -> List[Dict[str, Any]]:
    schema_ddl = get_schema_prompt()
    return [
        {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": (
                    "Search OmniTech technical documentation, user manuals, warranty policy, "
                    "refund policy, and shipping guidelines. Call this whenever you need factual details, "
                    "hardware specifications, reset steps, or policy conditions."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search keywords or specific technical topic."
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_database",
                "description": (
                    "Execute a safe, read-only SQL SELECT query over the store SQLite database. "
                    f"Available Database Tables and Schema:\n{schema_ddl}\n"
                    "Call this for exact arithmetic, counting orders, inventory lookup, customer orders, or revenue calculations."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "A single read-only SQL SELECT statement. Never use DROP/INSERT/UPDATE."
                        }
                    },
                    "required": ["sql_query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_order_status",
                "description": (
                    "Fast lookup for an order by order ID (e.g. 'ORD-1001'). Returns order status, customer name, "
                    "tracking number, and purchased product."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The exact Order ID, formatted like ORD-XXXX"
                        }
                    },
                    "required": ["order_id"]
                }
            }
        }
    ]

def dispatch_tool(name: str, raw_args: Any) -> Dict[str, Any]:
    """
    Defensively executes a requested tool (Lecture 10 & 13):
      - Handles arguments as string or dict
      - Catches errors and returns an error dict/string instead of crashing
      - Returns structured result and citation/metadata
    """
    # 1. Parse arguments defensively
    if isinstance(raw_args, str):
        try:
            args = json.loads(raw_args) if raw_args.strip() else {}
        except Exception as e:
            return {
                "success": False,
                "error": f"Invalid JSON arguments: {str(e)}",
                "content": f"Error: Could not parse arguments as JSON: {raw_args}"
            }
    elif isinstance(raw_args, dict):
        args = raw_args
    else:
        args = {}

    # 2. Dispatch
    if name == "search_knowledge_base":
        query = args.get("query", "").strip()
        if not query:
            return {"success": False, "error": "Argument 'query' is required", "content": "Error: query cannot be empty"}
        rag = get_rag_system()
        hits = rag.search_hybrid(query, top_k=3)
        if not hits:
            return {
                "success": True,
                "citations": [],
                "content": "No relevant documents found matching query.",
                "data": []
            }
        
        passages = []
        citations = []
        for h in hits:
            citations.append(h["citation"])
            passages.append(f"Source {h['citation']}:\n{h['text']}")
        
        return {
            "success": True,
            "citations": citations,
            "content": "\n\n---\n\n".join(passages),
            "data": hits
        }

    elif name == "query_database":
        sql = args.get("sql_query", "").strip()
        if not sql:
            return {"success": False, "error": "Argument 'sql_query' is required", "content": "Error: sql_query cannot be empty"}
        res = execute_guarded_sql(sql)
        if not res.get("success", False):
            return {
                "success": False,
                "error": res.get("error"),
                "content": f"Database Error: {res.get('error')}"
            }
        
        rows = res.get("rows", [])
        if not rows:
            return {
                "success": True,
                "content": f"Query returned 0 rows. (SQL: {res.get('query')})",
                "data": [],
                "query": res.get("query")
            }
        
        return {
            "success": True,
            "content": json.dumps(rows, indent=2, ensure_ascii=False),
            "data": rows,
            "query": res.get("query")
        }

    elif name == "get_order_status":
        order_id = args.get("order_id", "").strip()
        if not order_id:
            return {"success": False, "error": "Argument 'order_id' is required", "content": "Error: order_id cannot be empty"}
        res = get_order_by_id(order_id)
        return {
            "success": True,
            "content": json.dumps(res, indent=2, ensure_ascii=False),
            "data": res
        }

    else:
        return {
            "success": False,
            "error": f"Unknown tool: '{name}'",
            "content": f"Error: Tool '{name}' is not recognized."
        }
