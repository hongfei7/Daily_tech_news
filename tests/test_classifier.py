import unittest

from src.classifier import classify_item

class TestClassifier(unittest.TestCase):

    def test_classification(self):
        topic = classify_item("Llama 3 70B Release", "Meta has released the newest Llama open-source model")
        self.assertEqual(topic, "Open-source Models")
        
        topic2 = classify_item("CUDA 12.0 Optimization", "NVIDIA GPU inference optimizations for LLMs")
        self.assertEqual(topic2, "Chips / Compute / Infra")
        
        topic3 = classify_item("Making a sandwich", "Just a regular blog post")
        self.assertEqual(topic3, "Other")

if __name__ == "__main__":
    unittest.main()
