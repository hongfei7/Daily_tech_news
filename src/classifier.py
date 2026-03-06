"""Stable topic classification and tag extraction."""

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
        r"\bmcp\b",
        r"model context protocol",
        r"browser agent",
        r"assistant api",
        r"agent sdk",
        r"langgraph",
        r"autogen",
        r"crewai",
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
        r"foundation model",
        r"checkpoint",
        r"instruct model",
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
        r"code assistant",
        r"software engineering",
        r"program synthesis",
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
        r"kernel",
        r"accelerator",
        r"distributed training",
        r"quantization",
        r"vllm",
        r"sglang",
        r"mlx",
    ],
    "Robotics": [
        r"robot",
        r"robotics",
        r"humanoid",
        r"embodied",
        r"manipulation",
        r"autonomous driving",
        r"world model for robotics",
    ],
    "Security / AI Safety": [
        r"safety",
        r"alignment",
        r"red team",
        r"security",
        r"jailbreak",
        r"vulnerability",
        r"policy model",
        r"guardrail",
        r"secure",
        r"privacy",
        r"adversarial",
    ],
    "Data Infra / Vector DB / RAG": [
        r"\brag\b",
        r"vector db",
        r"vector database",
        r"vector store",
        r"milvus",
        r"qdrant",
        r"weaviate",
        r"pinecone",
        r"retrieval",
        r"embedding",
        r"chunking",
        r"rerank",
        r"langchain",
        r"llamaindex",
        r"knowledge base",
        r"semantic search",
        r"context7",
        r"context engineering",
        r"pgvector",
        r"zilliz",
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
        r"state of the art",
        r"arxiv",
        r"preprint",
        r"dataset",
        r"evaluation",
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
    "repository",
    "enterprise",
    "platform",
}

PHRASE_PATTERNS = [
    r"\b[A-Z][a-zA-Z0-9]+(?:[- ][A-Z][a-zA-Z0-9]+)+\b",
    r"\b[a-z]+(?:[-/][a-z0-9]+){1,3}\b",
    r"\b[A-Z]{2,}(?:[-/][A-Z0-9]+)*\b",
    r"\b[a-z]+ [a-z]+(?: model| agent| benchmark| protocol| inference| database| reasoning| sdk| ide)\b",
]

EMERGING_TAG_HINTS = {
    "mcp": "MCP",
    "model context protocol": "MCP",
    "browser use": "Browser Agents",
    "browser-use": "Browser Agents",
    "browser agent": "Browser Agents",
    "computer use": "Computer-use Agents",
    "small reasoning": "Small Reasoning Models",
    "reasoning model": "Small Reasoning Models",
    "ai ide": "AI IDE Benchmark",
    "cursor": "AI IDE Benchmark",
    "windsurf": "AI IDE Benchmark",
    "video generation": "Video Generation Tooling",
    "on-device": "On-device Agents",
    "context7": "Context Engineering",
}


def _normalize_text(title: str, summary: str) -> str:
    text = f"{title}\n{summary}".strip()
    return text.replace("/", " ").replace("_", " ").replace("-", " ")


def _source_fallback_topic(source: str | None) -> str:
    if source in {"arxiv", "dblp"}:
        return "Research Breakthroughs"
    return "Other"


def classify_stable_topic(title: str, summary: str, source: str | None = None) -> str:
    text = _normalize_text(title, summary).lower()
    best_topic = _source_fallback_topic(source)
    best_score = 1 if best_topic != "Other" else 0

    for topic, patterns in TOPIC_RULES.items():
        score = sum(1 for pattern in patterns if re.search(pattern, text))
        if source == "github" and topic in {"Data Infra / Vector DB / RAG", "AI Agents", "AI Coding Tools"}:
            score += 1 if score > 0 else 0
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
            cleaned = cleaned.replace("/", " ").strip()
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


def suggest_emerging_topic(tags: list[str], title: str, summary: str) -> str:
    text = f"{title}\n{summary}\n{' '.join(tags)}".lower()
    for hint, label in EMERGING_TAG_HINTS.items():
        if hint in text:
            return label

    for tag in tags:
        clean_tag = tag.strip()
        if len(clean_tag) < 4:
            continue
        if any(ch.isupper() for ch in clean_tag) or clean_tag.lower() in {"mcp", "cursor", "windsurf", "qdrant", "milvus", "weaviate"}:
            return clean_tag
    return ""


def classify_item(title: str, summary: str, use_llm: bool = False, source: str | None = None) -> str:
    del use_llm
    return classify_stable_topic(title, summary, source=source)


def classify_item_multi(title: str, summary: str, source: str | None = None) -> dict[str, object]:
    stable_topic = classify_stable_topic(title, summary, source=source)
    tags = extract_tags(title, summary)
    emerging_topic = suggest_emerging_topic(tags, title, summary)
    return {
        "stable_topic": stable_topic,
        "emerging_topic": emerging_topic,
        "tags": tags,
    }


def get_keywords(title: str, summary: str) -> list[str]:
    return extract_tags(title, summary, limit=5)
