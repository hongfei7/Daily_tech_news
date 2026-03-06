"""End-to-end data pipeline."""

from __future__ import annotations

from loguru import logger

from src.aggregator import aggregate_daily_stats
from src.classifier import classify_item_multi
from src.config import EMERGING_DISCOVERY, FETCH_DAYS_BACK
from src.coverage import build_coverage_summary
from src.database import (
    bulk_upsert_items,
    get_connection,
    query_items,
    reset_llm_selection,
    upsert_emerging_topic_stat,
    upsert_item,
    upsert_llm_selection_stat,
)
from src.emerging import build_emerging_stats, discover_emerging_topics
from src.fetchers.arxiv_fetcher import fetch_arxiv
from src.fetchers.blogs_fetcher import fetch_blogs
from src.fetchers.dblp_fetcher import fetch_dblp
from src.fetchers.github_fetcher import fetch_github
from src.fetchers.hn_fetcher import fetch_hacker_news
from src.llm_selector import select_representative_items
from src.models import Item, LLMSelectionStat
from src.scoring import score_item
from src.summarizer import generate_one_line_summary
from src.utils import deduplicate_items


def _fetch_all(days_back: int) -> list[dict]:
    raw_data: list[dict] = []
    for name, fetcher in [
        ("arxiv", fetch_arxiv),
        ("github", fetch_github),
        ("blogs", fetch_blogs),
        ("hacker_news", fetch_hacker_news),
        ("dblp", fetch_dblp),
    ]:
        try:
            items = fetcher(days_back)
            raw_data.extend(items)
            logger.info("fetched {} items from {}", len(items), name)
        except Exception as exc:
            logger.exception("fetch step failed for {}: {}", name, exc)
    return raw_data


def _load_scoring_context() -> tuple[list[str], dict[str, int]]:
    with get_connection() as conn:
        title_rows = conn.execute("SELECT title FROM items ORDER BY date DESC LIMIT 3000").fetchall()
        topic_rows = conn.execute(
            """
            SELECT COALESCE(NULLIF(stable_topic, ''), COALESCE(NULLIF(topic, ''), 'Other')) AS stable_topic,
                   COUNT(*) AS cnt
            FROM items
            WHERE date >= date('now', '-7 days')
            GROUP BY COALESCE(NULLIF(stable_topic, ''), COALESCE(NULLIF(topic, ''), 'Other'))
            """
        ).fetchall()
    existing_titles = [row["title"] for row in title_rows]
    topic_counts = {row["stable_topic"]: row["cnt"] for row in topic_rows}
    return existing_titles, topic_counts


def _build_item(data: dict, existing_titles: list[str], topic_counts: dict[str, int]) -> Item:
    classified = classify_item_multi(data["title"], data["raw_summary"], source=data.get("source"))
    item = Item(
        id=data["id"],
        date=data["date"],
        source=data["source"],
        title=data["title"],
        url=data["url"],
        raw_summary=data.get("raw_summary", ""),
        one_line_summary=generate_one_line_summary(data["title"], data.get("raw_summary", ""), use_llm=False),
        stable_topic=classified["stable_topic"],
        emerging_topic=classified["emerging_topic"],
        tags=classified["tags"],
        topic=classified["stable_topic"],
        keywords=classified["tags"],
    )
    return score_item(item, existing_titles, topic_counts)


def _run_llm_item_summary(selected_items: list[dict], all_items_by_id: dict[str, Item]) -> None:
    for row in selected_items:
        item = all_items_by_id.get(row["id"])
        if item is None:
            item = Item(**row)
            all_items_by_id[row["id"]] = item
        item.one_line_summary = generate_one_line_summary(item.title, item.raw_summary, use_llm=True)


def run_pipeline(days_back: int = FETCH_DAYS_BACK) -> dict:
    logger.info("starting tech trend pipeline, days_back={}", days_back)
    raw_data = _fetch_all(days_back)
    if not raw_data:
        logger.warning("pipeline finished without fetched data")
        return {"status": "empty", "items": 0}

    unique_data = deduplicate_items(raw_data)
    logger.info("deduplicated {} -> {} items", len(raw_data), len(unique_data))

    existing_titles, topic_counts = _load_scoring_context()
    processed_items = [_build_item(data, existing_titles, topic_counts) for data in unique_data]
    bulk_upsert_items(processed_items)

    affected_dates = sorted({item.date for item in processed_items})
    summary: dict[str, object] = {"status": "ok", "dates": affected_dates, "items": len(processed_items)}

    all_items_by_id = {item.id: item for item in processed_items}

    for target_date in affected_dates:
        logger.info("processing date {}", target_date)
        day_items = query_items(date=target_date, limit=5000)
        if not day_items:
            continue

        lookback_items = query_items(limit=10000)
        emerging_candidates = discover_emerging_topics(lookback_items, target_date, EMERGING_DISCOVERY)
        for stat in build_emerging_stats(target_date, emerging_candidates):
            upsert_emerging_topic_stat(stat)
        candidate_map = {candidate.topic: candidate for candidate in emerging_candidates}

        for item in processed_items:
            if item.date != target_date:
                continue
            if item.emerging_topic and item.emerging_topic in candidate_map:
                continue
            matched_topic = next(
                (
                    candidate.topic
                    for candidate in emerging_candidates
                    if any(tag == candidate.topic for tag in item.tags)
                ),
                item.emerging_topic,
            )
            item.emerging_topic = matched_topic or item.emerging_topic
            upsert_item(item)

        day_items = query_items(date=target_date, limit=5000)
        reset_llm_selection(target_date)
        selection = select_representative_items(day_items, target_date)
        for selected in selection.selected_items:
            item = all_items_by_id.get(selected["id"])
            if item is not None:
                bucket, reason = selection.bucket_map[selected["id"]]
                item.llm_selected = 1
                item.selection_bucket = bucket
                item.selection_reason = reason
        _run_llm_item_summary(selection.selected_items, all_items_by_id)
        for item in processed_items:
            if item.date == target_date:
                bucket_reason = selection.bucket_map.get(item.id)
                if bucket_reason:
                    item.llm_selected = 1
                    item.selection_bucket = bucket_reason[0]
                    item.selection_reason = bucket_reason[1]
                upsert_item(item)

        day_items = query_items(date=target_date, limit=5000)
        coverage = build_coverage_summary(day_items, selection.selected_items, selection.stats)
        upsert_llm_selection_stat(
            LLMSelectionStat(
                date=target_date,
                total_items=coverage["total_items"],
                stable_topic_count=coverage["stable_topic_coverage"],
                emerging_topic_count=coverage["emerging_topic_coverage"],
                llm_items_selected=coverage["llm_items_selected"],
                top_bucket_count=coverage["bucket_distribution"]["top_pool"],
                stable_bucket_count=coverage["bucket_distribution"]["stable_pool"],
                emerging_bucket_count=coverage["bucket_distribution"]["emerging_pool"],
                coverage_ratio=coverage["coverage_ratio"],
                notes=coverage["human_readable_summary"],
            )
        )
        aggregate_daily_stats(target_date)

    logger.info("pipeline completed for {} dates", len(affected_dates))
    return summary


if __name__ == "__main__":
    from src.utils import setup_logger

    setup_logger()
    run_pipeline()
