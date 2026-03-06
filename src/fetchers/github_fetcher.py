"""Fetch active GitHub repositories relevant to current AI topics."""

from __future__ import annotations

import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from urllib import error, request

from loguru import logger

from src.config import GITHUB_KEYWORDS, GITHUB_TOKEN, MAX_ITEMS_PER_SOURCE
from src.utils import clean_text, make_id


def fetch_github(days_back: int = 1) -> list[dict]:
    logger.info(f"开始抓取 GitHub (过去 {days_back} 天)...")
    items: list[dict] = []

    since_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "TechTrendDashboard/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    per_page = max(5, MAX_ITEMS_PER_SOURCE // max(1, len(GITHUB_KEYWORDS)))

    for keyword in GITHUB_KEYWORDS:
        query = f'"{keyword}" pushed:>={since_date}'
        params = urllib.parse.urlencode(
            {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": per_page,
            }
        )
        url = f"https://api.github.com/search/repositories?{params}"

        try:
            req = request.Request(url, headers=headers)
            with request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))

            for repo in data.get("items", []):
                desc = repo.get("description", "")
                raw_summary = clean_text(desc) if desc else clean_text(repo.get("full_name", ""))
                stars = repo.get("stargazers_count", 0)
                raw_summary = f"[Stars: {stars}] {raw_summary}"

                date_str = repo.get("pushed_at", repo.get("created_at", ""))
                date_val = date_str[:10] if date_str else datetime.now(timezone.utc).strftime("%Y-%m-%d")
                url_str = repo.get("html_url", "")

                items.append(
                    {
                        "id": make_id(url_str),
                        "date": date_val,
                        "source": "github",
                        "title": repo.get("full_name", ""),
                        "url": url_str,
                        "raw_summary": raw_summary,
                    }
                )
        except error.HTTPError as exc:
            if exc.code == 403:
                logger.warning("GitHub API 速率受限，跳过剩余 GitHub 查询。建议配置 GITHUB_TOKEN。")
                break
            logger.warning("GitHub query 失败，keyword='{}'，status={}", keyword, exc.code)
        except Exception as exc:
            logger.warning("GitHub query 异常，keyword='{}'，error={}", keyword, exc)

    deduped = {item["id"]: item for item in items}
    final_items = list(deduped.values())
    logger.info(f"GitHub 抓取完成，共 {len(final_items)} 条活跃项目。")
    return final_items


if __name__ == "__main__":
    print(fetch_github()[:2])
