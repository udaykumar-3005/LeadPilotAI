from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Lead(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    location: str = Field(min_length=2, max_length=100)
    requirement: str = Field(min_length=3, max_length=500)
    budget_lakh: float = Field(gt=0, le=100000)
    timeline: str = Field(min_length=2, max_length=200)
    message: str = Field(min_length=10, max_length=5000)


class Analysis(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    summary: str = Field(min_length=1, max_length=1000)
    intent: Literal["buy", "explore", "unknown"]
    intent_evidence: str
    requirements: list[str] = Field(max_length=10)
    objections: list[str] = Field(max_length=10)
    missing_information: list[str] = Field(max_length=10)
    timeline_days: int | None = Field(default=None, ge=0, le=3650)
    timeline_evidence: str = ""
    financing: Literal["ready", "pending", "unknown"]
    financing_evidence: str
    next_action: str = Field(min_length=1, max_length=1000)
    suggested_response: str = Field(min_length=1, max_length=2000)

    def check_evidence(self, lead):
        source = " ".join([lead.requirement, lead.timeline, lead.message]).casefold()
        for field in ("intent", "timeline", "financing"):
            evidence = getattr(self, f"{field}_evidence").strip().casefold()
            known = self.timeline_days is not None if field == "timeline" else getattr(self, field) != "unknown"
            if known and (not evidence or evidence not in source):
                raise ValueError(f"{field} needs an exact supporting quote from the lead")
        return self


class Followup(BaseModel):
    action: str = Field(min_length=3, max_length=500)
    due_date: str
    status: Literal["Pending", "Completed"] = "Pending"

    @field_validator("due_date")
    @classmethod
    def valid_date(cls, value):
        from datetime import date

        return date.fromisoformat(value).isoformat()
