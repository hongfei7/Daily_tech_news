"""
models.py - Pydantic 数据模型，定义 Item 和 DailyTopicStat 的数据结构
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Item(BaseModel):
    """单条科技信息条目"""
    id: str                                  # UUID 或内容哈希
    date: str                                # YYYY-MM-DD
    source: str                              # 来源标识（如 openai_blog）
    title: str
    url: str
    raw_summary: str = ""                    # 原始摘要文本
    one_line_summary: str = ""              # 一句话摘要（中文）
    topic: str = "Other"                     # 主 topic
    subtopic: str = ""                       # 子 topic（可选）
    keywords: list[str] = Field(default_factory=list)   # 关键词列表
    entities: list[str] = Field(default_factory=list)   # 实体列表
    importance_score: float = 0.0
    novelty_score: float = 0.0
    momentum_score: float = 0.0
    source_weight: float = 0.6
    final_score: float = 0.0
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    model_config = ConfigDict(populate_by_name=True)


class DailyTopicStat(BaseModel):
    """每天按 topic 聚合的统计数据"""
    date: str
    topic: str
    item_count: int = 0
    avg_importance: float = 0.0
    avg_novelty: float = 0.0
    avg_momentum: float = 0.0
    final_score: float = 0.0
    trend_delta_7d: float = 0.0             # 与 7 天前均值对比的变化量
    top_summary: str = ""                   # 今日该 topic 的代表性摘要
