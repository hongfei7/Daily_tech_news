"""Fetch recent research-oriented items from DBLP with graceful degradation."""

from __future__ import annotations

import json
import ssl
import time
import urllib.parse
from datetime import datetime, timedelta
from urllib import error, request

from loguru import logger

from src.config import DBLP_SEARCH_QUERIES, MAX_ITEMS_PER_SOURCE
from src.utils import clean_text, make_id


DBLP_API = "https://dblp.org/search/publ/api"
SSL_CONTEXT = ssl._create_unverified_context()


def _build_url(query: str, limit: int) -> str:
    params = {
        "q": query,
        "format": "json",
        "h": limit,
    }
    return f"{DBLP_API}?{urllib.parse.urlencode(params)}"


def _request_json(url: str, retries: int = 2, timeout: int = 20) -> dict:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = request.Request(url, headers={"User-Agent": "TechTrendDashboard/1.0"})
            with request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            last_error = exc
            if 500 <= exc.code < 600 and attempt < retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            raise
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            raise
    if last_error:
        raise last_error
    return {}


def _extract_items(hits: list[dict], cutoff_year: int) -> list[dict]:
    items: list[dict] = []
    today = datetime.now().strftime("%Y-%m-%d")
    for hit in hits:
        info = hit.get("info", {})
        title = clean_text(info.get("title", ""))
        if not title:
            continue

        year_raw = info.get("year")
        try:
            year_value = int(year_raw) if year_raw else cutoff_year
        except ValueError:
            year_value = cutoff_year
        if year_value < cutoff_year:
            continue

        url_str = info.get("ee", info.get("url", "")) or ""
        venue = info.get("venue", "Unknown Venue")
        authors = info.get("authors", {}).get("author", [])
        if isinstance(authors, dict):
            authors = [authors]
        elif isinstance(authors, str):
            authors = [{"text": authors}]
        author_names = ", ".join(author.get("text", "") for author in authors if isinstance(author, dict))
        summary = f"Published at {venue}. Authors: {author_names}".strip()

        items.append(
            {
                "id": make_id(url_str or title),
                "date": today,
                "source": "dblp",
                "title": title,
                "url": url_str,
                "raw_summary": summary,
            }
        )
    return items


def fetch_dblp(days_back: int = 1) -> list[dict]:
    logger.info(f"开始抓取 DBLP (过去 {days_back} 天)...")
    items: list[dict] = []

    cutoff_date = datetime.now() - timedelta(days=days_back)
    cutoff_year = cutoff_date.year

    for query in DBLP_SEARCH_QUERIES:
        query_variants = [
            f"{query} {cutoff_year}",
            query,
        ]
        query_items: list[dict] = []
        last_error: Exception | None = None

        for variant in query_variants:
            try:
                url = _build_url(variant, MAX_ITEMS_PER_SOURCE)
                data = _request_json(url)
                hits = data.get("result", {}).get("hits", {}).get("hit", [])
                query_items = _extract_items(hits, cutoff_year)
                if variant != query and query_items:
                    logger.debug("DBLP query fallback succeeded: '{}' -> '{}'", query, variant)
                break
            except error.HTTPError as exc:
                last_error = exc
                if exc.code >= 500:
                    logger.warning("DBLP 临时错误，query='{}'，variant='{}'，status={}", query, variant, exc.code)
                else:
                    logger.warning("DBLP 请求失败，query='{}'，variant='{}'，status={}", query, variant, exc.code)
            except Exception as exc:
                last_error = exc
                logger.warning("DBLP 请求异常，query='{}'，variant='{}'，error={}", query, variant, exc)

        if last_error and not query_items:
            logger.warning("跳过 DBLP query='{}'，未取到结果: {}", query, last_error)
            continue

        items.extend(query_items)

    deduped = {item["id"]: item for item in items}
    final_items = list(deduped.values())
    logger.info(f"DBLP 抓取完成，共 {len(final_items)} 条数据。")
    return final_items


if __name__ == "__main__":
    from src.utils import setup_logger

    setup_logger()
    print(fetch_dblp()[:2])
