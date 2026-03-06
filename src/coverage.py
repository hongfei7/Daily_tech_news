"""Coverage explanation for representative LLM sampling."""

from __future__ import annotations


def build_coverage_summary(items: list[dict], selected_items: list[dict], selector_stats: dict) -> dict:
    total_items = len(items)
    stable_topics = {item.get("stable_topic", "Other") for item in items if item.get("stable_topic")}
    selected_stable_topics = {item.get("stable_topic", "Other") for item in selected_items if item.get("stable_topic")}
    emerging_topics = {item.get("emerging_topic") for item in items if item.get("emerging_topic")}
    selected_emerging_topics = {item.get("emerging_topic") for item in selected_items if item.get("emerging_topic")}

    summary = {
        "total_items": total_items,
        "llm_items_selected": len(selected_items),
        "stable_topic_coverage": len(selected_stable_topics),
        "emerging_topic_coverage": len(selected_emerging_topics),
        "bucket_distribution": {
            "top_pool": int(selector_stats.get("top_bucket_count", 0)),
            "stable_pool": int(selector_stats.get("stable_bucket_count", 0)),
            "emerging_pool": int(selector_stats.get("emerging_bucket_count", 0)),
        },
        "coverage_ratio": round(len(selected_items) / max(1, total_items), 3),
    }
    summary["human_readable_summary"] = (
        f"今日共处理 {total_items} 条科技信息，全部参与趋势统计；其中 {len(selected_items)} 条进入 LLM 精读，"
        f"包括 {summary['bucket_distribution']['top_pool']} 条头部高价值内容、"
        f"{summary['bucket_distribution']['stable_pool']} 条稳定主题覆盖样本、"
        f"{summary['bucket_distribution']['emerging_pool']} 条动态热点保底样本，"
        f"覆盖了 {len(selected_stable_topics)}/{max(1, len(stable_topics))} 个 stable topics 和 "
        f"{len(selected_emerging_topics)}/{max(1, len(emerging_topics) or 1)} 个 emerging topics。"
    )
    return summary
