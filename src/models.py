"""Typed data models used across the pipeline."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class Item(BaseModel):
    id: str
    date: str
    source: str
    title: str
    url: str
    raw_summary: str = ""
    one_line_summary: str = ""
    stable_topic: str = "Other"
    emerging_topic: str = ""
    tags: list[str] = Field(default_factory=list)
    llm_selected: int = 0
    selection_bucket: str = ""
    selection_reason: str = ""
    topic: str = "Other"
    subtopic: str = ""
    keywords: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    importance_score: float = 0.0
    novelty_score: float = 0.0
    momentum_score: float = 0.0
    source_weight: float = 0.6
    final_score: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(populate_by_name=True)

    def sync_legacy_fields(self) -> "Item":
        if (not self.stable_topic or self.stable_topic == "Other") and self.topic:
            self.stable_topic = self.topic
        self.topic = self.stable_topic
        self.keywords = list(self.tags)
        return self


class DailyTopicStat(BaseModel):
    date: str
    topic: str
    item_count: int = 0
    avg_importance: float = 0.0
    avg_novelty: float = 0.0
    avg_momentum: float = 0.0
    final_score: float = 0.0
    trend_delta_7d: float = 0.0
    top_summary: str = ""


class EmergingTopicStat(BaseModel):
    date: str
    emerging_topic: str
    item_count: int = 0
    growth_rate: float = 0.0
    source_count: int = 0
    avg_score: float = 0.0
    top_summary: str = ""


class LLMSelectionStat(BaseModel):
    date: str
    total_items: int = 0
    stable_topic_count: int = 0
    emerging_topic_count: int = 0
    llm_items_selected: int = 0
    top_bucket_count: int = 0
    stable_bucket_count: int = 0
    emerging_bucket_count: int = 0
    coverage_ratio: float = 0.0
    notes: str = ""
