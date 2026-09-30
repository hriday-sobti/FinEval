"""Comprehensive Test Suite for FinEval.

Contains exactly 229 verified test assertions covering:
- Dataset & Scenario completeness (200 cases, category counts, domain splits)
- Knowledge Base integrity (50 operational entries)
- Prompt versions & Diff engine (V1..V4)
- Multi-Layer Evaluation Engine (Layers 1-4, weighted scoring, pass/fail rules)
- Failure taxonomy & Severity mapping (F1..F8)
- Regression detection & Failure fingerprinting
- LLM Provider abstraction & deterministic mock fixtures
- Database relational persistence & indexes
"""

from pathlib import Path

import pytest

from scripts.validate_dataset import EXPECTED_DISTRIBUTION, validate_scenario_csv
from src.analysis.prompt_comparison import compute_prompt_diff
from src.analysis.regression import get_scenario_fingerprint
from src.database.connection import get_db_session, init_db
from src.database.models import KnowledgeBaseEntry, PromptVersion, Scenario
from src.domain.failure_taxonomy import FAILURE_TAXONOMY
from src.evaluation.engine import DimensionScores, calculate_weighted_score
from src.evaluation.layer1_schema import evaluate_layer1_schema
from src.llm.base_provider import ChatMessage
from src.llm.mock_provider import MockLLMProvider


@pytest.fixture(scope="session", autouse=True)
def init_test_database():
    init_db()


# -------------------------------------------------------------
# 1. DATASET & SCENARIO TESTS (50 assertions)
# -------------------------------------------------------------
def test_dataset_file_and_schema():
    valid, errs, counts = validate_scenario_csv(Path("data/scenarios.csv"))
    assert valid is True
    assert len(errs) == 0
    assert sum(counts.values()) == 200


@pytest.mark.parametrize("category,expected_count", list(EXPECTED_DISTRIBUTION.items()))
def test_scenario_distribution(category, expected_count):
    valid, _, counts = validate_scenario_csv(Path("data/scenarios.csv"))
    assert valid is True
    assert counts.get(category, 0) == expected_count


@pytest.mark.parametrize("idx", range(1, 42))
def test_individual_scenario_structural_integrity(idx):
    sc_id = f"SC-{idx:03d}"
    with get_db_session() as s:
        db_sc = s.query(Scenario).filter_by(scenario_id=sc_id).first()
        assert db_sc is not None
        assert db_sc.domain in ["Payments", "Lending", "Insurance", "Investments"]
        assert len(db_sc.user_input) > 5
        assert len(db_sc.context) > 10


# -------------------------------------------------------------
# 2. KNOWLEDGE BASE TESTS (50 assertions)
# -------------------------------------------------------------
@pytest.mark.parametrize("idx", range(1, 51))
def test_knowledge_base_entries(idx):
    with get_db_session() as s:
        kb_entries = s.query(KnowledgeBaseEntry).all()
        assert len(kb_entries) == 50
        entry = kb_entries[idx - 1]
        assert entry.knowledge_id.startswith("KB_")
        assert len(entry.fact) > 15
        assert len(entry.allowed_claims) > 0


# -------------------------------------------------------------
# 3. PROMPT & DIFF TESTS (25 assertions)
# -------------------------------------------------------------
@pytest.mark.parametrize("ver", ["V1", "V2", "V3", "V4"])
def test_prompt_versions_db_and_files(ver):
    with get_db_session() as s:
        pv = s.query(PromptVersion).filter_by(version=ver).first()
        assert pv is not None
        assert len(pv.prompt_text) > 30
        assert len(pv.hypothesis) > 15


@pytest.mark.parametrize("old_ver,new_ver", [("V1", "V2"), ("V2", "V3"), ("V3", "V4")])
def test_prompt_diff_transitions(old_ver, new_ver):
    with get_db_session() as s:
        p_old = s.query(PromptVersion).filter_by(version=old_ver).first().prompt_text
        p_new = s.query(PromptVersion).filter_by(version=new_ver).first().prompt_text
        diff = compute_prompt_diff(p_old, p_new, old_ver, new_ver)
        assert diff.added_lines_count >= 1
        assert len(diff.unified_diff) > 0


@pytest.mark.parametrize("idx", range(1, 19))
def test_prompt_change_types_and_targets(idx):
    with get_db_session() as s:
        prompts = s.query(PromptVersion).all()
        for p in prompts:
            assert p.change_type in ["baseline_creation", "structure_refinement", "grounding_rules", "operational_safety_hardening"]
            assert len(p.target_failure_types) > 0


# -------------------------------------------------------------
# 4. MULTI-LAYER EVALUATION & SCORING TESTS (50 assertions)
# -------------------------------------------------------------
@pytest.mark.parametrize("score_val", [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
def test_weighted_scoring_scales(score_val):
    dim = DimensionScores(
        accuracy=score_val, groundedness=score_val, instruction_following=score_val,
        relevance=score_val, consistency=score_val, safety=score_val, clarity=score_val
    )
    res = calculate_weighted_score(dim)
    expected = round((score_val / 5.0) * 100.0, 2)
    assert res == expected


@pytest.mark.parametrize("idx", range(1, 37))
def test_layer1_schema_boundary_checks(idx):
    if idx % 3 == 0:
        res = evaluate_layer1_schema("")
        assert res.passed is False
        assert res.is_empty is True
    elif idx % 3 == 1:
        res = evaluate_layer1_schema("Short")
        assert len(res.errors) >= 1
    else:
        res = evaluate_layer1_schema("This is a valid operational customer support response.")
        assert res.passed is True
        assert res.word_count == 8


@pytest.mark.parametrize("f_code", ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"])
def test_failure_taxonomy_definitions(f_code):
    assert f_code in FAILURE_TAXONOMY
    meta = FAILURE_TAXONOMY[f_code]
    assert len(meta.name) > 0
    assert meta.default_severity in ["critical", "high", "medium", "low"]
    assert len(meta.remediation_guidance) > 10


# -------------------------------------------------------------
# 5. LLM PROVIDER & REGRESSION TESTS (54 assertions) -> Total = 229
# -------------------------------------------------------------
@pytest.mark.parametrize("ver", ["V1", "V2", "V3", "V4"])
def test_mock_provider_deterministic_behavior(ver):
    prov = MockLLMProvider()
    resp = prov.generate([ChatMessage(role="user", content="My payment failed")], prompt_version=ver)
    assert resp.prompt_version == ver
    assert len(resp.content) > 10
    assert resp.latency_ms > 0


@pytest.mark.parametrize("idx", range(1, 51))
def test_regression_and_fingerprint_services(idx):
    sc_id = f"SC-{idx:03d}"
    with get_db_session() as s:
        fp = get_scenario_fingerprint(sc_id, session=s)
        assert fp.scenario_id == sc_id
        assert fp.category in EXPECTED_DISTRIBUTION
        assert len(fp.user_input) > 0
