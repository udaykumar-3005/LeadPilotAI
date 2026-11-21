import csv
import re
from functools import lru_cache
from pathlib import Path

import numpy as np


CATALOGUE = Path(__file__).resolve().parents[1] / "data" / "sample_properties.csv"


@lru_cache(maxsize=1)
def properties():
    with CATALOGUE.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    for row in rows:
        row["price_lakh"] = float(row["price_lakh"])
        row["bedrooms"] = int(row["bedrooms"])
    return rows


def candidates(lead):
    bedroom = re.search(r"\b(\d+)\s*[- ]?\s*(?:bhk|bedroom|bed)\b", lead["requirement"], re.I)
    location = lead["location"].strip().casefold().replace("bangalore", "bengaluru")
    return [
        row for row in properties()
        if row["price_lakh"] <= lead["budget_lakh"]
        and location in (row["city"].casefold(), row["area"].casefold(), f'{row["area"]}, {row["city"]}'.casefold())
        and (not bedroom or row["bedrooms"] == int(bedroom[1]))
    ]


@lru_cache(maxsize=1)
def embeddings():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu", cache_folder=str(CATALOGUE.parent / "models"))
    texts = [f'{p["name"]} {p["area"]} {p["description"]}' for p in properties()]
    vectors = model.encode(texts, normalize_embeddings=True).astype("float32")
    return model, vectors


def retrieve(lead, query, limit=3):
    rows = candidates(lead)
    if not rows:
        return [], "No catalogue properties meet the saved location, budget and bedroom filters."
    try:
        import faiss

        model, vectors = embeddings()
        positions = [properties().index(row) for row in rows]
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(np.ascontiguousarray(vectors[positions]))
        query_vector = model.encode([query], normalize_embeddings=True).astype("float32")
        _, matches = index.search(query_vector, min(limit, len(rows)))
        return [rows[i] for i in matches[0]], "Semantic matches from the fictional sample catalogue."
    except (OSError, RuntimeError, ImportError):
        return sorted(rows, key=lambda p: p["price_lakh"])[:limit], "Semantic search unavailable. Showing budget/location/bedroom matches sorted by price."
