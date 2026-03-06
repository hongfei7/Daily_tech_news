"""Backfill demo data for local UI verification."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.aggregator import aggregate_daily_stats
from src.classifier import classify_item_multi
from src.coverage import build_coverage_summary
from src.database import init_db, upsert_emerging_topic_stat, upsert_item, upsert_llm_selection_stat
from src.emerging import build_emerging_stats, discover_emerging_topics
from src.llm_selector import select_representative_items
from src.models import Item, LLMSelectionStat
from src.scoring import score_item
from src.summarizer import generate_one_line_summary
from src.utils import setup_logger


DEMO_ITEMS = [
    ("openai_blog", "OpenAI adds Model Context Protocol support to Responses API", "MCP support lands in production workflow APIs for tool calling and agent orchestration."),
    ("anthropic_blog", "Claude Code update improves browser agent reliability", "Anthropic ships browser automation improvements for code and web tasks."),
    ("github", "browser-use/browser-use", "[Stars: 61234] Browser agent framework for controlling web apps with LLMs."),
    ("github", "modelcontextprotocol/servers", "[Stars: 18500] Official MCP servers bundle expands IDE and data integrations."),
    ("arxiv", "Small reasoning models outperform larger baselines on cost efficiency", "A paper shows small reasoning models closing the quality gap with careful test-time compute."),
    ("meta_ai_blog", "Llama tools for on-device agents", "Meta details low-latency on-device agent runtimes and mobile inference tooling."),
    ("nvidia_blog", "Blackwell inference stack reduces serving cost for agent workloads", "New inference stack changes cost/performance profile for production agents."),
    ("hacker_news", "Cursor benchmark for AI IDEs sparks debate", "[HN Points: 620] Community debate around AI IDE benchmark validity and practical coding gains."),
    ("github", "milvus-io/milvus", "[Stars: 32100] Multi-vector search update improves RAG retrieval quality."),
    ("dblp", "Research on video generation tooling orchestration", "Framework analysis for multimodal video generation stacks."),
]


def main() -> None:
    logger = setup_logger("demo_data")
    init_db()
    today = datetime.now(timezone.utc).date()
    existing_titles: list[str] = []
    topic_counts: dict[str, int] = {}
    inserted: list[Item] = []

    for offset in range(7):
        date_value = str(today - timedelta(days=offset))
        for index, (source, title, raw_summary) in enumerate(DEMO_ITEMS):
            if offset > 2 and index % 2 == 0:
                continue
            classified = classify_item_multi(title, raw_summary)
            item = Item(
                id=f"demo-{offset}-{index}",
                date=date_value,
                source=source,
                title=title,
                url=f"https://example.com/{offset}/{index}",
                raw_summary=raw_summary,
                one_line_summary=generate_one_line_summary(title, raw_summary),
                stable_topic=classified["stable_topic"],
                emerging_topic=classified["emerging_topic"],
                tags=classified["tags"],
                topic=classified["stable_topic"],
                keywords=classified["tags"],
            )
            score_item(item, existing_titles, topic_counts)
            upsert_item(item)
            inserted.append(item)
            existing_titles.append(title)
            topic_counts[item.stable_topic] = topic_counts.get(item.stable_topic, 0) + 1

    for offset in range(7):
        date_value = str(today - timedelta(days=offset))
        day_items = [item.model_dump() for item in inserted if item.date == date_value]
        candidates = discover_emerging_topics([item.model_dump() for item in inserted], date_value)
        for stat in build_emerging_stats(date_value, candidates):
            upsert_emerging_topic_stat(stat)
        selection = select_representative_items(day_items, date_value)
        coverage = build_coverage_summary(day_items, selection.selected_items, selection.stats)
        upsert_llm_selection_stat(
            LLMSelectionStat(
                date=date_value,
                total_items=coverage["total_items"],
                stable_topic_count=coverage["stable_topic_coverage"],
                emerging_topic_count=coverage["emerging_topic_coverage"],
                llm_items_selected=coverage["llm_items_selected"],
                top_bucket_count=coverage["bucket_distribution"]["top_pool"],
                stable_bucket_count=coverage["bucket_distribution"]["stable_pool"],
                emerging_bucket_count=coverage["bucket_distribution"]["emerging_pool"],
                coverage_ratio=coverage["coverage_ratio"],
                notes=coverage["human_readable_summary"],
            )
        )
        for selected in selection.selected_items:
            item = next(item for item in inserted if item.id == selected["id"])
            bucket, reason = selection.bucket_map[item.id]
            item.llm_selected = 1
            item.selection_bucket = bucket
            item.selection_reason = reason
            upsert_item(item)
        aggregate_daily_stats(date_value)

    logger.info("demo data backfilled")


if __name__ == "__main__":
    main()
