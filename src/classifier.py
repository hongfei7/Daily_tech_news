"""Stable topic classification and lightweight tag extraction."""

from __future__ import annotations

import re
from collections import Counter

from src.config import TOPICS


TOPIC_RULES: dict[str, list[str]] = {
    "AI Agents": [
        r"\bagent(s)?\b",
        r"browser use",
        r"computer use",
        r"tool use",
        r"multi-agent",
        r"workflow agent",
        r"mcp",
        r"model context protocol",
    ],
    "Open-source Models": [
        r"\bllama\b",
        r"\bmistral\b",
        r"\bqwen\b",
        r"\bgemma\b",
        r"\bmixtral\b",
        r"\bdeepseek\b",
        r"open[- ]weights",
        r"open[- ]source model",
        r"small reasoning model",
    ],
    "AI Coding Tools": [
        r"cursor",
        r"windsurf",
        r"cline",
        r"copilot",
        r"devin",
        r"swe-bench",
        r"code review",
        r"ai ide",
        r"coding agent",
    ],
    "Chips / Compute / Infra": [
        r"\bgpu\b",
        r"\btpu\b",
        r"\bh100\b",
        r"\bb200\b",
        r"\bcuda\b",
        r"\btensorrt\b",
        r"inference",
        r"serving",
        r"throughput",
        r"compiler",
    ],
    "Robotics": [
        r"robot",
        r"robotics",
        r"humanoid",
        r"embodied",
        r"manipulation",
        r"autonomous driving",
    ],
    "Security / AI Safety": [
        r"safety",
        r"alignment",
        r"red team",
        r"security",
        r"jailbreak",
        r"vulnerability",
        r"policy model",
    ],
    "Data Infra / Vector DB / RAG": [
        r"\brag\b",
        r"vector db",
        r"vector database",
        r"milvus",
        r"qdrant",
        r"weaviate",
        r"pinecone",
        r"retrieval",
        r"embedding",
    ],
    "Research Breakthroughs": [
        r"\bsota\b",
        r"breakthrough",
        r"benchmark",
        r"paper",
        r"reasoning",
        r"architecture",
        r"diffusion",
        r"world model",
    ],
}

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "into",
    "using",
    "new",
    "open",
    "source",
    "model",
    "models",
    "tool",
    "tools",
    "launch",
    "release",
    "released",
    "today",
    "their",
    "about",
    "over",
    "after",
}

PHRASE_PATTERNS = [
    r"\b[A-Z][a-zA-Z0-9]+(?:[- ][A-Z][a-zA-Z0-9]+)+\b",
    r"\b[a-z]+(?:[-/][a-z0-9]+){1,3}\b",
    r"\b[A-Z]{2,}(?:[-/][A-Z0-9]+)*\b",
    r"\b[a-z]+ [a-z]+(?: model| agent| benchmark| protocol| inference| database| reasoning)\b",
]


def _normalize_text(title: str, summary: str) -> str:
    return f"{title}\n{summary}".strip()


def classify_stable_topic(title: str, summary: str) -> str:
    text = _normalize_text(title, summary).lower()
    best_topic = "Other"
    best_score = 0

    for topic in TOPIC_RULES:
        score = sum(1 for pattern in TOPIC_RULES[topic] if re.search(pattern, text))
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic if best_topic in TOPICS else "Other"


def _extract_candidate_tokens(text: str) -> list[str]:
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9\-]{2,}\b", text)
    return [word.lower() for word in words if word.lower() not in STOPWORDS]


def extract_tags(title: str, summary: str, limit: int = 8) -> list[str]:
    source_text = _normalize_text(title, summary)
    lowered = source_text.lower()
    candidates: Counter[str] = Counter()

    for phrase_pattern in PHRASE_PATTERNS:
        for match in re.findall(phrase_pattern, source_text):
            cleaned = re.sub(r"\s+", " ", match.strip())
            if len(cleaned) >= 3:
                candidates[cleaned] += 3

    for token in _extract_candidate_tokens(lowered):
        if len(token) >= 4:
            candidates[token] += 1

    ordered = [tag for tag, _ in candidates.most_common() if tag.lower() not in STOPWORDS]
    deduped: list[str] = []
    seen = set()
    for tag in ordered:
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(tag)
        if len(deduped) >= limit:
            break
    return deduped


def classify_item(title: str, summary: str, use_llm: bool = False) -> str:
    del use_llm
    return classify_stable_topic(title, summary)


def classify_item_multi(title: str, summary: str) -> dict[str, object]:
    stable_topic = classify_stable_topic(title, summary)
    tags = extract_tags(title, summary)
    emerging_topic = tags[0] if stable_topic == "Other" and tags else ""
    return {
        "stable_topic": stable_topic,
        "emerging_topic": emerging_topic,
        "tags": tags,
    }


def get_keywords(title: str, summary: str) -> list[str]:
    return extract_tags(title, summary, limit=5)
