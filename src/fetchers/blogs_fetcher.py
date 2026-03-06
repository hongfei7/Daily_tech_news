"""
blogs_fetcher.py - 使用 feedparser 抓取官方博客 RSS
"""

import feedparser
from loguru import logger

from src.config import BLOG_FEEDS, MAX_ITEMS_PER_SOURCE
from src.utils import clean_text, make_id, parse_date


def fetch_blogs(days_back: int = 1) -> list[dict]:
    """
    抓取各大科技公司的官方博客
    """
    logger.info("开始抓取 官方博客 Rss Feed...")
    items = []

    for feed_info in BLOG_FEEDS:
        source_name = feed_info["name"]
        url = feed_info["url"]
        logger.debug(f"正在获取 {source_name}: {url}")

        try:
            parsed = feedparser.parse(url)
            entries = parsed.entries[:MAX_ITEMS_PER_SOURCE]

            for entry in entries:
                title = clean_text(entry.get("title", ""))
                link = entry.get("link", "")
                
                # 尝试获取摘要或全文的前半部分
                summary = entry.get("summary", "")
                if not summary and "content" in entry:
                    summary = entry.content[0].value
                raw_summary = clean_text(summary)
                
                # 获取日期
                # feedparser 尝试解析多种日期格式，存入 published_parsed 
                # 或 date_parsed, 如果没有我们尝试拿原始字符串解析
                if "published_parsed" in entry and entry.published_parsed:
                    import time
                    from datetime import datetime
                    t = time.mktime(entry.published_parsed)
                    date_str = datetime.fromtimestamp(t).strftime('%Y-%m-%d')
                elif "published" in entry:
                    date_str = parse_date(entry.published)
                elif "updated" in entry:
                    date_str = parse_date(entry.updated)
                else:
                    date_str = parse_date(None)

                items.append({
                    "id": make_id(link),
                    "date": date_str,
                    "source": source_name,
                    "title": title,
                    "url": link,
                    "raw_summary": raw_summary,
                })
        except Exception as e:
            logger.error(f"解析 {source_name} 失败: {e}")

    logger.info(f"官方博客 抓取完成，共 {len(items)} 条数据。")
    return items

if __name__ == "__main__":
    res = fetch_blogs()
    print(res[:2])
