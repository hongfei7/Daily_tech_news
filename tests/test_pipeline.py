import unittest
import os
import tempfile
from pathlib import Path

# mock DB path for tests
temp_dir = tempfile.TemporaryDirectory()
os.environ["DB_PATH"] = str(Path(temp_dir.name) / "test.db")

from src.database import init_db, query_items
from src.pipeline import run_pipeline

class TestPipeline(unittest.TestCase):

    def setUp(self):
        init_db()

    def tearDown(self):
        temp_dir.cleanup()

    def test_run_pipeline_no_crash(self):
        # We don't want to actually hit APIs heavily, 
        # but running with days_back=0 should do minimal fetching or empty
        # We just want to ensure it doesn't crash
        try:
            run_pipeline(days_back=0)
            items = query_items()
            self.assertIsInstance(items, list)
        except Exception as e:
            self.fail(f"Pipeline crashed: {e}")

if __name__ == "__main__":
    unittest.main()
