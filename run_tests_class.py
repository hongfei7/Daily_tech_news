import pytest
import sys

with open("test_class_out.txt", "w", encoding="utf-8") as f:
    sys.stdout = f
    sys.stderr = f
    pytest.main(["-v", "--tb=short", "tests/test_classifier.py"])
