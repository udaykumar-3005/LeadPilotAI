import json

from src.ai import generate
from src.prompts import CHAT
from src.rag import retrieve


def answer(record, question, history, use_properties=False):
    matches, note = retrieve(record["lead"], question) if use_properties else ([], "Property search not requested.")
    context = {
        "selected_lead": record["lead"],
        "analysis": record["analysis"],
        "followup": record.get("followup"),
        "catalogue": matches,
        "retrieval_note": note,
        "history": [{"role": m["role"], "content": m["content"]} for m in history[-10:]],
        "question": question,
    }
    return generate(json.dumps(context), CHAT), matches, note
