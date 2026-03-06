"""
dblp_fetcher.py - 从 DBLP 抓取最新论文
"""

import json
from urllib import request
import urllib.parse
from datetime import datetime, timedelta

from loguru import logger

from src.config import MAX_ITEMS_PER_SOURCE, DBLP_SEARCH_QUERIES
from src.utils import clean_text, make_id

def fetch_dblp(days_back: int = 1) -> list[dict]:
    """
    通过 DBLP API 获取最新相关论文
    DBLP 没有按时间的精细过滤 API，所以我们通过查询近期发表物并过滤
    """
    logger.info(f"开始抓取 DBLP (过去 {days_back} 天)...")
    items = []
    
    cutoff_date = datetime.now() - timedelta(days=days_back)
    cutoff_year = cutoff_date.year
    
    for query in DBLP_SEARCH_QUERIES:
        try:
            # 加上年份限制来缩小范围: e.g. "large language models year:2024"
            search_term = f"{query} year:{cutoff_year}"
            encoded_query = urllib.parse.quote_plus(search_term)
            
            url = f"https://dblp.org/search/publ/api?q={encoded_query}&format=json&h={MAX_ITEMS_PER_SOURCE}"
            req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0 TechTrend/1.0'})
            
            import ssl
            context = ssl._create_unverified_context()
            
            with request.urlopen(req, timeout=15, context=context) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            
            for hit in hits:
                info = hit.get("info", {})
                
                title = info.get("title", "")
                title = clean_text(title)
                if not title:
                    continue
                    
                url_str = info.get("ee", info.get("url", ""))
                
                # DBLP通常只有年份没有具体日期，我们取当前日期作为发现日期
                # 如果能在 info 里面找到类似 date 的，尽量解析
                date_str = datetime.now().strftime("%Y-%m-%d")
                
                # DBLP通常没有详细 summary，用 Venue/Authors 拼凑一个简短的 raw_summary
                venue = info.get("venue", "Unknown Venue")
                authors = info.get("authors", {}).get("author", [])
                if isinstance(authors, dict):
                     authors = [authors]
                elif isinstance(authors, str):
                     authors = [{"text": authors}]
                     
                author_names = ", ".join([a.get("text", "") for a in authors if isinstance(a, dict)])
                summary = f"Published at {venue}. Authors: {author_names}"
                
                items.append({
                    "id": make_id(url_str or title),
                    "date": date_str,
                    "source": "dblp",
                    "title": title,
                    "url": url_str,
                    "raw_summary": summary,
                })
                
        except Exception as e:
            logger.error(f"抓取 DBLP 失败 (query={query}): {e}")
            
    logger.info(f"DBLP 抓取完成，共 {len(items)} 条数据。")
    return items

if __name__ == "__main__":
    from src.utils import setup_logger
    setup_logger()
    res = fetch_dblp()
    print(res[:2])
