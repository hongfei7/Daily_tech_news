"""Aggregation helpers for stable topics, emerging topics, and source coverage."""

from __future__ import annotations

import math
from collections import defaultdict

from src.config import TOPICS
from src.database import (
    query_daily_stats,
    query_emerging_stats,
    query_items,
    query_llm_selection_stat,
    upsert_daily_stat,
)
from src.models import DailyTopicStat
from src.summarizer import summarize_stable_topic


def aggregate_daily_stats(target_date: str) -> list[DailyTopicStat]:
    items = query_items(date=target_date, limit=5000)
    if not items:
        return []

    past_stats = query_daily_stats(days=7)
    historical_average = {}
    for topic in TOPICS:
        values = [row["final_score"] for row in past_stats if row["topic"] == topic and row["date"] < target_date]
        historical_average[topic] = sum(values) / len(values) if values else 0.0

    groups: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        groups[item.get("stable_topic", "Other")].append(item)

    results: list[DailyTopicStat] = []
    for topic in TOPICS:
        group = groups.get(topic, [])
        if not group:
            continue
        count = len(group)
        avg_importance = sum(item.get("importance_score", 0.0) for item in group) / count
        avg_novelty = sum(item.get("novelty_score", 0.0) for item in group) / count
        avg_momentum = sum(item.get("momentum_score", 0.0) for item in group) / count
        base_score = sum(item.get("final_score", 0.0) for item in group) / count
        topic_final_score = min(100.0, base_score + min(15.0, math.log10(count + 1) * 5))
        trend_delta = topic_final_score - historical_average.get(topic, 0.0)
        summary = summarize_stable_topic(topic, group, trend_delta)
        stat = DailyTopicStat(
            date=target_date,
            topic=topic,
            item_count=count,
            avg_importance=round(avg_importance, 3),
            avg_novelty=round(avg_novelty, 3),
            avg_momentum=round(avg_momentum, 3),
            final_score=round(topic_final_score, 1),
            trend_delta_7d=round(trend_delta, 1),
            top_summary=summary,
        )
        upsert_daily_stat(stat)
        results.append(stat)
    return results


def get_today_dashboard_data(target_date: str) -> dict:
    items = query_items(date=target_date, limit=5000)
    stable_stats = [row for row in query_daily_stats(days=7) if row["date"] == target_date]
    emerging_stats = [row for row in query_emerging_stats(days=7) if row["date"] == target_date]
    selection_stats = query_llm_selection_stat(target_date) or {}
    return {
        "items": items,
        "stable_stats": sorted(stable_stats, key=lambda row: row["final_score"], reverse=True),
        "emerging_stats": sorted(emerging_stats, key=lambda row: row["growth_rate"], reverse=True),
        "selection_stats": selection_stats,
    }


def build_trend_series(days: int = 30) -> dict:
    stable = query_daily_stats(days=days)
    emerging = query_emerging_stats(days=days)
    items = query_items(limit=10000)
    source_heatmap: dict[tuple[str, str], int] = defaultdict(int)
    for item in items:
        source_heatmap[(item.get("stable_topic", "Other"), item["source"])] += 1
    return {
        "stable": stable,
        "emerging": emerging,
        "source_heatmap": [
            {"stable_topic": stable_topic, "source": source, "count": count}
            for (stable_topic, source), count in source_heatmap.items()
        ],
    }
