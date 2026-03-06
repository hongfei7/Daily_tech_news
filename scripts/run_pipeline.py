"""
run_pipeline.py - 手动运行数据抓取与处理流程
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import run_pipeline
from src.utils import setup_logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行科技趋势数据抓取 Pipeline")
    parser.add_argument("--days", type=int, default=1, help="回溯抓取的天数 (默认: 1)")
    args = parser.parse_args()

    setup_logger("run_pipeline")
    run_pipeline(days_back=args.days)
