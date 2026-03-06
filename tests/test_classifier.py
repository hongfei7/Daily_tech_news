from src.classifier import classify_item_multi


def test_stable_topic_always_present():
    result = classify_item_multi("Completely random title", "No obvious topic but still should classify.")
    assert result["stable_topic"]
    assert result["stable_topic"] == "Other"


def test_known_topic_classification():
    result = classify_item_multi("Llama open weights update", "A new open-source model release.")
    assert result["stable_topic"] == "Open-source Models"
    assert result["tags"]
