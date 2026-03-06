"""Run the full daily pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import init_db, migrate_db
from src.pipeline import run_pipeline
from src.utils import setup_logger


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the tech trend pipeline.")
    parser.add_argument("--days", type=int, default=1, help="Look back N days when fetching.")
    args = parser.parse_args()

    setup_logger("run_pipeline")
    init_db()
    migrate_db()
    result = run_pipeline(days_back=args.days)
    print(result)
