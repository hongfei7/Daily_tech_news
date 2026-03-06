"""Rule-first summarization with optional LLM enhancement."""

from __future__ import annotations

import re

from src.llm_client import call_minimax_llm
from src.utils import truncate


def generate_one_line_summary(title: str, raw_summary: str, use_llm: bool = False) -> str:
    if use_llm:
        prompt = (
            "请用中文写一句不超过60字的摘要，强调这条科技信息对程序员意味着什么，不要复述标题。\n"
            f"标题：{title}\n摘要：{raw_summary}"
        )
        llm_summary = call_minimax_llm(prompt, "你是程序员科技新闻编辑。")
        if llm_summary:
            return truncate(llm_summary.strip(), max_chars=80)

    summary = re.sub(r"\[[^\]]+\]", "", raw_summary).strip()
    summary = re.sub(r"\s+", " ", summary)
    lead = truncate(summary, max_chars=42) if summary else ""
    if any(keyword in title.lower() for keyword in ["agent", "copilot", "cursor", "devin"]):
        prefix = "这意味着 AI 自动化开发工具链继续前移"
    elif any(keyword in title.lower() for keyword in ["gpu", "cuda", "inference", "nvidia"]):
        prefix = "这意味着模型部署和推理成本结构可能继续变化"
    elif any(keyword in title.lower() for keyword in ["rag", "vector", "database", "retrieval"]):
        prefix = "这意味着工程侧检索和数据基础设施仍在快速演进"
    else:
        prefix = "这意味着开发者需要关注相关技术栈的新能力"
    return truncate(f"{prefix}：{lead or title}", max_chars=80)


def summarize_stable_topic(topic: str, items: list[dict], trend_delta: float) -> str:
    if not items:
        return f"{topic} 今日暂无显著新增。"
    top_item = max(items, key=lambda item: item.get("final_score", 0.0))
    trend_text = "升温" if trend_delta > 1 else "回落" if trend_delta < -1 else "持平"
    return truncate(
        f"{topic} 今日由《{top_item['title']}》带动，近7天整体{trend_text}，说明该方向仍在持续吸收开发者注意力。",
        88,
    )


def summarize_emerging_topic(topic: str, items: list[dict], growth_rate: float) -> str:
    if not items:
        return f"{topic} 最近升温，但暂无代表样本。"
    top_item = max(items, key=lambda item: item.get("final_score", 0.0))
    text = f"{topic} 近几天增长 {growth_rate:.1f}x，当前更偏"
    title = top_item["title"].lower()
    if any(word in title for word in ["paper", "benchmark", "reasoning", "research"]):
        text += "研究热"
    elif any(word in title for word in ["tool", "sdk", "framework", "infra", "database"]):
        text += "工程热"
    else:
        text += "产品热"
    text += f"，代表链接是《{top_item['title']}》。"
    return truncate(text, 90)
