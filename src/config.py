"""Central project configuration."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = BASE_DIR / os.getenv("DB_PATH", "data/tech_trends.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
FETCH_DAYS_BACK = int(os.getenv("FETCH_DAYS_BACK", "1"))
MAX_ITEMS_PER_SOURCE = int(os.getenv("MAX_ITEMS_PER_SOURCE", "50"))

# Stable topics are intentionally fixed to preserve day-over-day comparability.
TOPICS = [
    "AI Agents",
    "Open-source Models",
    "AI Coding Tools",
    "Chips / Compute / Infra",
    "Robotics",
    "Security / AI Safety",
    "Data Infra / Vector DB / RAG",
    "Research Breakthroughs",
    "Other",
]

SOURCE_WEIGHTS: dict[str, float] = {
    "openai_blog": 1.00,
    "anthropic_blog": 1.00,
    "google_ai_blog": 0.95,
    "meta_ai_blog": 0.90,
    "microsoft_ai_blog": 0.90,
    "nvidia_blog": 0.85,
    "huggingface_blog": 0.85,
    "arxiv": 0.80,
    "github": 0.75,
    "dblp": 0.70,
    "hacker_news": 0.65,
    "default": 0.60,
}

SCORE_WEIGHTS = {
    "importance": 0.45,
    "momentum": 0.35,
    "novelty": 0.20,
}

EMERGING_DISCOVERY = {
    "lookback_days": 7,
    "recent_days": 3,
    "min_keyword_freq": 5,
    "min_growth_ratio": 2.0,
    "min_source_count": 2,
    "top_n_emerging": 10,
}

LLM_SELECTION = {
    "max_items_per_run": int(os.getenv("MAX_LLM_ITEMS_PER_RUN", "30")),
    "score_threshold": float(os.getenv("LLM_SCORE_THRESHOLD", "30.0")),
    "top_pool_ratio": 0.4,
    "stable_pool_ratio": 0.4,
    "emerging_pool_ratio": 0.2,
    "min_items_per_stable_topic": 1,
    "max_topic_share": 0.35,
    "auto_expand_budget": True,
    "hard_cap": 80,
}

ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO", "cs.CR"]

DBLP_SEARCH_QUERIES = [
    "large language models",
    "prompt engineering",
    "retrieval augmented generation",
    "agents",
    "robotics",
]

GITHUB_KEYWORDS = [
    "llm agent",
    "open source llm",
    "ai coding",
    "vector database",
    "rag retrieval",
    "robotics ml",
    "inference optimization",
    "ai safety",
]

BLOG_FEEDS = [
    {"name": "openai_blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "anthropic_blog", "url": "https://www.anthropic.com/news/rss"},
    {"name": "google_ai_blog", "url": "https://blog.google/technology/ai/rss/"},
    {"name": "meta_ai_blog", "url": "https://ai.meta.com/blog/rss/"},
    {"name": "microsoft_ai_blog", "url": "https://blogs.microsoft.com/ai/feed/"},
    {"name": "huggingface_blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "nvidia_blog", "url": "https://blogs.nvidia.com/feed/"},
]

HN_MIN_POINTS = 50
HN_MAX_ITEMS = 30

TITLE_SIMILARITY_THRESHOLD = 0.85

TOPIC_ALIASES = {
    "AI Agents": "AI Agents",
    "Open-source Models": "Open-source Models",
    "AI Coding Tools": "AI Coding Tools",
    "Chips / Compute / Infra": "Chips / Compute / Infra",
    "Robotics": "Robotics",
    "Security / AI Safety": "Security / AI Safety",
    "Data Infra / Vector DB / RAG": "Data Infra / Vector DB / RAG",
    "Research Breakthroughs": "Research Breakthroughs",
    "Other": "Other",
}
