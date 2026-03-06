"""Scoring utilities for ranking items."""

from __future__ import annotations

import math
import re

from src.config import SCORE_WEIGHTS, SOURCE_WEIGHTS
from src.models import Item
from src.utils import title_similarity


def calculate_importance(item: Item) -> float:
    score = 0.45
    text = f"{item.title} {item.raw_summary}".lower()
    strong_keywords = [
        "release",
        "benchmark",
        "launch",
        "model",
        "open source",
        "open weights",
        "breakthrough",
        "agent",
        "reasoning",
    ]
    for keyword in strong_keywords:
        if keyword in text:
            score += 0.08

    star_match = re.search(r"\[Stars:\s*(\d+)\]", item.raw_summary)
    if star_match:
        stars = int(star_match.group(1))
        score += min(0.35, math.log10(max(1, stars)) / 8)

    hn_match = re.search(r"\[HN Points:\s*(\d+)\]", item.raw_summary)
    if hn_match:
        points = int(hn_match.group(1))
        score += min(0.3, math.log10(max(1, points)) / 7)

    return min(1.0, score)


def calculate_novelty(item: Item, existing_titles: list[str]) -> float:
    max_similarity = 0.0
    for title in existing_titles:
        max_similarity = max(max_similarity, title_similarity(item.title, title))
    novelty = 1.0 - max_similarity
    if item.source == "arxiv":
        novelty = max(novelty, 0.65)
    return min(1.0, max(0.0, novelty))


def calculate_momentum(stable_topic: str, topic_counts_last_7d: dict[str, int]) -> float:
    count = topic_counts_last_7d.get(stable_topic, 0)
    if count <= 0:
        return 0.2
    return max(0.1, min(1.0, math.log10(count + 1) / math.log10(18)))


def score_item(item: Item, existing_titles: list[str], topic_counts_last_7d: dict[str, int]) -> Item:
    item.sync_legacy_fields()
    item.source_weight = SOURCE_WEIGHTS.get(item.source, SOURCE_WEIGHTS["default"])
    item.importance_score = calculate_importance(item)
    item.novelty_score = calculate_novelty(item, existing_titles)
    item.momentum_score = calculate_momentum(item.stable_topic, topic_counts_last_7d)

    final = (
        SCORE_WEIGHTS["importance"] * item.importance_score
        + SCORE_WEIGHTS["novelty"] * item.novelty_score
        + SCORE_WEIGHTS["momentum"] * item.momentum_score
    ) * item.source_weight
    item.final_score = round(min(100.0, final * 100), 1)
    return item
