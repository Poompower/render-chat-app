import sqlite3
import re
from typing import Dict, Any, List, Tuple
from src.config import DB_PATH

BANNED_KEYWORDS = re.compile(
    r"(?is)\b(insert|update|delete|drop|alter|create|replace|attach|"
    r"detach|pragma|vacuum|reindex|truncate|grant|revoke)\b"
)

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def get_schema_prompt() -> str:
    """Extract literal DDL from sqlite_master as taught in Lecture 11."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables_sql = [row[0] for row in cur.fetchall() if row[0]]
    conn.close()
    return "\n\n".join(tables_sql)

def clean_sql(text: str) -> str:
    """Strip markdown ```sql fences and any trailing semicolon."""
    if not isinstance(text, str):
        return ""
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:sql)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*```$", "", s)
    s = s.strip()
    # Strip trailing semicolon if present
    if s.endswith(";"):
        s = s[:-1].strip()
    return s

def guard_sql(sql: str) -> Tuple[bool, str]:
    """
    Guards SQL query against writes, injections, stacked queries, and comments (Lecture 11 & HW6).
    Returns (is_safe: bool, reason_or_cleaned_sql: str).
    """
    cleaned = clean_sql(sql)
    if not cleaned:
        return False, "Error: Empty or non-string SQL statement."

    # 1. SQL comments (-- or /* or */) -> Reject
    if "--" in cleaned or "/*" in cleaned or "*/" in cleaned:
        return False, "Security Error: SQL comments are not permitted."

    # 2. Must start with SELECT (case-insensitive)
    if not re.match(r"(?is)^\s*SELECT\b", cleaned):
        return False, "Security Error: Query must start with a SELECT statement."

    # 3. Reject embedded ';' (stacked statements)
    if ";" in cleaned:
        return False, "Security Error: Stacked or multiple statements separated by ';' are forbidden."

    # 4. Reject any banned keyword on word boundaries
    if BANNED_KEYWORDS.search(cleaned):
        return False, "Security Error: Modifying statement detected. Only read-only queries are permitted."

    # 5. Append LIMIT 100 if absent to prevent runaway result sets
    if not re.search(r"(?is)\bLIMIT\s+\d+\b", cleaned):
        cleaned += " LIMIT 100"

    return True, cleaned

def execute_guarded_sql(sql_query: str) -> Dict[str, Any]:
    """
    Safely executes a read-only SQL query against store.db.
    Returns a dict with {"columns": [...], "rows": [...], "row_count": int, "query": str}
    or raises a clear error string.
    """
    is_safe, guarded = guard_sql(sql_query)
    if not is_safe:
        return {"error": guarded, "success": False}

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(guarded)
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description] if cur.description else []
        formatted_rows = [dict(row) for row in rows]
        return {
            "success": True,
            "query": guarded,
            "columns": col_names,
            "rows": formatted_rows,
            "row_count": len(formatted_rows)
        }
    except Exception as e:
        return {"error": f"SQLite execution error: {str(e)}", "success": False, "query": guarded}
    finally:
        conn.close()

def get_order_by_id(order_id: str) -> Dict[str, Any]:
    """Look up an order with joined product details."""
    order_id = order_id.strip().upper()
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
    SELECT o.order_id, o.customer_name, o.customer_email, o.quantity, o.total_price,
           o.status, o.order_date, o.tracking_number,
           p.name AS product_name, p.category, p.warranty_months
    FROM orders o
    JOIN products p ON o.product_id = p.id
    WHERE o.order_id = ?
    """
    cur.execute(query, (order_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"found": True, "order": dict(row)}
    return {"found": False, "message": f"Order ID '{order_id}' was not found in the database."}
