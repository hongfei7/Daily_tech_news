"""
hn_fetcher.py - 抓取 Hacker News 首页并过滤高票/相关条目
"""

import json
from urllib import request
from datetime import datetime

from loguru import logger

from src.config import HN_MAX_ITEMS, HN_MIN_POINTS
from src.utils import make_id, clean_text


def fetch_hacker_news(days_back: int = 1) -> list[dict]:
    """
    调用 Algolia HN API (Hacker News Search) 以获取过去 N 天的高票文章。
    """
    logger.info(f"开始抓取 Hacker News (过去 {days_back} 天)...")
    items = []

    # HN Algolia API 更易于按时间戳和 points 搜索
    import time
    ts_now = int(time.time())
    ts_since = ts_now - (days_back * 86400)
    
    # 我们只抓取 points > HN_MIN_POINTS，且时间在最近 N 天的记录
    url = f"http://hn.algolia.com/api/v1/search?numericFilters=created_at_i>{ts_since},points>{HN_MIN_POINTS}&hitsPerPage={HN_MAX_ITEMS}"

    try:
        req = request.Request(url, headers={'User-Agent': 'TechTrendDashboard/1.0'})
        with request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        for hit in data.get('hits', []):
            url_str = hit.get('url') or hit.get('story_url')
            # 如果没有链接，有可能是个讨论串，跳过或者指向 HN 本站
            if not url_str:
                url_str = f"https://news.ycombinator.com/item?id={hit.get('objectID')}"

            title = hit.get('title') or hit.get('story_title', '')
            title = clean_text(title)
            if not title:
                continue

            points = hit.get('points', 0)
            raw_summary = f"[HN Points: {points}] " + (hit.get('story_text', '') or '')
            raw_summary = clean_text(raw_summary)

            created_at = hit.get('created_at', '')
            if created_at:
                date_str = created_at[:10]  # format is 2024-05-19T...
            else:
                date_str = datetime.utcnow().strftime('%Y-%m-%d')

            items.append({
                "id": make_id(url_str),
                "date": date_str,
                "source": "hacker_news",
                "title": title,
                "url": url_str,
                "raw_summary": raw_summary,
            })

    except Exception as e:
        logger.error(f"抓取 Hacker News 失败: {e}")

    logger.info(f"Hacker News 抓取完成，共 {len(items)} 条符合阈值的数据。")
    return items

if __name__ == "__main__":
    res = fetch_hacker_news()
    print(res[:2])
