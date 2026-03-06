from src.coverage import build_coverage_summary


def test_coverage_summary_builds_human_readable_output():
    items = [
        {"stable_topic": "AI Agents", "emerging_topic": "MCP"},
        {"stable_topic": "AI Coding Tools", "emerging_topic": "AI IDE Benchmark"},
        {"stable_topic": "Other", "emerging_topic": ""},
    ]
    selected = items[:2]
    stats = {
        "top_bucket_count": 1,
        "stable_bucket_count": 1,
        "emerging_bucket_count": 0,
    }
    summary = build_coverage_summary(items, selected, stats)
    assert summary["coverage_ratio"] > 0
    assert "今日共处理" in summary["human_readable_summary"]
