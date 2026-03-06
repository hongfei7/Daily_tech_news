"""
aggregator.py - 按天计算 Topic 粒度的统计数据
"""

from loguru import logger

from src.database import query_items, upsert_daily_stat, query_daily_stats
from src.models import DailyTopicStat
from src.config import TOPICS

def aggregate_daily_stats(target_date: str):
    """
    聚合指定日期的 items 数据，计算每个 topic 的均分，并对比过去 7 天产生趋势。
    将结果写入 daily_topic_stats 表。
    """
    logger.info(f"开始聚合 {target_date} 的数据...")
    
    # 1. 获取当天的所有 items
    items = query_items(date=target_date, limit=1000)
    if not items:
        logger.warning(f"日期 {target_date} 没有抓取到数据，跳过聚合。")
        return
        
    # 分组
    topic_groups = {t: [] for t in TOPICS}
    for item in items:
        t = item["topic"]
        if t in topic_groups:
            topic_groups[t].append(item)
        else:
            topic_groups["Other"].append(item)
            
    # 2. 获取过去 7 天的统计数据用于计算 trend_delta_7d
    past_stats = query_daily_stats(days=7)
    past_topic_avg = {}
    
    for t in TOPICS:
        t_stats = [s for s in past_stats if s["topic"] == t and s["date"] < target_date]
        if t_stats:
            avg_past_score = sum(s["final_score"] for s in t_stats) / len(t_stats)
            past_topic_avg[t] = avg_past_score
        else:
            past_topic_avg[t] = 0.0

    # 3. 计算并保存
    for topic, group in topic_groups.items():
        if not group:
            continue
            
        count = len(group)
        avg_imp = sum(i["importance_score"] for i in group) / count
        avg_nov = sum(i["novelty_score"] for i in group) / count
        avg_mom = sum(i["momentum_score"] for i in group) / count
        
        # Topic 的 final_score 可以是 top 3 item 的平均，或者全体平均
        # 这里为了突出价值，取全体平均 + 数量对数加成
        import math
        base_score = sum(i["final_score"] for i in group) / count
        vol_bonus = min(15.0, math.log10(count + 1) * 5) 
        topic_final_score = min(100.0, base_score + vol_bonus)
        
        trend_delta = topic_final_score - past_topic_avg[t]
        
        # 挑选最高分的摘要作为代表
        top_item = max(group, key=lambda x: x["final_score"])
        top_summary = top_item["one_line_summary"] or top_item["title"]
        
        stat = DailyTopicStat(
            date=target_date,
            topic=topic,
            item_count=count,
            avg_importance=round(avg_imp, 3),
            avg_novelty=round(avg_nov, 3),
            avg_momentum=round(avg_mom, 3),
            final_score=round(topic_final_score, 1),
            trend_delta_7d=round(trend_delta, 1),
            top_summary=top_summary
        )
        
        upsert_daily_stat(stat)
        
    logger.info(f"聚合完成: {target_date}")
