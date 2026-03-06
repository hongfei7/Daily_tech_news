from collections import Counter

from src.llm_selector import select_representative_items


def test_selector_uses_three_buckets_and_limits_single_topic():
    items = []
    for idx in range(20):
        items.append(
            {
                "id": f"agent-{idx}",
                "date": "2026-03-06",
                "source": "github" if idx < 10 else "arxiv",
                "title": f"Agent item {idx}",
                "stable_topic": "AI Agents",
                "emerging_topic": "MCP" if idx < 5 else "",
                "final_score": 90 - idx,
            }
        )
    for idx in range(8):
        items.append(
            {
                "id": f"coding-{idx}",
                "date": "2026-03-06",
                "source": "hacker_news",
                "title": f"AI IDE benchmark {idx}",
                "stable_topic": "AI Coding Tools",
                "emerging_topic": "AI IDE Benchmark",
                "final_score": 70 - idx,
            }
        )
    for idx in range(6):
        items.append(
            {
                "id": f"infra-{idx}",
                "date": "2026-03-06",
                "source": "nvidia_blog",
                "title": f"Inference stack {idx}",
                "stable_topic": "Chips / Compute / Infra",
                "emerging_topic": "",
                "final_score": 65 - idx,
            }
        )
    result = select_representative_items(items, "2026-03-06")
    buckets = {bucket for bucket, _ in result.bucket_map.values()}
    assert {"top_pool", "stable_pool", "emerging_pool"} <= buckets
    stable_counts = Counter(item["stable_topic"] for item in result.selected_items)
    assert stable_counts["AI Agents"] < len(result.selected_items)
