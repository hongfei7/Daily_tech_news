"""
backfill_demo_data.py - 回填一些测试用 Demo 数据，避免 API 环境受限时页面空缺。
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_db, upsert_item, upsert_daily_stat
from src.models import Item, DailyTopicStat
from src.config import TOPICS
from src.utils import setup_logger

logger = setup_logger("demo_data")

DEMO_DATA = [
    {
        "title": "GPT-4o API Update: Structured Outputs and Improved Performance",
        "url": "https://openai.com/blog/api-updates",
        "source": "openai_blog",
        "topic": "Open-source Models",  # Deliberately varied
        "raw_summary": "We are introducing structured outputs in the API to guarantee that the model will exactly follow your JSON Schemas...",
        "one_line_summary": "GPT-4o API 更新，现在原生支持并保证输出 JSON Schema 结构体匹配。",
    },
    {
        "title": "LLaMA-3 70B Release: The new state of the art in open weights",
        "url": "https://ai.meta.com/blog/llama-3",
        "source": "meta_ai_blog",
        "topic": "Open-source Models",
        "raw_summary": "Today we are releasing LLaMA 3 70B, which beats many proprietary models on popular benchmarks...",
        "one_line_summary": "Meta 发布 Llama-3 70B，在多项核心 Benchmark 上击败闭源闭源模型。",
    },
    {
        "title": "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering",
        "url": "https://arxiv.org/abs/2405.00001",
        "source": "arxiv",
        "topic": "AI Coding Tools",
        "raw_summary": "We introduce SWE-agent, an autonomous system capable of resolving real-world GitHub issues at scale...",
        "one_line_summary": "普林斯顿大学推出 SWE-agent，实现 GitHub 仓库级别的自动化 Issue 修复工具。",
    },
    {
        "title": "Milvus 2.4 vector database released with multi-vector search",
        "url": "https://github.com/milvus-io/milvus",
        "source": "github",
        "topic": "Data Infra / Vector DB / RAG",
        "raw_summary": "[Stars: 25000] Milvus is an open-source vector database built to power embedding similarity search and AI applications...",
        "one_line_summary": "Milvus 2.4 发布，原生支持多向量检索功能，极大增强 RAG 能力。",
    },
    {
        "title": "NVIDIA Blackwell B200 Architecture Technical Overview",
        "url": "https://blogs.nvidia.com/b200-overview",
        "source": "nvidia_blog",
        "topic": "Chips / Compute / Infra",
        "raw_summary": "NVIDIA Blackwell architecture features a new tensor core capable of processing 20 petaflops of FP4 precision...",
        "one_line_summary": "英伟达 B200 芯片架构详解：引入 FP4 精度支持，算力达到 20 PFLOPS。",
    },
    {
        "title": "Figure 01 Humanoid Robot demonstrates autonomous coffee making",
        "url": "https://news.ycombinator.com/item?id=38900012",
        "source": "hacker_news",
        "topic": "Robotics",
        "raw_summary": "[HN Points: 1540] A new video shows the Figure 01 robot autonomously operating a Keurig machine using end-to-end neural networks...",
        "one_line_summary": "Figure 01 人形机器人演示端到端视觉与动作控制，完成泡咖啡等高精度任务。",
    }
]

def backfill():
    init_db()
    
    today = datetime.now(timezone.utc)
    
    logger.info("插入 Demo Items...")
    for i, data in enumerate(DEMO_DATA):
        # 让日期分布在最近 3 天
        days_offset = random.randint(0, 2)
        d_date = (today - timedelta(days=days_offset)).strftime("%Y-%m-%d")
        
        item = Item(
            id=f"demo_id_{i}",
            date=d_date,
            source=data["source"],
            title=data["title"],
            url=data["url"],
            raw_summary=data["raw_summary"],
            one_line_summary=data["one_line_summary"],
            topic=data["topic"],
            importance_score=round(random.uniform(0.6, 0.9), 2),
            novelty_score=round(random.uniform(0.5, 0.9), 2),
            momentum_score=round(random.uniform(0.4, 0.8), 2),
            final_score=round(random.uniform(60, 95), 1)
        )
        upsert_item(item)
        
    logger.info("插入 Demo 每日统计数据...")
    for days_ago in range(7):
        target_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        for topic in TOPICS:
            # 制造一些假的趋势数据
            base_score = random.uniform(30, 80)
            if topic == "Open-source Models" and days_ago < 3:
                base_score += 20  # 让它呈现上升趋势
                
            stat = DailyTopicStat(
                date=target_date,
                topic=topic,
                item_count=random.randint(1, 15),
                avg_importance=round(random.uniform(0.3, 0.9), 2),
                avg_novelty=round(random.uniform(0.3, 0.9), 2),
                avg_momentum=round(random.uniform(0.3, 0.9), 2),
                final_score=round(base_score, 1),
                trend_delta_7d=round(random.uniform(-5.0, +15.0), 1),
                top_summary=f"今天在 {topic} 领域发生了许多重要进展。"
            )
            upsert_daily_stat(stat)

    logger.info("Demo 数据回填完成！你可以启动 Streamlit 查看了。")

if __name__ == "__main__":
    backfill()
