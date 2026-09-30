"""SQLAlchemy Database Models and Relational Architecture for FinEval.

Models:
- PromptVersion
- KnowledgeBaseEntry
- Scenario
- BenchmarkRun
- ModelResponse
- Evaluation
- FailureEvent
- TranscriptTurn
- ChangeLedgerEntry
"""

import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.types import TypeDecorator


# JSON fallback for SQLite vs PostgreSQL JSONB
class SafeJSON(TypeDecorator):
    """Platform-independent JSON type that uses JSONB on PostgreSQL and Text on SQLite."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


class Base(DeclarativeBase):
    pass


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    version: str = Column(String(32), primary_key=True)  # e.g., "V1", "V2", "V3", "V4"
    name: str = Column(String(128), nullable=False)
    purpose: str = Column(Text, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    prompt_text: str = Column(Text, nullable=False)
    change_type: str = Column(String(64), nullable=False)
    hypothesis: str = Column(Text, nullable=False)
    target_failure_types: Any = Column(SafeJSON, nullable=False, default=list)

    # Relationships
    model_responses = relationship("ModelResponse", back_populates="prompt_rel")
    benchmark_runs = relationship("BenchmarkRun", back_populates="prompt_rel")
    change_ledgers = relationship("ChangeLedgerEntry", back_populates="prompt_rel")


class KnowledgeBaseEntry(Base):
    __tablename__ = "knowledge_base"

    knowledge_id: str = Column(String(64), primary_key=True)
    domain: str = Column(String(64), nullable=False, index=True)
    topic: str = Column(String(128), nullable=False)
    fact: str = Column(Text, nullable=False)
    allowed_claims: Any = Column(SafeJSON, nullable=False, default=list)
    prohibited_claims: Any = Column(SafeJSON, nullable=False, default=list)
    source_label: str = Column(String(128), default="Synthetic Knowledge Base", nullable=False)


class Scenario(Base):
    __tablename__ = "scenarios"

    scenario_id: str = Column(String(64), primary_key=True)
    domain: str = Column(String(64), nullable=False, index=True)
    category: str = Column(String(64), nullable=False, index=True)
    subcategory: str = Column(String(64), nullable=False)
    difficulty: str = Column(String(32), nullable=False)  # easy, medium, hard
    language_style: str = Column(String(64), nullable=False)  # formal, colloquial, fragmented
    conversation_type: str = Column(String(32), nullable=False)  # single_turn, multi_turn
    turns: Any = Column(SafeJSON, nullable=False, default=list)
    user_input: str = Column(Text, nullable=False)
    context: str = Column(Text, nullable=False)
    expected_action: str = Column(String(128), nullable=False)
    expected_facts: Any = Column(SafeJSON, nullable=False, default=list)
    allowed_claims: Any = Column(SafeJSON, nullable=False, default=list)
    prohibited_claims: Any = Column(SafeJSON, nullable=False, default=list)
    must_include: Any = Column(SafeJSON, nullable=False, default=list)
    must_not_include: Any = Column(SafeJSON, nullable=False, default=list)
    severity_if_failed: str = Column(String(32), nullable=False, default="medium")  # critical, high, medium, low
    tags: Any = Column(SafeJSON, nullable=False, default=list)
    gold_rationale: str = Column(Text, nullable=False)

    # Relationships
    model_responses = relationship("ModelResponse", back_populates="scenario_rel")
    evaluations = relationship("Evaluation", back_populates="scenario_rel")
    failure_events = relationship("FailureEvent", back_populates="scenario_rel")


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    benchmark_run_id: str = Column(String(64), primary_key=True)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    prompt_version: str = Column(String(32), ForeignKey("prompt_versions.version"), nullable=False, index=True)
    model_name: str = Column(String(64), nullable=False)
    evaluation_mode: str = Column(String(32), nullable=False)  # smoke, core, full
    dataset_version: str = Column(String(32), default="v1.0", nullable=False)
    configuration_version: str = Column(String(32), default="1.0", nullable=False)
    total_scenarios: int = Column(Integer, default=0, nullable=False)
    passed_scenarios: int = Column(Integer, default=0, nullable=False)
    failed_scenarios: int = Column(Integer, default=0, nullable=False)
    average_score: float = Column(Float, default=0.0, nullable=False)
    duration_seconds: float = Column(Float, default=0.0, nullable=False)

    # Relationships
    prompt_rel = relationship("PromptVersion", back_populates="benchmark_runs")
    model_responses = relationship("ModelResponse", back_populates="run_rel")
    evaluations = relationship("Evaluation", back_populates="run_rel")
    failure_events = relationship("FailureEvent", back_populates="run_rel")


class ModelResponse(Base):
    __tablename__ = "model_responses"

    response_id: str = Column(String(64), primary_key=True)
    benchmark_run_id: str = Column(String(64), ForeignKey("benchmark_runs.benchmark_run_id"), nullable=False, index=True)
    scenario_id: str = Column(String(64), ForeignKey("scenarios.scenario_id"), nullable=False, index=True)
    prompt_version: str = Column(String(32), ForeignKey("prompt_versions.version"), nullable=False, index=True)
    model_name: str = Column(String(64), nullable=False)
    full_prompt: str = Column(Text, nullable=False)
    raw_response: str = Column(Text, nullable=False)
    latency_ms: float = Column(Float, default=0.0, nullable=False)
    token_usage: Any = Column(SafeJSON, nullable=True)
    status: str = Column(String(32), default="success", nullable=False)  # success, error, timeout
    error_message: Optional[str] = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    run_rel = relationship("BenchmarkRun", back_populates="model_responses")
    scenario_rel = relationship("Scenario", back_populates="model_responses")
    prompt_rel = relationship("PromptVersion", back_populates="model_responses")
    evaluation = relationship("Evaluation", back_populates="response_rel", uselist=False)
    transcripts = relationship("TranscriptTurn", back_populates="response_rel")


class Evaluation(Base):
    __tablename__ = "evaluations"

    evaluation_id: str = Column(String(64), primary_key=True)
    benchmark_run_id: str = Column(String(64), ForeignKey("benchmark_runs.benchmark_run_id"), nullable=False, index=True)
    scenario_id: str = Column(String(64), ForeignKey("scenarios.scenario_id"), nullable=False, index=True)
    response_id: str = Column(String(64), ForeignKey("model_responses.response_id"), nullable=False, index=True)
    prompt_version: str = Column(String(32), nullable=False, index=True)

    # Dimension Scores (0-5 scale)
    accuracy_score: float = Column(Float, nullable=False)
    groundedness_score: float = Column(Float, nullable=False)
    instruction_following_score: float = Column(Float, nullable=False)
    relevance_score: float = Column(Float, nullable=False)
    consistency_score: float = Column(Float, nullable=False)
    safety_score: float = Column(Float, nullable=False)
    clarity_score: float = Column(Float, nullable=False)

    # Overall Weighted Score (0 - 100%)
    overall_score: float = Column(Float, nullable=False)
    passed: bool = Column(Boolean, nullable=False)
    is_critical_fail: bool = Column(Boolean, default=False, nullable=False)

    # Layer evaluations
    layer_results: Any = Column(SafeJSON, nullable=False, default=dict)
    evaluator_mode: str = Column(String(32), default="deterministic_and_judge", nullable=False)

    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    run_rel = relationship("BenchmarkRun", back_populates="evaluations")
    scenario_rel = relationship("Scenario", back_populates="evaluations")
    response_rel = relationship("ModelResponse", back_populates="evaluation")
    failures = relationship("FailureEvent", back_populates="eval_rel")


class FailureEvent(Base):
    __tablename__ = "failure_events"

    failure_id: str = Column(String(64), primary_key=True)
    scenario_id: str = Column(String(64), ForeignKey("scenarios.scenario_id"), nullable=False, index=True)
    benchmark_run_id: str = Column(String(64), ForeignKey("benchmark_runs.benchmark_run_id"), nullable=False, index=True)
    evaluation_id: str = Column(String(64), ForeignKey("evaluations.evaluation_id"), nullable=False, index=True)
    prompt_version: str = Column(String(32), nullable=False, index=True)
    failure_type: str = Column(String(32), nullable=False, index=True)  # F1..F8
    severity: str = Column(String(32), nullable=False, index=True)  # critical, high, medium, low
    evidence: str = Column(Text, nullable=False)
    diagnosis: str = Column(Text, nullable=False)
    recommended_fix: str = Column(Text, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    eval_rel = relationship("Evaluation", back_populates="failures")
    scenario_rel = relationship("Scenario", back_populates="failure_events")
    run_rel = relationship("BenchmarkRun", back_populates="failure_events")


class TranscriptTurn(Base):
    __tablename__ = "transcripts"

    transcript_id: str = Column(String(64), primary_key=True)
    benchmark_run_id: str = Column(String(64), nullable=False, index=True)
    response_id: str = Column(String(64), ForeignKey("model_responses.response_id"), nullable=False, index=True)
    scenario_id: str = Column(String(64), nullable=False, index=True)
    turn_index: int = Column(Integer, nullable=False)
    role: str = Column(String(32), nullable=False)  # user, assistant, system
    content: str = Column(Text, nullable=False)
    has_failure: bool = Column(Boolean, default=False, nullable=False)
    failure_type: Optional[str] = Column(String(32), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    response_rel = relationship("ModelResponse", back_populates="transcripts")


class ChangeLedgerEntry(Base):
    __tablename__ = "change_ledger"

    ledger_id: str = Column(String(64), primary_key=True)
    version: str = Column(String(32), ForeignKey("prompt_versions.version"), nullable=False, index=True)
    change_description: str = Column(Text, nullable=False)
    hypothesis: str = Column(Text, nullable=False)
    target_failures: Any = Column(SafeJSON, nullable=False, default=list)
    observed_result: str = Column(Text, nullable=False)
    regression_status: str = Column(String(64), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    prompt_rel = relationship("PromptVersion", back_populates="change_ledgers")


# Indexes for analytical performance
Index("idx_eval_score", Evaluation.overall_score)
Index("idx_failure_type_sev", FailureEvent.failure_type, FailureEvent.severity)
Index("idx_run_prompt", BenchmarkRun.prompt_version, BenchmarkRun.timestamp)
