import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database import guard_sql, clean_sql, execute_guarded_sql, get_order_by_id
from src.rag import get_rag_system
from src.tools import get_tool_definitions, dispatch_tool
from eval.evaluate import run_evaluation

class TestOmniTechCapstone(unittest.TestCase):

    def test_sql_guard_clean_sql(self):
        # Strip ```sql code fences and trailing semicolons
        raw = "```sql\nSELECT * FROM products;\n```"
        cleaned = clean_sql(raw)
        self.assertEqual(cleaned, "SELECT * FROM products")

    def test_sql_guard_select_only(self):
        # Disallow non-SELECT
        is_safe, msg = guard_sql("INSERT INTO products VALUES (1, 'x', 'y', 10, 1, 5, 12)")
        self.assertFalse(is_safe)
        self.assertIn("Security Error", msg)

        # Disallow DROP
        is_safe, msg = guard_sql("DROP TABLE orders")
        self.assertFalse(is_safe)

        # Disallow stacked queries with semicolon
        is_safe, msg = guard_sql("SELECT 1; DROP TABLE products")
        self.assertFalse(is_safe)

        # Disallow SQL comments (-- or /* */)
        is_safe, msg = guard_sql("SELECT * FROM products -- then drop")
        self.assertFalse(is_safe)

        # Valid SELECT must pass and have LIMIT appended
        is_safe, sql = guard_sql("SELECT id, name, price FROM products WHERE price < 5000")
        self.assertTrue(is_safe)
        self.assertIn("LIMIT 100", sql)

    def test_database_execution(self):
        res = execute_guarded_sql("SELECT COUNT(*) AS total FROM products")
        self.assertTrue(res.get("success"))
        self.assertGreater(res["rows"][0]["total"], 0)

        # Order lookup test
        order = get_order_by_id("ORD-1001")
        self.assertTrue(order["found"])
        self.assertEqual(order["order"]["customer_name"], "Somchai Prasert")

    def test_rag_retrieval(self):
        rag = get_rag_system()
        self.assertGreaterEqual(len(rag.chunks), 15)

        # Hybrid search returns hits with citation
        hits = rag.search_hybrid("warranty policy for battery", top_k=3)
        self.assertGreater(len(hits), 0)
        self.assertTrue(any("warranty" in h["citation"].lower() for h in hits))

    def test_tool_dispatch_defensive(self):
        tools = get_tool_definitions()
        self.assertEqual(len(tools), 3)

        # Dispatch search
        res = dispatch_tool("search_knowledge_base", '{"query": "30-day money back guarantee"}')
        self.assertTrue(res["success"])
        self.assertIn("citations", res)

        # Dispatch invalid json should return error string rather than crash
        res_bad = dispatch_tool("search_knowledge_base", 'malformed { json')
        self.assertFalse(res_bad["success"])
        self.assertIn("Invalid JSON", res_bad["error"])

    def test_evaluation_reproducibility(self):
        results = run_evaluation()
        self.assertEqual(results["total_test_samples"], 30)
        # Verify improved hybrid beats or equals baseline
        b_r1 = results["retrieval_comparison"]["baseline"]["recall@1"]
        i_r1 = results["retrieval_comparison"]["improved"]["recall@1"]
        self.assertGreaterEqual(i_r1, b_r1)
        self.assertEqual(results["sql_execution_accuracy"], 1.0)

if __name__ == "__main__":
    unittest.main()
