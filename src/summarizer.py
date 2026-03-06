"""
summarizer.py - 为每个 Item 生成一句话摘要
"""

import re
from loguru import logger
from src.utils import truncate
from src.llm_client import call_minimax_llm

def generate_one_line_summary(title: str, raw_summary: str) -> str:
    """
    优先使用 MiniMax LLM 生成对程序员有价值的一句话摘要，如果失败则尝试截断组合。
    """
    prompt = f"请提取以下科技资讯的核心信息，并用中文写一句对程序员有价值的一句话摘要，体现方向和价值。尽量在50字左右，不要超过80字。\n标题：{title}\n摘要：{raw_summary}"
    sys_prompt = "你是一个专为程序员服务的科技趋势提炼助手。直接输出一句话摘要，不要带任何前缀或废话。"
    
    llm_summary = call_minimax_llm(prompt, sys_prompt)
    if llm_summary:
        return truncate(llm_summary.strip(' "\''), max_chars=80)
    
    # 当前为占位：直接尝试组合标题和前 50 字描述
    clean_desc = re.sub(r'\[.*?\]', '', raw_summary)  # 去掉开头的类似 [Stars: 100]
    clean_desc = clean_desc.strip()
    
    # 取第一句话或者前 60 个字符
    match = re.search(r'^(.*?)[.?!。？！]', clean_desc)
    if match:
        first_sentence = match.group(1)
    else:
        first_sentence = truncate(clean_desc, max_chars=60).rstrip('…')
        
    combined = f"{title}: {first_sentence}"
    return truncate(combined, max_chars=80)
