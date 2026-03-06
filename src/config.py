"""
config.py - 全局配置中心，从环境变量和 .env 文件中读取配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 加载 .env 文件
load_dotenv(BASE_DIR / ".env")

# ─── 数据库 ─────────────────────────────────────────────
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "data/tech_trends.db")

# ─── 日志 ────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"

# ─── 抓取参数 ────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
FETCH_DAYS_BACK = int(os.getenv("FETCH_DAYS_BACK", "1"))
MAX_ITEMS_PER_SOURCE = int(os.getenv("MAX_ITEMS_PER_SOURCE", "50"))

# ─── 主题体系 ─────────────────────────────────────────────
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

# ─── 来源权重 ─────────────────────────────────────────────
SOURCE_WEIGHTS: dict[str, float] = {
    "openai_blog":        1.0,
    "anthropic_blog":     1.0,
    "google_ai_blog":     0.95,
    "meta_ai_blog":       0.90,
    "microsoft_ai_blog":  0.90,
    "nvidia_blog":        0.85,
    "huggingface_blog":   0.85,
    "arxiv":              0.80,
    "github":             0.75,
    "hacker_news":        0.65,
    "default":            0.60,
}

# ─── 评分权重 ─────────────────────────────────────────────
SCORE_WEIGHTS = {
    "importance": 0.45,
    "momentum":   0.35,
    "novelty":    0.20,
}

# ─── arXiv 分类 ───────────────────────────────────────────
ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO", "cs.CR"]

# ─── GitHub 搜索关键词 ─────────────────────────────────────
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

# ─── 博客 RSS / Feed 列表 ─────────────────────────────────
BLOG_FEEDS = [
    {"name": "openai_blog",       "url": "https://openai.com/blog/rss.xml"},
    {"name": "anthropic_blog",    "url": "https://www.anthropic.com/news/rss"},
    {"name": "google_ai_blog",    "url": "https://blog.google/technology/ai/rss/"},
    {"name": "meta_ai_blog",      "url": "https://ai.meta.com/blog/rss/"},
    {"name": "microsoft_ai_blog", "url": "https://blogs.microsoft.com/ai/feed/"},
    {"name": "huggingface_blog",  "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "nvidia_blog",       "url": "https://blogs.nvidia.com/feed/"},
]

# ─── Hacker News ────────────────────────────────────────
HN_MIN_POINTS = 50        # 最低票数阈值
HN_MAX_ITEMS  = 30        # 每次最多取条数

# ─── 去重阈值 ────────────────────────────────────────────
TITLE_SIMILARITY_THRESHOLD = 0.85   # 标题相似度超过此值则视为重复
