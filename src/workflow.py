from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from src.ai import generate
from src.models import Analysis, Lead
from src.prompts import ANALYZE
from src.scoring import score_lead


class State(TypedDict, total=False):
    lead: Lead
    analysis: Analysis
    attempts: int
    error: str
    retryable: bool
    result: dict


def understand(state):
    try:
        text = generate(state["lead"].model_dump_json(), ANALYZE, Analysis)
        analysis = Analysis.model_validate_json(text).check_evidence(state["lead"])
        return {"analysis": analysis, "attempts": state["attempts"] + 1, "error": ""}
    except (ValidationError, ValueError):
        return {"error": "Gemini returned invalid analysis. Please try again.", "retryable": True, "attempts": state["attempts"] + 1}
    except RuntimeError as exc:
        return {"error": str(exc), "retryable": False, "attempts": state["attempts"] + 1}


def route(state):
    if not state.get("error"):
        return "score"
    return "understand" if state["retryable"] and state["attempts"] < 2 else END


def score(state):
    return {"result": {**state["analysis"].model_dump(), **score_lead(state["analysis"])}}


def build_workflow():
    graph = StateGraph(State)
    graph.add_node("understand", understand)
    graph.add_node("score", score)
    graph.add_edge(START, "understand")
    graph.add_conditional_edges("understand", route, {"understand": "understand", "score": "score", END: END})
    graph.add_edge("score", END)
    return graph.compile()


workflow = build_workflow()


def analyze_lead(lead):
    state = workflow.invoke({"lead": lead, "attempts": 0})
    if state.get("error"):
        raise RuntimeError(state["error"])
    return state["result"]
