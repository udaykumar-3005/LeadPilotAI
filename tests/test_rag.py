from unittest.mock import patch

import numpy as np

from src.rag import candidates, properties, retrieve


def test_hard_filters(lead):
    matches = candidates(lead.model_dump())
    assert [r["id"] for r in matches] == ["P001"]
    assert candidates(lead.model_copy(update={"budget_lakh": 20}).model_dump()) == []
    assert candidates(lead.model_copy(update={"location": "Unknown city"}).model_dump()) == []


def test_semantic_order_preserves_filters(lead):
    class Encoder:
        def encode(self, texts, **kwargs):
            return np.array([[0, 1]], dtype="float32")

    vectors = np.zeros((len(properties()), 2), dtype="float32")
    vectors[0], vectors[1] = [1, 0], [0, 1]
    with patch("src.rag.embeddings", return_value=(Encoder(), vectors)):
        matches, note = retrieve(lead.model_copy(update={"budget_lakh": 90}).model_dump(), "lake view")
    assert [r["id"] for r in matches] == ["P002", "P001"]
    assert "Semantic" in note


def test_embedding_failure_has_honest_fallback(lead):
    with patch("src.rag.embeddings", side_effect=OSError("offline")):
        matches, note = retrieve(lead.model_dump(), "metro")
    assert matches[0]["id"] == "P001"
    assert "unavailable" in note
