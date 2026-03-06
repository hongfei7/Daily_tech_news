"""
github_fetcher.py - 根据关键词抓取 GitHub 近期活跃/热门项目
"""

import json
from datetime import datetime, timedelta, timezone
from urllib import request, error

from loguru import logger

from src.config import GITHUB_KEYWORDS, GITHUB_TOKEN, MAX_ITEMS_PER_SOURCE
from src.utils import clean_text, make_id


def fetch_github(days_back: int = 1) -> list[dict]:
    """
    调用 GitHub Search API，查询指定关键词在最近 N 天内创建或更新的热门仓库
    """
    logger.info(f"开始抓取 GitHub (过去 {days_back} 天)...")
    items = []
    
    since_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime('%Y-%m-%d')
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'TechTrendDashboard/1.0'
    }
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'

    # 每天每个关键词拉取少数几个最高 star 的
    per_page = max(5, MAX_ITEMS_PER_SOURCE // len(GITHUB_KEYWORDS))

    for keyword in GITHUB_KEYWORDS:
        # 查询语法：keyword pushed:>DATE 或者 created:>DATE
        # 这里用 pushed 寻找最近活跃的
        query = f'"{keyword}" pushed:>={since_date}'
        url = f"https://api.github.com/search/repositories?q={request.pathname2url(query)}&sort=stars&order=desc&per_page={per_page}"

        try:
            req = request.Request(url, headers=headers)
            with request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))

            for repo in data.get('items', []):
                desc = repo.get('description', '')
                # 如果没有描述，则使用名称作为描述
                raw_summary = clean_text(desc) if desc else clean_text(repo['full_name'])
                
                # 在 summary 中附加 star 数，便于评分模块读取
                stars = repo.get('stargazers_count', 0)
                raw_summary = f"[Stars: {stars}] {raw_summary}"
                
                # 取推送日期或创建日期作为事件日期
                date_str = repo.get('pushed_at', repo.get('created_at', ''))
                if date_str:
                    date_val = date_str[:10]
                else:
                    date_val = datetime.now(timezone.utc).strftime('%Y-%m-%d')

                url_str = repo.get('html_url', '')

                items.append({
                    "id": make_id(url_str),
                    "date": date_val,
                    "source": "github",
                    "title": repo.get('full_name', ''),
                    "url": url_str,
                    "raw_summary": raw_summary,
                })
        except error.HTTPError as e:
            if e.code == 403:
                logger.warning("GitHub API 达到速率限制，请配置 GITHUB_TOKEN。跳过剩余关键词。")
                break
            else:
                logger.error(f"抓取 GitHub 关键词 '{keyword}' 失败: {e}")
        except Exception as e:
            logger.error(f"抓取 GitHub 关键词 '{keyword}' 失败: {e}")

    logger.info(f"GitHub 抓取完成，共 {len(items)} 条活跃项目。")
    return items

if __name__ == "__main__":
    res = fetch_github()
    print(res[:2])
