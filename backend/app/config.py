import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')
DATA_DIR = ROOT / 'backend' / 'data'
UPLOAD_DIR = ROOT / 'uploads'
KNOWLEDGE_DIR = ROOT / 'knowledge'
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DATA_DIR / "plantmind.db"}')
# Resolve relative SQLite paths against the project, independent of launch directory.
if DATABASE_URL.startswith('sqlite:///') and not DATABASE_URL.startswith('sqlite:////'):
    db_path = DATABASE_URL.removeprefix('sqlite:///')
    if db_path != ':memory:' and not Path(db_path).is_absolute():
        DATABASE_URL = f'sqlite:///{ROOT / db_path}'

# --- Knowledge graph backend -------------------------------------------------
# 'sqlite' (local fallback, default) or 'neo4j' (requires a running Neo4j server).
GRAPH_BACKEND = os.getenv('GRAPH_BACKEND', 'sqlite')
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', '')

# --- LLM provider ------------------------------------------------------------
LLM_API_KEY = os.getenv('LLM_API_KEY', '').strip()
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')
LLM_TIMEOUT_SECONDS = float(os.getenv('LLM_TIMEOUT_SECONDS', '20'))

# --- Seeding -----------------------------------------------------------------
SEED_DEMO = os.getenv('SEED_DEMO', 'true').lower() in ('1', 'true', 'yes')

# --- CORS --------------------------------------------------------------------
CORS_ORIGINS = [o.strip() for o in os.getenv(
    'CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if o.strip()]
