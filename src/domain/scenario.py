"""Pydantic Domain Models and Validation for FinEval Scenarios."""

from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

CategoryType = Literal[
    "Standard",
    "Ambiguous",
    "Edge Case",
    "Multi-turn",
    "Contradictory",
    "Hallucination Trap",
    "Adversarial",
    "Policy / Escalation Sensitive",
]

DomainType = Literal["Payments", "Lending", "Insurance", "Investments"]
DifficultyType = Literal["easy", "medium", "hard"]
SeverityType = Literal["critical", "high", "medium", "low"]
ConversationType = Literal["single_turn", "multi_turn"]


class ConversationTurn(BaseModel):
    turn_index: int = Field(..., ge=0)
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)


class ScenarioSchema(BaseModel):
    scenario_id: str = Field(..., min_length=3)
    domain: DomainType
    category: CategoryType
    subcategory: str = Field(..., min_length=2)
    difficulty: DifficultyType
    language_style: str = Field(..., min_length=2)
    conversation_type: ConversationType
    turns: List[ConversationTurn] = Field(default_factory=list)
    user_input: str = Field(..., min_length=2)
    context: str = Field(..., min_length=2)
    expected_action: str = Field(..., min_length=2)
    expected_facts: List[str] = Field(default_factory=list)
    allowed_claims: List[str] = Field(default_factory=list)
    prohibited_claims: List[str] = Field(default_factory=list)
    must_include: List[str] = Field(default_factory=list)
    must_not_include: List[str] = Field(default_factory=list)
    severity_if_failed: SeverityType
    tags: List[str] = Field(default_factory=list)
    gold_rationale: str = Field(..., min_length=5)

    @field_validator("turns", mode="before")
    @classmethod
    def ensure_turns(cls, v, values):
        if isinstance(v, list) and len(v) == 0:
            # Auto-wrap single-turn user_input if turns is empty
            pass
        return v
