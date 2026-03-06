"""
llm_client.py - 封装对 MiniMax API 的调用
"""

import os
import requests
from loguru import logger
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.parent

from dotenv import load_dotenv

def get_minimax_key() -> str:
    """获取 MiniMax 密钥，按优先级依次从环境变量读取"""
    env_key = (
        os.environ.get("MINIMAX_API_KEY")
        or os.environ.get("MiniMax_API_Key")
        or os.environ.get("MINIMAX_API_KEY_d")
    )
    if env_key:
        return env_key.strip()

    raise ValueError(
        "未找到 MiniMax API Key，请设置环境变量："
        "MINIMAX_API_KEY / MiniMax_API_Key / MINIMAX_API_KEY_d"
    )
        
    # 本地可以使用 .env 文件
    load_dotenv(BASE_DIR / ".env")
    env_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("MiniMax_API_Key")
    if env_key:
        return env_key
        
    logger.error("未找到 MiniMax API 密钥，请在环境或 .env 中配置 MiniMax_API_Key")
    return ""

def call_minimax_llm(prompt: str, system_prompt: str = "") -> Optional[str]:
    """
    调用 MiniMax M2.5 模型。如果失败返回 None。
    """
    api_key = get_minimax_key()
    if not api_key:
        return None
        
    url = "https://api.minimax.chat/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": "MiniMax-M2.5",
        "messages": messages,
        "temperature": 0.1,  # 稍微低一些，保证内容可靠
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp_json = resp.json()
        if "choices" in resp_json and len(resp_json["choices"]) > 0:
            return resp_json["choices"][0]["message"]["content"].strip()
        else:
            logger.debug(f"LLM API 响应异常: {resp_json}")
            return None
    except Exception as e:
        logger.debug(f"LLM API 请求失败: {e}")
        return None
