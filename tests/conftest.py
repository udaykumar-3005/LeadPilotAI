import pytest

from src.models import Analysis, Lead


@pytest.fixture
def lead():
    return Lead(
        name="Ananya Rao", location="Whitefield", requirement="2 BHK near metro",
        budget_lakh=85, timeline="Within 30 days",
        message="I want to buy a flat. My home loan is approved. Can I visit this weekend?",
    )


@pytest.fixture
def analysis():
    return Analysis(
        summary="Buyer seeks a 2 BHK in Whitefield.", intent="buy", intent_evidence="I want to buy a flat",
        requirements=["2 BHK", "Near metro"], objections=[], missing_information=["Preferred visit time"],
        timeline_days=30, timeline_evidence="Within 30 days", financing="ready",
        financing_evidence="My home loan is approved", next_action="Confirm a preferred visit time.",
        suggested_response="Thanks for your enquiry. What time would suit you for a visit?",
    )


@pytest.fixture(autouse=True)
def isolated_storage(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "leads.db"))
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")
