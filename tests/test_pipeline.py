import os
import tempfile
from pathlib import Path
from unittest.mock import patch

temp_dir = tempfile.TemporaryDirectory()
os.environ["DB_PATH"] = str(Path(temp_dir.name) / "test.db")

from src.database import init_db, query_items
from src.pipeline import run_pipeline


def test_run_pipeline_no_crash():
    init_db()
    fake_items = [
        {
            "id": "1",
            "date": "2099-03-06",
            "source": "github",
            "title": "modelcontextprotocol/servers",
            "url": "https://example.com/1",
            "raw_summary": "[Stars: 1234] MCP servers are expanding.",
        },
        {
            "id": "2",
            "date": "2099-03-06",
            "source": "arxiv",
            "title": "Small reasoning models",
            "url": "https://example.com/2",
            "raw_summary": "New paper on small reasoning models.",
        },
    ]
    with patch("src.pipeline.fetch_arxiv", return_value=fake_items), patch("src.pipeline.fetch_github", return_value=[]), patch(
        "src.pipeline.fetch_blogs", return_value=[]
    ), patch("src.pipeline.fetch_hacker_news", return_value=[]), patch("src.pipeline.fetch_dblp", return_value=[]):
        result = run_pipeline(days_back=0)
    assert result["status"] == "ok"
    assert query_items(limit=10)
