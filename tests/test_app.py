from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.database import list_leads


def test_intake_dashboard_and_followup(analysis):
    app = AppTest.from_file("../app.py", default_timeout=30).run()
    assert not app.exception
    app.sidebar.radio[0].set_value("New lead").run()
    app.button[0].click().run()
    assert app.text_input(key="name").value == "Kavya Menon (Demo)"
    analysis.summary = "Buyer seeks a 2 BHK in Whitefield."
    analysis.intent_evidence = "I want to buy a 2 BHK in Whitefield"
    analysis.timeline_days = 25
    analysis.timeline_evidence = "Within 25 days"
    analysis.financing_evidence = "My home loan of 60 lakh is approved"
    with patch("src.workflow.generate", return_value=analysis.model_dump_json()):
        next(b for b in app.button if b.label == "Analyze and save lead").click().run()
    assert not app.exception
    assert len(list_leads()) == 1
    app.sidebar.radio[0].set_value("Dashboard").run()
    assert not app.exception
    assert app.metric[0].value == "1"
    next(b for b in app.button if b.label == "Save follow-up").click().run()
    assert list_leads()[0]["followup"]["status"] == "Pending"
    app.sidebar.radio[0].set_value("Follow-ups").run()
    assert not app.exception
    next(s for s in app.selectbox if s.label == "Status").set_value("Completed")
    next(b for b in app.button if b.label == "Save follow-up").click().run()
    assert list_leads()[0]["followup"]["status"] == "Completed"
