import unittest

from src.models import Item
from src.scoring import score_item, calculate_importance, calculate_novelty

class TestScoring(unittest.TestCase):
    
    def setUp(self):
        self.item = Item(
            id="test", date="2024-05-01", source="github",
            title="Awesome Agent Tool", url="http://test",
            raw_summary="[Stars: 5000] This is a great tool.",
            topic="AI Agents"
        )
        self.existing = ["Old Agent Tool", "Something else"]
        self.topic_counts = {"AI Agents": 10}

    def test_importance(self):
        score = calculate_importance(self.item)
        # 基础分 0.5 + 识别到 stars 加成
        self.assertTrue(score > 0.5)

    def test_novelty(self):
        # 不太相似
        nov = calculate_novelty(self.item, ["Completely Different Title"])
        self.assertTrue(nov > 0.5)
        
        # 极其相似
        nov_low = calculate_novelty(self.item, ["Awesome Agent Tools"])
        self.assertTrue(nov_low <= 0.5)

    def test_full_scoring(self):
        scored_item = score_item(self.item, self.existing, self.topic_counts)
        self.assertTrue(scored_item.final_score > 0)
        self.assertTrue(scored_item.final_score <= 100)

if __name__ == "__main__":
    unittest.main()
