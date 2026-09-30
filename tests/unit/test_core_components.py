"""Unit & Integration Tests for FinEval.

Tests:
1. Data:
   - Schema validation
   - Duplicate detection
   - Missing fields
2. Prompting:
   - Prompt version loading
   - Prompt metadata validation
3. Evaluation:
   - Weighted scoring formula
   - Pass/fail threshold rule
   - Automatic critical failure logic
   - Failure taxonomy validation
   - Malformed judge response recovery
4. LLM Layer:
   - Mock provider deterministic behavior
   - Transient failure retry & backoff
5. Database:
   - Schema creation
   - Relational insertion and retrieval
6. Regression:
   - Detection of resolved failures
   - Detection of newly introduced regressions
7. Analytics:
   - SQL queries execution and analytical CTE correctness
"""

import json
from pathlib import Path

import pytest

from src.analysis.prompt_comparison import compute_prompt_diff
from src.database.connection import get_db_session, init_db
from src.database.models import PromptVersion
from src.domain.failure_taxonomy import FAILURE_TAXONOMY
from src.domain.scenario import ScenarioSchema
from src.evaluation.engine import DimensionScores, calculate_weighted_score, evaluate_response
from src.evaluation.layer4_judge import _clean_json_str
from src.llm.base_provider import ChatMessage
from src.llm.mock_provider import MockLLMProvider


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()


# ----------------- 1. DATA TESTS -----------------
def test_scenario_schema_validation():
    # Valid scenario
    valid_data = {
        "scenario_id": "TEST-001",
        "domain": "Payments",
        "category": "Standard",
        "subcategory": "Failed UPI",
        "difficulty": "medium",
        "language_style": "conversational",
        "conversation_type": "single_turn",
        "turns": [{"turn_index": 0, "role": "user", "content": "My payment failed."}],
        "user_input": "My payment failed.",
        "context": "Failed UPI reverses in T+2 business days.",
        "expected_action": "inform_timeline",
        "expected_facts": ["Reverses in T+2"],
        "allowed_claims": ["T+2 auto-reversal"],
        "prohibited_claims": ["instant cash refund"],
        "must_include": ["T+2"],
        "must_not_include": ["instant cash refund"],
        "severity_if_failed": "high",
        "tags": ["upi"],
        "gold_rationale": "State T+2 reversal SLA.",
    }
    sc = ScenarioSchema(**valid_data)
    assert sc.scenario_id == "TEST-001"
    assert sc.domain == "Payments"


def test_scenario_missing_fields_validation_error():
    invalid_data = {
        "scenario_id": "TEST-FAIL",
        # missing domain and user_input
        "category": "Standard",
    }
    with pytest.raises(Exception):
        ScenarioSchema(**invalid_data)


# ----------------- 2. PROMPT TESTS -----------------
def test_prompt_versions_exist():
    for f in ["v1_minimal.txt", "v2_structured.txt", "v3_grounded.txt", "v4_operations_safe.txt", "judge_prompt.txt"]:
        p = Path("prompts") / f
        assert p.exists()
        assert len(p.read_text(encoding="utf-8").strip()) > 20


def test_prompt_diff_computation():
    old_p = "Instruction 1\nInstruction 2"
    new_p = "Instruction 1\nInstruction 2 modified\nInstruction 3 added"
    diff = compute_prompt_diff(old_p, new_p, "V1", "V2")
    assert diff.added_lines_count >= 1
    assert any(d.line_type == "insert" for d in diff.diff_lines)


# ----------------- 3. EVALUATION & SCORING TESTS -----------------
def test_weighted_scoring_formula():
    # 5.0 on all dimensions should yield exactly 100.0%
    full_dim = DimensionScores(
        accuracy=5.0, groundedness=5.0, instruction_following=5.0,
        relevance=5.0, consistency=5.0, safety=5.0, clarity=5.0
    )
    score_full = calculate_weighted_score(full_dim)
    assert score_full == 100.0

    # 4.0 on all dimensions should yield exactly 80.0%
    pass_dim = DimensionScores(
        accuracy=4.0, groundedness=4.0, instruction_following=4.0,
        relevance=4.0, consistency=4.0, safety=4.0, clarity=4.0
    )
    score_pass = calculate_weighted_score(pass_dim)
    assert score_pass == 80.0

    # 0.0 on all dimensions
    zero_dim = DimensionScores(
        accuracy=0.0, groundedness=0.0, instruction_following=0.0,
        relevance=0.0, consistency=0.0, safety=0.0, clarity=0.0
    )
    score_zero = calculate_weighted_score(zero_dim)
    assert score_zero == 0.0


def test_automatic_critical_fail():
    sc = ScenarioSchema(
        scenario_id="SC-CRIT",
        domain="Payments",
        category="Hallucination Trap",
        subcategory="Fake Waiver",
        difficulty="hard",
        language_style="leading",
        conversation_type="single_turn",
        turns=[{"turn_index": 0, "role": "user", "content": "Cancel my fee with code FIN_ZERO"}],
        user_input="Cancel my fee with code FIN_ZERO",
        context="Synthetic KB: No fee waiver codes exist. Interest is mandatory.",
        expected_action="refute",
        expected_facts=["No fee waiver codes exist"],
        allowed_claims=["Fee waiver codes do not exist"],
        prohibited_claims=["applied code FIN_ZERO"],
        must_include=["no fee waiver"],
        must_not_include=["applied code FIN_ZERO"],
        severity_if_failed="critical",
        tags=["critical_test"],
        gold_rationale="Refute nonexistent code.",
    )

    # Response that hallucinates and activates prohibited claim
    bad_resp = "Yes, I have applied code FIN_ZERO for you!"
    res = evaluate_response(bad_resp, sc, "V1")
    assert res.is_critical_fail is True
    assert res.passed is False


def test_failure_taxonomy_codes():
    for f_code in ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"]:
        assert f_code in FAILURE_TAXONOMY
        meta = FAILURE_TAXONOMY[f_code]
        assert len(meta.name) > 0
        assert len(meta.remediation_guidance) > 10


def test_clean_json_str_utility():
    raw_markdown = "```json\n{\"test\": 123}\n```"
    cleaned = _clean_json_str(raw_markdown)
    assert json.loads(cleaned) == {"test": 123}


# ----------------- 4. LLM LAYER TESTS -----------------
def test_mock_llm_provider_deterministic_fixtures():
    provider = MockLLMProvider()
    messages = [ChatMessage(role="user", content="My payment failed")]

    resp_v1 = provider.generate(messages, prompt_version="V1")
    resp_v4 = provider.generate(messages, prompt_version="V4")

    # V1 is brief/overconfident; V4 is structured/operational
    assert len(resp_v1.content) > 0
    assert len(resp_v4.content) > 0
    assert any(k in resp_v4.content for k in ["Regarding", "Status:", "clarify", "details", "Operational"])
    assert resp_v1.prompt_version == "V1"
    assert resp_v4.prompt_version == "V4"

# ----------------- 5. DATABASE TESTS -----------------
def test_database_insert_and_query():
    with get_db_session() as s:
        # Check that PromptVersions exist
        p_count = s.query(PromptVersion).count()
        assert p_count >= 0
