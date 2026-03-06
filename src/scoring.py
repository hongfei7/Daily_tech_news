"""
scoring.py - 信息价值打分模块
"""

import math
from src.config import SCORE_WEIGHTS, SOURCE_WEIGHTS
from src.models import Item

def calculate_importance(item: Item) -> float:
    """
    衡量信息本身价值
    """
    score = 0.5  # 基础分
    
    # 标题关键词加分
    text = item.title.lower()
    strong_keywords = ["release", "benchmark", "launch", "model", "open source", "sota", "breakthrough"]
    for kw in strong_keywords:
        if kw in text:
            score += 0.2
            
    # 从原始摘要提取 star/point 数据加分
    import re
    # 匹配 [Stars: 1234] 或 [HN Points: 456]
    star_match = re.search(r'\[Stars:\s*(\d+)\]', item.raw_summary)
    if star_match:
        stars = int(star_match.group(1))
        # 简单对数加分，stars > 100 才有明显加成，最高 + 0.4
        if stars > 0:
            bonus = min(0.4, (math.log10(stars) / 10.0))
            score += bonus
            
    hn_match = re.search(r'\[HN Points:\s*(\d+)\]', item.raw_summary)
    if hn_match:
        points = int(hn_match.group(1))
        if points > 0:
            bonus = min(0.4, (math.log10(points) / 8.0))
            score += bonus
            
    return min(1.0, score)

def calculate_novelty(item: Item, existing_titles: list[str]) -> float:
    """
    衡量是否是新东西（MVP: 标题如果曾在库里出现近似的，说明是老新闻了）
    """
    from src.utils import title_similarity
    
    max_sim = 0.0
    for t in existing_titles:
        sim = title_similarity(item.title, t)
        if sim > max_sim:
            max_sim = sim
            
    # 越相似，novelty 越低
    novelty = 1.0 - max_sim
    # 对于 arXiv 文章，自带一定的 novelty
    if item.source == "arxiv":
        novelty = max(novelty, 0.6)
        
    return min(1.0, max(0.0, novelty))

def calculate_momentum(topic: str, topic_counts_last_7d: dict) -> float:
    """
    衡量方向温度：最近该话题出现的频率
    topic_counts_last_7d: { "topic_a": 15, "topic_b": 2 ... }
    """
    count = topic_counts_last_7d.get(topic, 0)
    # 取对数做平滑, count=10 -> 1.0
    if count == 0:
        return 0.2
    
    score = min(1.0, math.log10(count + 1) / math.log10(15))
    return max(0.1, score)

def score_item(item: Item, existing_titles: list[str], topic_counts_last_7d: dict) -> Item:
    """
    计算综合评分并原地更新 item
    """
    # 1. 设置来源权重
    item.source_weight = SOURCE_WEIGHTS.get(item.source, SOURCE_WEIGHTS["default"])
    
    # 2. importance
    item.importance_score = calculate_importance(item)
    
    # 3. novelty
    item.novelty_score = calculate_novelty(item, existing_titles)
    
    # 4. momentum
    item.momentum_score = calculate_momentum(item.topic, topic_counts_last_7d)
    
    # 5. final
    w = SCORE_WEIGHTS
    final = (
        w["importance"] * item.importance_score +
        w["novelty"] * item.novelty_score +
        w["momentum"] * item.momentum_score
    ) * item.source_weight
    
    # 放大分数到 0-100 便于展示
    item.final_score = round(min(100.0, final * 100), 1)
    
    return item
