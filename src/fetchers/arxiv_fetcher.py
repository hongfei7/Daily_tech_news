"""
arxiv_fetcher.py - 从 arXiv API 抓取最新论文
"""

import xml.etree.ElementTree as ET
from urllib import request

from loguru import logger

from src.config import ARXIV_CATEGORIES, MAX_ITEMS_PER_SOURCE
from src.utils import clean_text, make_id, parse_date


def fetch_arxiv(days_back: int = 1) -> list[dict]:
    """
    通过 arXiv API 获取指定类别最新论文。
    """
    logger.info(f"开始抓取 arXiv (过去 {days_back} 天)...")
    items = []
    
    # 构造查询串：cs.AI OR cs.LG ...
    query = " OR ".join([f"cat:{c}" for c in ARXIV_CATEGORIES])
    # sortBy=lastUpdatedDate&sortOrder=desc 获取最新
    # 这里为了简单，不做精确的天数过滤，直接取 max_results，后续依靠 date 在外部或这里过滤
    url = f"http://export.arxiv.org/api/query?search_query={query}&sortBy=lastUpdatedDate&sortOrder=desc&max_results={MAX_ITEMS_PER_SOURCE}"

    try:
        req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0 TechTrend/1.0'})
        with request.urlopen(req, timeout=15) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        # arXiv 原子的命名空间
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text
            title = clean_text(title)
            
            summary = entry.find('atom:summary', ns).text
            summary = clean_text(summary)
            
            link = entry.find("atom:link[@rel='alternate']", ns)
            url_str = link.attrib.get('href', '') if link is not None else entry.find('atom:id', ns).text
            
            published = entry.find('atom:published', ns).text
            date_str = parse_date(published)
            
            # TODO: 可以在这里添加精确的 days_back 过滤，目前交给 Pipeline 处理较为统一
            
            items.append({
                "id": make_id(url_str),
                "date": date_str,
                "source": "arxiv",
                "title": title,
                "url": url_str,
                "raw_summary": summary,
            })

    except Exception as e:
        logger.error(f"抓取 arXiv 失败: {e}")

    logger.info(f"arXiv 抓取完成，共 {len(items)} 条数据。")
    return items

if __name__ == "__main__":
    res = fetch_arxiv()
    print(res[:2])
