"""
utils.py - 通用工具函数：日志配置、文本清洗、ID 生成、去重等
"""

import hashlib
import re
import sys
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from src.config import LOG_DIR, LOG_LEVEL


# ─── 日志初始化 ───────────────────────────────────────────
def setup_logger(name: str = "pipeline"):
    """配置 loguru logger（控制台 + 文件双输出）"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
        colorize=True,
    )
    logger.add(
        LOG_DIR / f"{name}.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )
    return logger


# ─── ID 生成 ──────────────────────────────────────────────
def make_id(url: str) -> str:
    """基于 URL 生成稳定的 8 位十六进制 ID"""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


# ─── 文本清洗 ─────────────────────────────────────────────
def clean_text(text: str) -> str:
    """去除 HTML 标签、多余空白和特殊字符"""
    if not text:
        return ""
    # 去 HTML 标签
    text = re.sub(r"<[^>]+>", " ", text)
    # 去多余空白
    text = re.sub(r"\s+", " ", text).strip()
    # 去无意义的控制字符
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)
    return text


def truncate(text: str, max_chars: int = 400) -> str:
    """截断文本到指定长度，末尾加省略号"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


# ─── 时间解析 ─────────────────────────────────────────────
def parse_date(date_str: Optional[str]) -> str:
    """
    将各种格式的日期字符串统一为 YYYY-MM-DD。
    解析失败则返回今天的日期。
    """
    if not date_str:
        return today_str()

    fmts = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            continue

    # feedparser 使用 time.struct_time
    try:
        import time
        t = time.mktime(date_str)
        return datetime.fromtimestamp(t).strftime("%Y-%m-%d")
    except Exception:
        pass

    return today_str()


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ─── 去重 ─────────────────────────────────────────────────
def normalize_title(title: str) -> str:
    """标准化标题：小写、去标点，用于相似度比较"""
    t = title.lower()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def title_similarity(a: str, b: str) -> float:
    """
    计算两个标题的相似度（Jaccard on tokens）。
    返回 0~1 之间的浮点数。
    """
    tokens_a = set(normalize_title(a).split())
    tokens_b = set(normalize_title(b).split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def deduplicate_items(items: list[dict], threshold: float = 0.85) -> list[dict]:
    """
    按标题相似度去重，保留 final_score 更高的那条。
    threshold: Jaccard 相似度阈值。
    """
    kept: list[dict] = []
    for item in sorted(items, key=lambda x: x.get("final_score", 0), reverse=True):
        duplicate = False
        for k in kept:
            if title_similarity(item["title"], k["title"]) >= threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(item)
    return kept
