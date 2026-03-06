from src.emerging import discover_emerging_topics


def test_emerging_discovery_finds_growing_keyword():
    items = []
    for idx in range(2):
        items.append(
            {
                "id": f"base-{idx}",
                "date": "2026-03-01",
                "source": "github",
                "title": "General LLM tooling",
                "tags": ["General LLM tooling"],
                "stable_topic": "Other",
                "final_score": 50,
                "one_line_summary": "baseline",
            }
        )
    for idx in range(6):
        items.append(
            {
                "id": f"recent-{idx}",
                "date": "2026-03-06",
                "source": "github" if idx % 2 == 0 else "arxiv",
                "title": "MCP workflow update",
                "tags": ["MCP"],
                "stable_topic": "Other",
                "final_score": 80,
                "one_line_summary": "recent",
            }
        )
    candidates = discover_emerging_topics(items, "2026-03-06")
    assert any(candidate.topic == "MCP" for candidate in candidates)
