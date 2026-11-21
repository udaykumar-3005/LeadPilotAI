from unittest.mock import patch

import pytest

from src.ai import generate
from src.models import Lead
from src.workflow import analyze_lead


def test_valid_analysis_is_scored(lead, analysis):
    with patch("src.workflow.generate", return_value=analysis.model_dump_json()) as model:
        result = analyze_lead(lead)
    assert result["priority"] == "Hot"
    assert result["score"] == 100
    assert model.call_count == 1


def test_invalid_output_retries_once(lead, analysis):
    with patch("src.workflow.generate", side_effect=["not json", analysis.model_dump_json()]) as model:
        assert analyze_lead(lead)["score"] == 100
    assert model.call_count == 2


def test_invalid_output_stops_after_two_attempts(lead):
    with patch("src.workflow.generate", return_value="{}") as model:
        with pytest.raises(RuntimeError, match="invalid analysis"):
            analyze_lead(lead)
    assert model.call_count == 2


def test_api_failure_does_not_loop(lead):
    with patch("src.workflow.generate", side_effect=RuntimeError("Gemini quota reached")) as model:
        with pytest.raises(RuntimeError, match="quota"):
            analyze_lead(lead)
    assert model.call_count == 1


def test_unfounded_evidence_is_rejected(lead, analysis):
    analysis.financing_evidence = "Customer has cash ready"
    with pytest.raises(ValueError, match="financing"):
        analysis.check_evidence(lead)


def test_missing_key_is_clear(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        generate("test", "test")


def test_missing_fields_fail_before_api():
    with pytest.raises(ValueError):
        Lead(name=" ", location="Pune", requirement="2 BHK", budget_lakh=0, timeline="", message="")
