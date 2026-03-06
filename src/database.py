"""
database.py - SQLite 数据库操作层
提供初始化、写入、查询的完整接口
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from loguru import logger

from src.config import DB_PATH
from src.models import DailyTopicStat, Item


# ─── 连接上下文管理器 ──────────────────────────────────────
@contextmanager
def get_connection():
    """返回一个线程安全的 SQLite 连接上下文"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── 初始化 ────────────────────────────────────────────────
def init_db():
    """创建数据库和所需表（幂等操作）"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id              TEXT PRIMARY KEY,
                date            TEXT NOT NULL,
                source          TEXT NOT NULL,
                title           TEXT NOT NULL,
                url             TEXT UNIQUE NOT NULL,
                raw_summary     TEXT DEFAULT '',
                one_line_summary TEXT DEFAULT '',
                topic           TEXT DEFAULT 'Other',
                subtopic        TEXT DEFAULT '',
                keywords        TEXT DEFAULT '[]',
                entities        TEXT DEFAULT '[]',
                importance_score REAL DEFAULT 0.0,
                novelty_score   REAL DEFAULT 0.0,
                momentum_score  REAL DEFAULT 0.0,
                source_weight   REAL DEFAULT 0.6,
                final_score     REAL DEFAULT 0.0,
                created_at      TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_items_date  ON items(date);
            CREATE INDEX IF NOT EXISTS idx_items_topic ON items(topic);
            CREATE INDEX IF NOT EXISTS idx_items_source ON items(source);

            CREATE TABLE IF NOT EXISTS daily_topic_stats (
                date            TEXT NOT NULL,
                topic           TEXT NOT NULL,
                item_count      INTEGER DEFAULT 0,
                avg_importance  REAL DEFAULT 0.0,
                avg_novelty     REAL DEFAULT 0.0,
                avg_momentum    REAL DEFAULT 0.0,
                final_score     REAL DEFAULT 0.0,
                trend_delta_7d  REAL DEFAULT 0.0,
                top_summary     TEXT DEFAULT '',
                PRIMARY KEY (date, topic)
            );

            CREATE INDEX IF NOT EXISTS idx_stats_date  ON daily_topic_stats(date);
            CREATE INDEX IF NOT EXISTS idx_stats_topic ON daily_topic_stats(topic);
        """)
    logger.info(f"数据库初始化完成: {DB_PATH}")


# ─── 写入 ──────────────────────────────────────────────────
def upsert_item(item: Item) -> bool:
    """
    写入或更新单条 Item。
    若 URL 已存在则跳过（保持原有数据）。
    返回 True 表示新写入，False 表示已存在。
    """
    sql = """
        INSERT OR IGNORE INTO items
            (id, date, source, title, url, raw_summary, one_line_summary,
             topic, subtopic, keywords, entities,
             importance_score, novelty_score, momentum_score,
             source_weight, final_score, created_at)
        VALUES
            (:id, :date, :source, :title, :url, :raw_summary, :one_line_summary,
             :topic, :subtopic, :keywords, :entities,
             :importance_score, :novelty_score, :momentum_score,
             :source_weight, :final_score, :created_at)
    """
    params = item.model_dump()
    params["keywords"] = json.dumps(params["keywords"], ensure_ascii=False)
    params["entities"] = json.dumps(params["entities"], ensure_ascii=False)

    with get_connection() as conn:
        cur = conn.execute(sql, params)
        return cur.rowcount > 0


def upsert_daily_stat(stat: DailyTopicStat):
    """写入或覆盖单条每日统计"""
    sql = """
        INSERT OR REPLACE INTO daily_topic_stats
            (date, topic, item_count, avg_importance, avg_novelty,
             avg_momentum, final_score, trend_delta_7d, top_summary)
        VALUES
            (:date, :topic, :item_count, :avg_importance, :avg_novelty,
             :avg_momentum, :final_score, :trend_delta_7d, :top_summary)
    """
    with get_connection() as conn:
        conn.execute(sql, stat.model_dump())


def bulk_upsert_items(items: list[Item]) -> int:
    """批量写入 items，返回实际新写入条数"""
    count = 0
    for item in items:
        if upsert_item(item):
            count += 1
    return count


# ─── 查询 ──────────────────────────────────────────────────
def query_items(
    date: Optional[str] = None,
    topic: Optional[str] = None,
    source: Optional[str] = None,
    min_score: float = 0.0,
    limit: int = 200,
    search: Optional[str] = None,
) -> list[dict]:
    """灵活查询 items 表，返回字典列表"""
    clauses = ["final_score >= :min_score"]
    params: dict = {"min_score": min_score, "limit": limit}

    if date:
        clauses.append("date = :date")
        params["date"] = date
    if topic and topic != "全部":
        clauses.append("topic = :topic")
        params["topic"] = topic
    if source and source != "全部":
        clauses.append("source = :source")
        params["source"] = source
    if search:
        clauses.append("title LIKE :search")
        params["search"] = f"%{search}%"

    where = " AND ".join(clauses)
    sql = f"""
        SELECT * FROM items
        WHERE {where}
        ORDER BY final_score DESC
        LIMIT :limit
    """
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def query_daily_stats(
    days: int = 30,
    topic: Optional[str] = None,
) -> list[dict]:
    """查询最近 N 天的 daily_topic_stats，用于趋势图"""
    params: dict = {"days": days}
    clauses = [f"date >= date('now', '-{days} days')"]
    if topic and topic != "全部":
        clauses.append("topic = :topic")
        params["topic"] = topic

    where = " AND ".join(clauses)
    sql = f"""
        SELECT * FROM daily_topic_stats
        WHERE {where}
        ORDER BY date ASC
    """
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_distinct_sources() -> list[str]:
    """返回数据库中所有来源名"""
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT source FROM items ORDER BY source").fetchall()
    return [r["source"] for r in rows]


def get_distinct_dates() -> list[str]:
    """返回数据库中所有日期（降序）"""
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT date FROM items ORDER BY date DESC").fetchall()
    return [r["date"] for r in rows]


def get_latest_date() -> Optional[str]:
    """返回数据库中最新的日期"""
    with get_connection() as conn:
        row = conn.execute("SELECT MAX(date) as d FROM items").fetchone()
    return row["d"] if row else None
