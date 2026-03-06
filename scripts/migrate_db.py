"""Safely migrate an existing database to the current schema."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import migrate_db
from src.utils import setup_logger


if __name__ == "__main__":
    logger = setup_logger("migrate_db")
    logger.info("running database migration")
    migrate_db()
    logger.info("database migration completed")
