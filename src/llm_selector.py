"""Representative LLM sampling with multi-bucket quotas."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import ceil

from src.config import LLM_SELECTION, TOPICS, TITLE_SIMILARITY_THRESHOLD
from src.utils import title_similarity


@dataclass
class SelectionResult:
    selected_items: list[dict]
    bucket_map: dict[str, tuple[str, str]]
    stats: dict[str, int | float | str]


def _dedupe_candidates(items: list[dict], seen_titles: list[str], seen_ids: set[str]) -> list[dict]:
    deduped: list[dict] = []
    for item in items:
        if item["id"] in seen_ids:
            continue
        if any(title_similarity(item["title"], title) >= TITLE_SIMILARITY_THRESHOLD for title in seen_titles):
            continue
        deduped.append(item)
    return deduped


def _within_share_limits(
    item: dict,
    selected: list[dict],
    max_items: int,
    max_topic_share: float,
) -> bool:
    if not selected:
        return True
    stable_counts = Counter(chosen.get("stable_topic", "Other") for chosen in selected)
    source_counts = Counter(chosen["source"] for chosen in selected)
    emerging_counts = Counter(chosen.get("emerging_topic", "") for chosen in selected if chosen.get("emerging_topic"))
    stable_cap = max(1, ceil(max_items * max_topic_share))
    source_cap = max(2, ceil(max_items * 0.3))
    emerging_cap = max(1, ceil(max_items * 0.25))
    if stable_counts[item.get("stable_topic", "Other")] >= stable_cap:
        return False
    if source_counts[item["source"]] >= source_cap:
        return False
    emerging_topic = item.get("emerging_topic") or ""
    if emerging_topic and emerging_counts[emerging_topic] >= emerging_cap:
        return False
    return True


def _pick_from_pool(
    pool: list[dict],
    selected: list[dict],
    bucket_map: dict[str, tuple[str, str]],
    max_items: int,
    desired_count: int,
    bucket: str,
    reason: str,
) -> None:
    seen_titles = [item["title"] for item in selected]
    seen_ids = {item["id"] for item in selected}
    for item in _dedupe_candidates(pool, seen_titles, seen_ids):
        if len(selected) >= max_items or desired_count <= 0:
            return
        if not _within_share_limits(item, selected, max_items, LLM_SELECTION["max_topic_share"]):
            continue
        selected.append(item)
        bucket_map[item["id"]] = (bucket, reason)
        seen_titles.append(item["title"])
        seen_ids.add(item["id"])
        desired_count -= 1


def _allocate_budget(total_budget: int, total_items: int, unique_stable_topics: int, unique_emerging_topics: int) -> int:
    budget = total_budget
    if LLM_SELECTION["auto_expand_budget"]:
        if total_items >= total_budget * 3:
            budget += 10
        if unique_stable_topics >= 8:
            budget += 5
        if unique_emerging_topics >= 5:
            budget += 5
    return min(budget, LLM_SELECTION["hard_cap"])


def select_representative_items(items: list[dict], target_date: str, settings: dict | None = None) -> SelectionResult:
    del target_date
    cfg = settings or LLM_SELECTION
    eligible = [item for item in items if item.get("final_score", 0.0) >= cfg["score_threshold"]]
    if not eligible:
        eligible = sorted(items, key=lambda item: item.get("final_score", 0.0), reverse=True)[: cfg["max_items_per_run"]]

    stable_topics = {item.get("stable_topic", "Other") for item in items if item.get("stable_topic")}
    emerging_topics = {item.get("emerging_topic") for item in items if item.get("emerging_topic")}
    max_items = _allocate_budget(cfg["max_items_per_run"], len(items), len(stable_topics), len(emerging_topics))

    top_budget = max(1, round(max_items * cfg["top_pool_ratio"]))
    stable_budget = max(1, round(max_items * cfg["stable_pool_ratio"]))
    emerging_budget = max(1, max_items - top_budget - stable_budget)

    ranked = sorted(eligible, key=lambda item: item.get("final_score", 0.0), reverse=True)
    selected: list[dict] = []
    bucket_map: dict[str, tuple[str, str]] = {}

    _pick_from_pool(ranked, selected, bucket_map, max_items, top_budget, "top_pool", "top_score")

    stable_groups: dict[str, list[dict]] = defaultdict(list)
    for item in ranked:
        stable_groups[item.get("stable_topic", "Other")].append(item)

    per_topic_sorted = sorted(
        stable_groups.items(),
        key=lambda pair: sum(item.get("final_score", 0.0) for item in pair[1]) / max(1, len(pair[1])),
        reverse=True,
    )
    stable_candidates: list[dict] = []
    for topic, group in per_topic_sorted:
        if topic == "Other":
            continue
        stable_candidates.extend(group[: max(1, cfg["min_items_per_stable_topic"])])
    emerging_groups: dict[str, list[dict]] = defaultdict(list)
    for item in ranked:
        if item.get("emerging_topic"):
            emerging_groups[item["emerging_topic"]].append(item)
    emerging_ranked: list[dict] = []
    for _, group in sorted(
        emerging_groups.items(),
        key=lambda pair: (
            len(pair[1]),
            sum(item.get("final_score", 0.0) for item in pair[1]) / max(1, len(pair[1])),
        ),
        reverse=True,
    ):
        emerging_ranked.extend(group[:2])
    _pick_from_pool(emerging_ranked, selected, bucket_map, max_items, emerging_budget, "emerging_pool", "emerging_reserved")
    if len(selected) < top_budget + stable_budget + emerging_budget and emerging_ranked:
        _pick_from_pool(
            emerging_ranked,
            selected,
            bucket_map,
            max_items,
            top_budget + stable_budget + emerging_budget - len(selected),
            "emerging_pool",
            "emerging_fill",
        )

    _pick_from_pool(stable_candidates, selected, bucket_map, max_items, stable_budget, "stable_pool", "stable_coverage")
    if len(selected) < top_budget + stable_budget + emerging_budget:
        flattened = [item for _, group in per_topic_sorted for item in group]
        _pick_from_pool(
            flattened,
            selected,
            bucket_map,
            max_items,
            top_budget + stable_budget + emerging_budget - len(selected),
            "stable_pool",
            "stable_heat",
        )

    if len(selected) < max_items:
        _pick_from_pool(ranked, selected, bucket_map, max_items, max_items - len(selected), "top_pool", "budget_fill")

    selected = selected[:max_items]
    bucket_counts = Counter(bucket for bucket, _ in bucket_map.values())
    stats = {
        "total_items": len(items),
        "max_items": max_items,
        "llm_items_selected": len(selected),
        "top_bucket_count": bucket_counts.get("top_pool", 0),
        "stable_bucket_count": bucket_counts.get("stable_pool", 0),
        "emerging_bucket_count": bucket_counts.get("emerging_pool", 0),
        "stable_topic_count": len({item.get("stable_topic", "Other") for item in selected}),
        "emerging_topic_count": len({item.get("emerging_topic") for item in selected if item.get("emerging_topic")}),
        "coverage_ratio": round(len(selected) / max(1, len(items)), 3),
    }
    return SelectionResult(selected_items=selected, bucket_map=bucket_map, stats=stats)
