"""Initialize the SQLite database."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import init_db
from src.utils import setup_logger


if __name__ == "__main__":
    logger = setup_logger("init_db")
    logger.info("initializing database")
    init_db()
    logger.info("database ready")
