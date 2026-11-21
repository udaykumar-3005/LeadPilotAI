import json
from unittest.mock import patch

import pytest

from src.chatbot import answer
from src.database import delete_lead, hosted, list_leads, save_followup, save_lead


def test_storage_and_followup_are_isolated(lead, analysis):
    first = save_lead(lead, analysis.model_dump())
    second = save_lead(lead.model_copy(update={"name": "Another buyer"}), analysis.model_dump())
    task = {"action": "Call about visit", "due_date": "2026-11-23", "status": "Pending"}
    save_followup(first["id"], task)
    records = {r["id"]: r for r in list_leads()}
    assert records[first["id"]]["followup"] == task
    assert records[second["id"]]["followup"] is None
    task["status"] = "Completed"
    save_followup(first["id"], task)
    assert next(r for r in list_leads() if r["id"] == first["id"])["followup"]["status"] == "Completed"
    delete_lead(first["id"])
    assert [r["id"] for r in list_leads()] == [second["id"]]


def test_chat_receives_only_selected_lead(lead, analysis):
    first = save_lead(lead, analysis.model_dump())
    save_lead(lead.model_copy(update={"name": "Private Other Buyer"}), analysis.model_dump())
    with patch("src.chatbot.generate", return_value="Emphasize metro access.") as model, patch("src.chatbot.retrieve") as search:
        answer(first, "What should I emphasize?", [])
    context = json.loads(model.call_args.args[0])
    assert context["selected_lead"]["name"] == "Ananya Rao"
    assert "Private Other Buyer" not in model.call_args.args[0]
    search.assert_not_called()


def test_property_chat_uses_retrieval(lead, analysis):
    record = {"lead": lead.model_dump(), "analysis": analysis.model_dump()}
    with patch("src.chatbot.retrieve", return_value=([{"id": "P001"}], "Sample")) as search, patch("src.chatbot.generate", return_value="[P001]") as model:
        answer(record, "Find a flat", [], True)
    search.assert_called_once()
    assert json.loads(model.call_args.args[0])["catalogue"] == [{"id": "P001"}]


def test_partial_hosted_config_does_not_silently_use_sqlite(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    with pytest.raises(RuntimeError, match="both"):
        hosted()
