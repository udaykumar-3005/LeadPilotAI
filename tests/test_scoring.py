import pytest

from src.scoring import score_lead


@pytest.mark.parametrize("intent,days,finance,score,priority", [
    ("buy", 30, "ready", 100, "Hot"),
    ("buy", 31, "pending", 75, "Hot"),
    ("buy", 90, "unknown", 65, "Warm"),
    ("buy", 91, "unknown", 55, "Warm"),
    ("explore", 180, "unknown", 30, "Cold"),
    ("explore", 181, "unknown", 20, "Cold"),
    ("unknown", None, "unknown", 10, "Cold"),
])
def test_priority_rules(analysis, intent, days, finance, score, priority):
    analysis.intent, analysis.timeline_days, analysis.financing = intent, days, finance
    result = score_lead(analysis)
    assert result["score"] == score
    assert result["priority"] == priority
    assert sum(result["reasons"].values()) == score
