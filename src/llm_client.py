"""
llm_client.py - 封装对 MiniMax API 的调用
"""

import json
import requests
from loguru import logger
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.parent
APIKEY_PATH = BASE_DIR / "src" / "apikey.json"

import os

def get_minimax_key() -> str:
    """获取 apikey.json 中保存的 Gemini / MiniMax 密钥，或从环境变量获取（用于 GitHub Actions）"""
    # 优先从环境变量读取
    env_key = os.environ.get("MINIMAX_API_KEY")
    if env_key:
        return env_key
        
    try:
        if APIKEY_PATH.exists():
            with open(APIKEY_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get("api_keys", {}).get("gemini", "")
    except Exception as e:
        logger.error(f"读取 apikey.json 失败: {e}")
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
