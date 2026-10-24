import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
DB_PATH = DATA_DIR / "store.db"
EVAL_DIR = BASE_DIR / "eval"
BENCHMARK_PATH = EVAL_DIR / "benchmark_data.json"

MODEL_NAME = os.getenv("LLM_MODEL", "gemma-4-E4B-it")

def get_openai_client_and_base():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    raw_base = os.getenv("OPENAI_BASE_URL", "").strip()

    if not raw_base or "api.openai.com" in raw_base:
        base_url = "https://llm.nat-d.uk/v1"
    else:
        base_url = raw_base

    return api_key, base_url
