def score_lead(analysis):
    intent = {"buy": 35, "explore": 10, "unknown": 0}[analysis.intent]
    days = analysis.timeline_days
    urgency = 0 if days is None else 30 if days <= 30 else 20 if days <= 90 else 10 if days <= 180 else 0
    finance = {"ready": 25, "pending": 10, "unknown": 0}[analysis.financing]
    clarity = 10 if analysis.requirements else 0
    reasons = {
        "Purchase intent": intent,
        "Buying timeline": urgency,
        "Financing readiness": finance,
        "Stated requirements": clarity,
    }
    score = sum(reasons.values())
    return {"score": score, "priority": "Hot" if score >= 70 else "Warm" if score >= 40 else "Cold", "reasons": reasons}
