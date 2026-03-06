"""
init_db.py - 初始化 SQLite 数据库
"""

import sys
from pathlib import Path

# 添加项目根目录到 sys.path，以便可以直接运行脚本
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_db
from src.utils import setup_logger

if __name__ == "__main__":
    logger = setup_logger("init_db")
    logger.info("开始初始化科技趋势数据库...")
    init_db()
    logger.info("初始化完成！")
