"""Discover fast-rising emerging topics from recent items."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.config import EMERGING_DISCOVERY
from src.models import EmergingTopicStat


@dataclass
class EmergingCandidate:
    topic: str
    recent_count: int
    baseline_count: int
    growth_rate: float
    source_count: int
    avg_score: float
    emerging_score: float
    item_ids: list[str]
    top_summary: str


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def _normalize_tag(tag: str) -> str:
    tag = " ".join(tag.split()).strip()
    return tag[:80]


def discover_emerging_topics(
    items: list[dict],
    target_date: str,
    settings: dict | None = None,
) -> list[EmergingCandidate]:
    cfg = settings or EMERGING_DISCOVERY
    if not items:
        return []

    target_dt = _parse_date(target_date)
    lookback_days = cfg["lookback_days"]
    recent_days = cfg["recent_days"]
    recent_cutoff = target_dt - timedelta(days=recent_days - 1)
    baseline_cutoff = target_dt - timedelta(days=lookback_days - 1)

    grouped: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "recent_count": 0,
            "baseline_count": 0,
            "sources": set(),
            "scores": [],
            "items": [],
        }
    )

    for item in items:
        item_date = _parse_date(item["date"])
        if item_date < baseline_cutoff or item_date > target_dt:
            continue
        tags = item.get("tags") or item.get("keywords") or []
        if item.get("stable_topic") == "Other":
            tags = list(dict.fromkeys(tags + [item.get("title", "")]))
        for raw_tag in tags:
            tag = _normalize_tag(str(raw_tag))
            if len(tag) < 3:
                continue
            bucket = grouped[tag]
            if item_date >= recent_cutoff:
                bucket["recent_count"] += 1
            else:
                bucket["baseline_count"] += 1
            bucket["sources"].add(item["source"])
            bucket["scores"].append(float(item.get("final_score", 0.0)))
            bucket["items"].append(item)

    candidates: list[EmergingCandidate] = []
    for topic, bucket in grouped.items():
        recent_count = int(bucket["recent_count"])
        baseline_count = int(bucket["baseline_count"])
        source_count = len(bucket["sources"])
        avg_score = sum(bucket["scores"]) / len(bucket["scores"]) if bucket["scores"] else 0.0
        if recent_count < cfg["min_keyword_freq"] or source_count < cfg["min_source_count"]:
            continue
        growth_rate = recent_count / max(1, baseline_count)
        if growth_rate < cfg["min_growth_ratio"]:
            continue

        source_diversity = min(1.0, source_count / 5.0)
        normalized_score = min(1.0, avg_score / 100.0)
        emerging_score = 0.5 * growth_rate + 0.3 * source_diversity + 0.2 * normalized_score
        items_sorted = sorted(bucket["items"], key=lambda item: item.get("final_score", 0.0), reverse=True)
        candidates.append(
            EmergingCandidate(
                topic=topic,
                recent_count=recent_count,
                baseline_count=baseline_count,
                growth_rate=round(growth_rate, 2),
                source_count=source_count,
                avg_score=round(avg_score, 1),
                emerging_score=round(emerging_score, 3),
                item_ids=[item["id"] for item in items_sorted[: recent_count + baseline_count]],
                top_summary=(items_sorted[0].get("one_line_summary") or items_sorted[0]["title"]) if items_sorted else "",
            )
        )

    candidates.sort(key=lambda candidate: (candidate.emerging_score, candidate.avg_score), reverse=True)
    return candidates[: cfg["top_n_emerging"]]


def build_emerging_stats(target_date: str, candidates: list[EmergingCandidate]) -> list[EmergingTopicStat]:
    return [
        EmergingTopicStat(
            date=target_date,
            emerging_topic=candidate.topic,
            item_count=candidate.recent_count,
            growth_rate=candidate.growth_rate,
            source_count=candidate.source_count,
            avg_score=candidate.avg_score,
            top_summary=candidate.top_summary,
        )
        for candidate in candidates
    ]
