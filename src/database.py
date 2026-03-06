"""SQLite persistence layer."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Optional

from loguru import logger

from src.config import DB_PATH
from src.models import DailyTopicStat, EmergingTopicStat, Item, LLMSelectionStat


ITEM_COLUMNS = {
    "stable_topic": "TEXT DEFAULT 'Other'",
    "emerging_topic": "TEXT DEFAULT ''",
    "tags": "TEXT DEFAULT '[]'",
    "llm_selected": "INTEGER DEFAULT 0",
    "selection_bucket": "TEXT DEFAULT ''",
    "selection_reason": "TEXT DEFAULT ''",
}


@contextmanager
def get_connection():
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


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


def _ensure_item_columns(conn: sqlite3.Connection) -> None:
    for column, sql_type in ITEM_COLUMNS.items():
        if not _column_exists(conn, "items", column):
            conn.execute(f"ALTER TABLE items ADD COLUMN {column} {sql_type}")

    # Backfill legacy values when old rows already exist.
    conn.execute(
        """
        UPDATE items
        SET stable_topic = COALESCE(NULLIF(stable_topic, ''), COALESCE(NULLIF(topic, ''), 'Other'))
        WHERE stable_topic IS NULL OR stable_topic = ''
        """
    )
    conn.execute(
        """
        UPDATE items
        SET tags = CASE
            WHEN tags IS NULL OR tags = '' THEN COALESCE(NULLIF(keywords, ''), '[]')
            ELSE tags
        END
        """
    )


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                raw_summary TEXT DEFAULT '',
                one_line_summary TEXT DEFAULT '',
                topic TEXT DEFAULT 'Other',
                subtopic TEXT DEFAULT '',
                keywords TEXT DEFAULT '[]',
                entities TEXT DEFAULT '[]',
                importance_score REAL DEFAULT 0.0,
                novelty_score REAL DEFAULT 0.0,
                momentum_score REAL DEFAULT 0.0,
                source_weight REAL DEFAULT 0.6,
                final_score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS daily_topic_stats (
                date TEXT NOT NULL,
                topic TEXT NOT NULL,
                item_count INTEGER DEFAULT 0,
                avg_importance REAL DEFAULT 0.0,
                avg_novelty REAL DEFAULT 0.0,
                avg_momentum REAL DEFAULT 0.0,
                final_score REAL DEFAULT 0.0,
                trend_delta_7d REAL DEFAULT 0.0,
                top_summary TEXT DEFAULT '',
                PRIMARY KEY (date, topic)
            );

            CREATE TABLE IF NOT EXISTS emerging_topic_stats (
                date TEXT NOT NULL,
                emerging_topic TEXT NOT NULL,
                item_count INTEGER DEFAULT 0,
                growth_rate REAL DEFAULT 0.0,
                source_count INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0.0,
                top_summary TEXT DEFAULT '',
                PRIMARY KEY (date, emerging_topic)
            );

            CREATE TABLE IF NOT EXISTS llm_selection_stats (
                date TEXT NOT NULL PRIMARY KEY,
                total_items INTEGER DEFAULT 0,
                stable_topic_count INTEGER DEFAULT 0,
                emerging_topic_count INTEGER DEFAULT 0,
                llm_items_selected INTEGER DEFAULT 0,
                top_bucket_count INTEGER DEFAULT 0,
                stable_bucket_count INTEGER DEFAULT 0,
                emerging_bucket_count INTEGER DEFAULT 0,
                coverage_ratio REAL DEFAULT 0.0,
                notes TEXT DEFAULT ''
            );
            """
        )
        _ensure_item_columns(conn)
        conn.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_items_date ON items(date);
            CREATE INDEX IF NOT EXISTS idx_items_topic ON items(topic);
            CREATE INDEX IF NOT EXISTS idx_items_stable_topic ON items(stable_topic);
            CREATE INDEX IF NOT EXISTS idx_items_emerging_topic ON items(emerging_topic);
            CREATE INDEX IF NOT EXISTS idx_items_source ON items(source);
            CREATE INDEX IF NOT EXISTS idx_items_llm_selected ON items(llm_selected);
            CREATE INDEX IF NOT EXISTS idx_stats_date ON daily_topic_stats(date);
            CREATE INDEX IF NOT EXISTS idx_stats_topic ON daily_topic_stats(topic);
            CREATE INDEX IF NOT EXISTS idx_emerging_stats_date ON emerging_topic_stats(date);
            CREATE INDEX IF NOT EXISTS idx_llm_selection_stats_date ON llm_selection_stats(date);
            """
        )
    logger.info("database initialized at {}", DB_PATH)


def migrate_db() -> None:
    init_db()


def _serialize_item(item: Item) -> dict[str, Any]:
    item.sync_legacy_fields()
    payload = item.model_dump()
    payload["keywords"] = json.dumps(payload["keywords"], ensure_ascii=False)
    payload["tags"] = json.dumps(payload["tags"], ensure_ascii=False)
    payload["entities"] = json.dumps(payload["entities"], ensure_ascii=False)
    return payload


def upsert_item(item: Item) -> bool:
    sql = """
        INSERT INTO items (
            id, date, source, title, url, raw_summary, one_line_summary,
            topic, stable_topic, emerging_topic, subtopic,
            keywords, tags, entities, llm_selected, selection_bucket, selection_reason,
            importance_score, novelty_score, momentum_score, source_weight, final_score, created_at
        ) VALUES (
            :id, :date, :source, :title, :url, :raw_summary, :one_line_summary,
            :topic, :stable_topic, :emerging_topic, :subtopic,
            :keywords, :tags, :entities, :llm_selected, :selection_bucket, :selection_reason,
            :importance_score, :novelty_score, :momentum_score, :source_weight, :final_score, :created_at
        )
        ON CONFLICT(id) DO UPDATE SET
            date = excluded.date,
            source = excluded.source,
            title = excluded.title,
            url = excluded.url,
            raw_summary = excluded.raw_summary,
            one_line_summary = excluded.one_line_summary,
            topic = excluded.topic,
            stable_topic = excluded.stable_topic,
            emerging_topic = excluded.emerging_topic,
            subtopic = excluded.subtopic,
            keywords = excluded.keywords,
            tags = excluded.tags,
            entities = excluded.entities,
            llm_selected = excluded.llm_selected,
            selection_bucket = excluded.selection_bucket,
            selection_reason = excluded.selection_reason,
            importance_score = excluded.importance_score,
            novelty_score = excluded.novelty_score,
            momentum_score = excluded.momentum_score,
            source_weight = excluded.source_weight,
            final_score = excluded.final_score,
            created_at = excluded.created_at
    """
    with get_connection() as conn:
        cur = conn.execute(sql, _serialize_item(item))
        return cur.rowcount > 0


def bulk_upsert_items(items: list[Item]) -> int:
    count = 0
    for item in items:
        if upsert_item(item):
            count += 1
    return count


def update_item_topics(item_ids: list[str], emerging_topic: str) -> None:
    if not item_ids:
        return
    placeholders = ",".join("?" for _ in item_ids)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE items SET emerging_topic = ? WHERE id IN ({placeholders})",
            [emerging_topic, *item_ids],
        )


def reset_llm_selection(date: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE items
            SET llm_selected = 0, selection_bucket = '', selection_reason = ''
            WHERE date = ?
            """,
            (date,),
        )


def mark_llm_selection(
    date: str,
    item_ids: list[str],
    bucket: str,
    reason: str,
) -> None:
    if not item_ids:
        return
    placeholders = ",".join("?" for _ in item_ids)
    with get_connection() as conn:
        conn.execute(
            f"""
            UPDATE items
            SET llm_selected = 1, selection_bucket = ?, selection_reason = ?
            WHERE date = ? AND id IN ({placeholders})
            """,
            [bucket, reason, date, *item_ids],
        )


def upsert_daily_stat(stat: DailyTopicStat) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO daily_topic_stats
            (date, topic, item_count, avg_importance, avg_novelty,
             avg_momentum, final_score, trend_delta_7d, top_summary)
            VALUES
            (:date, :topic, :item_count, :avg_importance, :avg_novelty,
             :avg_momentum, :final_score, :trend_delta_7d, :top_summary)
            """,
            stat.model_dump(),
        )


def upsert_emerging_topic_stat(stat: EmergingTopicStat) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO emerging_topic_stats
            (date, emerging_topic, item_count, growth_rate, source_count, avg_score, top_summary)
            VALUES
            (:date, :emerging_topic, :item_count, :growth_rate, :source_count, :avg_score, :top_summary)
            """,
            stat.model_dump(),
        )


def upsert_llm_selection_stat(stat: LLMSelectionStat) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO llm_selection_stats
            (date, total_items, stable_topic_count, emerging_topic_count, llm_items_selected,
             top_bucket_count, stable_bucket_count, emerging_bucket_count, coverage_ratio, notes)
            VALUES
            (:date, :total_items, :stable_topic_count, :emerging_topic_count, :llm_items_selected,
             :top_bucket_count, :stable_bucket_count, :emerging_bucket_count, :coverage_ratio, :notes)
            """,
            stat.model_dump(),
        )


def _loads_json_field(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _normalize_item_row(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["keywords"] = _loads_json_field(item.get("keywords", "[]")) or []
    item["tags"] = _loads_json_field(item.get("tags", "[]")) or []
    item["entities"] = _loads_json_field(item.get("entities", "[]")) or []
    if not item.get("stable_topic"):
        item["stable_topic"] = item.get("topic", "Other")
    return item


def query_items(
    date: Optional[str] = None,
    stable_topic: Optional[str] = None,
    emerging_topic: Optional[str] = None,
    source: Optional[str] = None,
    llm_selected: Optional[int] = None,
    min_score: float = 0.0,
    limit: int = 200,
    search: Optional[str] = None,
    topic: Optional[str] = None,
) -> list[dict]:
    clauses = ["final_score >= :min_score"]
    params: dict[str, Any] = {"min_score": min_score, "limit": limit}

    stable_topic = stable_topic or topic
    if date:
        clauses.append("date = :date")
        params["date"] = date
    if stable_topic and stable_topic != "全部":
        clauses.append("stable_topic = :stable_topic")
        params["stable_topic"] = stable_topic
    if emerging_topic and emerging_topic != "全部":
        clauses.append("emerging_topic = :emerging_topic")
        params["emerging_topic"] = emerging_topic
    if source and source != "全部":
        clauses.append("source = :source")
        params["source"] = source
    if llm_selected is not None:
        clauses.append("llm_selected = :llm_selected")
        params["llm_selected"] = llm_selected
    if search:
        clauses.append("(title LIKE :search OR raw_summary LIKE :search)")
        params["search"] = f"%{search}%"

    sql = f"""
        SELECT *
        FROM items
        WHERE {' AND '.join(clauses)}
        ORDER BY date DESC, final_score DESC
        LIMIT :limit
    """
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_normalize_item_row(row) for row in rows]


def query_daily_stats(days: int = 30, topic: Optional[str] = None) -> list[dict]:
    clauses = [f"date >= date('now', '-{days} days')"]
    params: dict[str, Any] = {}
    if topic and topic != "全部":
        clauses.append("topic = :topic")
        params["topic"] = topic
    sql = f"""
        SELECT *
        FROM daily_topic_stats
        WHERE {' AND '.join(clauses)}
        ORDER BY date ASC, final_score DESC
    """
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def query_emerging_stats(days: int = 30, emerging_topic: Optional[str] = None) -> list[dict]:
    clauses = [f"date >= date('now', '-{days} days')"]
    params: dict[str, Any] = {}
    if emerging_topic and emerging_topic != "全部":
        clauses.append("emerging_topic = :emerging_topic")
        params["emerging_topic"] = emerging_topic
    sql = f"""
        SELECT *
        FROM emerging_topic_stats
        WHERE {' AND '.join(clauses)}
        ORDER BY date ASC, growth_rate DESC
    """
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def query_llm_selection_stat(date: Optional[str] = None) -> Optional[dict]:
    sql = "SELECT * FROM llm_selection_stats"
    params: tuple[Any, ...] = ()
    if date:
        sql += " WHERE date = ?"
        params = (date,)
    sql += " ORDER BY date DESC LIMIT 1"
    with get_connection() as conn:
        row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def get_distinct_sources() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT source FROM items ORDER BY source").fetchall()
    return [row["source"] for row in rows]


def get_distinct_dates() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT date FROM items ORDER BY date DESC").fetchall()
    return [row["date"] for row in rows]


def get_distinct_emerging_topics(limit: int = 50) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT emerging_topic
            FROM items
            WHERE emerging_topic IS NOT NULL AND emerging_topic != ''
            ORDER BY emerging_topic
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row["emerging_topic"] for row in rows]


def get_latest_date() -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute("SELECT MAX(date) AS d FROM items").fetchone()
    return row["d"] if row and row["d"] else None
