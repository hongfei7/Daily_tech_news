"""
classifier.py - 根据标题和摘要进行 Topic 分类（MVP阶段使用关键词匹配）
"""

import re
from loguru import logger
from src.config import TOPICS

# 关键词到 Topic 的映射
TOPIC_RULES = {
    "AI Agents": [
        r"\bagent(s)?\b", r"auto-gpt", r"babyagi", r"multi-agent", r"tool use", r"copilot"
    ],
    "Open-source Models": [
        r"llama", r"mistral", r"qwen", r"gemma", r"mixtral", r"open-source llm", r"\b7b\b", r"\b70b\b", r"open model"
    ],
    "AI Coding Tools": [
        r"coding", r"code generation", r"copilot", r"cursor", r"code-llama", r"starcoder", r"devin", r"swe-bench"
    ],
    "Chips / Compute / Infra": [
        r"nvidia", r"gpu", r"h100", r"tpu", r"inference", r"vllm", r"tensorrt", r"cuda", r"compute", r"hardware"
    ],
    "Robotics": [
        r"roboti[cs]", r"embodied", r"manipulation", r"optimus", r"figure 01", r"humanoid"
    ],
    "Security / AI Safety": [
        r"safety", r"jailbreak", r"alignment", r"red teaming", r"security", r"hallucination", r"vulnerability"
    ],
    "Data Infra / Vector DB / RAG": [
        r"rag", r"vector db", r"pinecone", r"milvus", r"weaviate", r"qdrant", r"retrieval-augmented", r"database"
    ],
    "Research Breakthroughs": [
        r"state-of-the-art", r"\bsota\b", r"breakthrough", r"transformer", r"mamba", r"ssm", r"architecture", r"reward model", r"rlhf"
    ]
}

from src.llm_client import call_minimax_llm

def classify_item(title: str, summary: str) -> str:
    """
    使用 LLM 对抓取的数据进行准确的领域归类。
    如果没有匹配或模型出错，则退回使用关键词匹配规则归类为 "Other"。
    """
    text = f"{title} {summary}".lower()
    
    # LLM 分类
    topics_str = ", ".join(TOPICS)
    prompt = f"请将以下科技资讯归类到最合适的一个给定的主题中。你只能且必须从下面的主题列表中挑选一个完整的原样输出：[{topics_str}]。\n\n标题：{title}\n摘要：{summary}"
    sys_prompt = "你是一个精确的分类器，只能输出预定列表里的一个主题，绝对不可添加任何标点符号、解释或不在列表内的新主题。"
    
    llm_topic = call_minimax_llm(prompt, sys_prompt)
    if llm_topic:
        llm_topic = llm_topic.strip(' "\'')
        # 校验是否确实是一个有效topic（无视大小写）
        for t in TOPICS:
            if t.lower() == llm_topic.lower():
                return t
                
    # 失败回退到关键词规则分类
    best_topic = "Other"
    max_matches = 0
    
    for topic, pattern_list in TOPIC_RULES.items():
        matches = 0
        for pattern in pattern_list:
            if re.search(pattern, text):
                matches += 1
        
        if matches > max_matches:
            max_matches = matches
            best_topic = topic
            
    return best_topic

def get_keywords(title: str, summary: str) -> list[str]:
    """
    提取命中的关键词
    """
    text = f"{title} {summary}".lower()
    matched = []
    
    for topic, pattern_list in TOPIC_RULES.items():
        for pattern in pattern_list:
            if re.search(pattern, text) and pattern not in matched:
                # 简单清理正则符号以便展示
                clean_p = pattern.replace(r"\b", "").replace(r"(s)?", "s")
                matched.append(clean_p)
                
    return list(set(matched))[:5]  # 最多存5个
