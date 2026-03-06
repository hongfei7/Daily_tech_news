"""
pipeline.py - 全流程调度：抓取 -> 清洗 -> 归类摘要 -> 打分入库 -> 聚合
"""

from loguru import logger
from datetime import datetime

from src.config import FETCH_DAYS_BACK
from src.database import get_connection, bulk_upsert_items, query_items
from src.models import Item
from src.utils import deduplicate_items, today_str
from src.classifier import classify_item, get_keywords
from src.summarizer import generate_one_line_summary
from src.scoring import score_item

# 按需导入 Fetchers
from src.fetchers.arxiv_fetcher import fetch_arxiv
from src.fetchers.github_fetcher import fetch_github
from src.fetchers.blogs_fetcher import fetch_blogs
from src.fetchers.hn_fetcher import fetch_hacker_news
from src.fetchers.dblp_fetcher import fetch_dblp
from src.aggregator import aggregate_daily_stats

def run_pipeline(days_back: int = FETCH_DAYS_BACK):
    """
    执行完整的数据抓取和处理流程
    """
    logger.info("====================================")
    logger.info(f"🚀 开始执行科技趋势分析 Pipeline (回溯 {days_back} 天)")
    logger.info("====================================")
    
    # 1. 并发或顺序抓取数据
    raw_data = []
    
    try:
        raw_data.extend(fetch_arxiv(days_back))
    except Exception as e:
        logger.error(f"arXiv 抓取异常: {e}")
        
    try:
        raw_data.extend(fetch_github(days_back))
    except Exception as e:
        logger.error(f"GitHub 抓取异常: {e}")
        
    try:
        raw_data.extend(fetch_blogs(days_back))
    except Exception as e:
        logger.error(f"Blogs 抓取异常: {e}")
        
    try:
        raw_data.extend(fetch_hacker_news(days_back))
    except Exception as e:
        logger.error(f"HN 抓取异常: {e}")
        
    try:
        raw_data.extend(fetch_dblp(days_back))
    except Exception as e:
        logger.error(f"DBLP 抓取异常: {e}")

    logger.info(f"总计抓取到 {len(raw_data)} 条原始数据。")
    if not raw_data:
        logger.warning("未抓取到任何数据，Pipeline 终止。")
        return

    # 2. 去重（内存中先执行一轮文本去重）
    unique_data = deduplicate_items(raw_data, threshold=0.85)
    logger.info(f"文本去重后剩余 {len(unique_data)} 条数据。")

    # 3. 准备打分上下文 (例如最近7天的热度、已有标题等)
    with get_connection() as conn:
        # 获取现有的所有标题用于计算 novelty
        rows = conn.execute("SELECT title FROM items ORDER BY date DESC LIMIT 2000").fetchall()
        existing_titles = [r["title"] for r in rows]
        
        # 获取最近7天的 topic 频次用于 momentum
        rows = conn.execute("""
            SELECT topic, COUNT(*) as cnt 
            FROM items 
            WHERE date >= date('now', '-7 days')
            GROUP BY topic
        """).fetchall()
        topic_counts = {r["topic"]: r["cnt"] for r in rows}

    import concurrent.futures

    processed_items = []
    total_len = len(unique_data)
    
    def process_item(i, data, existing_titles, topic_counts):
        title = data["title"]
        summary = data["raw_summary"]
        
        # 归类
        topic = classify_item(title, summary)
        keywords = get_keywords(title, summary)
        
        # 摘要
        one_line = generate_one_line_summary(title, summary)
        
        # 组装为 Pydantic Model
        item = Item(
            id=data["id"],
            date=data["date"],
            source=data["source"],
            title=title,
            url=data["url"],
            raw_summary=summary,
            one_line_summary=one_line,
            topic=topic,
            keywords=keywords,
            # 其余分数先用默认值，下面计算
        )
        
        # 打分
        score_item(item, existing_titles, topic_counts)
        
        if (i + 1) % 10 == 0 or (i + 1) == total_len:
            logger.info(f"进度: 已处理 {i+1}/{total_len}...")
            
        return item

    # 4. 逐条处理：分类、摘要、打分 (多线程并发加速)
    logger.info("开始调用 LLM 处理摘要和分类，请耐心等待...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(process_item, i, data, existing_titles, topic_counts)
            for i, data in enumerate(unique_data)
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                processed_items.append(future.result())
            except Exception as e:
                logger.error(f"处理条目异常: {e}")
        
    # 5. 入库
    logger.info("正在将处理后的数据写入数据库...")
    inserted_count = bulk_upsert_items(processed_items)
    logger.info(f"成功新写入 {inserted_count} 条数据 (其余为已存在跳过)。")

    # 6. 按天聚合（聚合今天以及涉及到的历史日期）
    affected_dates = set(item.date for item in processed_items)
    for d in affected_dates:
        aggregate_daily_stats(d)
        
    logger.info("====================================")
    logger.info("✨ Pipeline 执行完毕")
    logger.info("====================================")

if __name__ == "__main__":
    from src.utils import setup_logger
    setup_logger()
    run_pipeline(days_back=1)
