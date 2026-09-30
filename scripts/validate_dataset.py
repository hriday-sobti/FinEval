"""Scenario Dataset Validator for FinEval.

Validates:
- Exactly 200 scenarios
- Category distribution matching specification
- No duplicate scenario IDs
- No null required fields
- Valid categories, domains, severities
- Valid JSON in turns, tags, and claims
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from src.domain.scenario import ScenarioSchema

EXPECTED_DISTRIBUTION = {
    "Standard": 50,
    "Ambiguous": 25,
    "Edge Case": 25,
    "Multi-turn": 25,
    "Contradictory": 20,
    "Hallucination Trap": 20,
    "Adversarial": 20,
    "Policy / Escalation Sensitive": 15,
}


def validate_scenario_csv(csv_path: Path) -> Tuple[bool, List[str], Dict[str, int]]:
    errors: List[str] = []
    category_counts: Dict[str, int] = Counter()
    seen_ids = set()

    if not csv_path.exists():
        return False, [f"File not found: {csv_path}"], {}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if len(rows) != 200:
        errors.append(f"Expected exactly 200 scenarios, found {len(rows)}.")

    for i, row in enumerate(rows, 1):
        s_id = (row.get("scenario_id") or "").strip()
        if not s_id:
            errors.append(f"Row {i}: Missing scenario_id")
            continue
        if s_id in seen_ids:
            errors.append(f"Row {i}: Duplicate scenario_id '{s_id}'")
        seen_ids.add(s_id)

        cat = (row.get("category") or "").strip()
        category_counts[cat] += 1

        # Check required fields
        for req in ["domain", "subcategory", "difficulty", "user_input", "context", "expected_action"]:
            if not (row.get(req) or "").strip():
                errors.append(f"Scenario {s_id}: Missing required field '{req}'")

        # Parse JSON fields
        for j_field in ["turns", "expected_facts", "allowed_claims", "prohibited_claims", "must_include", "must_not_include", "tags"]:
            val = row.get(j_field, "")
            try:
                parsed = json.loads(val) if val else []
                if not isinstance(parsed, list):
                    errors.append(f"Scenario {s_id}: Field '{j_field}' must be a JSON list.")
            except Exception as e:
                errors.append(f"Scenario {s_id}: Invalid JSON in '{j_field}': {e}")

        # Pydantic schema validation
        try:
            ScenarioSchema(
                scenario_id=s_id,
                domain=row.get("domain", ""),
                category=cat,
                subcategory=row.get("subcategory", ""),
                difficulty=row.get("difficulty", "medium"),
                language_style=row.get("language_style", "conversational"),
                conversation_type=row.get("conversation_type", "single_turn"),
                turns=json.loads(row.get("turns", "[]")),
                user_input=row.get("user_input", ""),
                context=row.get("context", ""),
                expected_action=row.get("expected_action", ""),
                expected_facts=json.loads(row.get("expected_facts", "[]")),
                allowed_claims=json.loads(row.get("allowed_claims", "[]")),
                prohibited_claims=json.loads(row.get("prohibited_claims", "[]")),
                must_include=json.loads(row.get("must_include", "[]")),
                must_not_include=json.loads(row.get("must_not_include", "[]")),
                severity_if_failed=row.get("severity_if_failed", "medium"),
                tags=json.loads(row.get("tags", "[]")),
                gold_rationale=row.get("gold_rationale", "Rationale"),
            )
        except Exception as e:
            errors.append(f"Scenario {s_id}: Pydantic validation failed: {e}")

    # Validate distribution
    for cat, exp_cnt in EXPECTED_DISTRIBUTION.items():
        actual_cnt = category_counts.get(cat, 0)
        if actual_cnt != exp_cnt:
            errors.append(f"Category '{cat}': expected {exp_cnt}, found {actual_cnt}")

    is_valid = len(errors) == 0
    return is_valid, errors, dict(category_counts)


if __name__ == "__main__":
    p = Path("data/scenarios.csv")
    valid, errs, counts = validate_scenario_csv(p)
    print(f"Validation status: {'PASSED' if valid else 'FAILED'}")
    print("Category breakdown:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    if errs:
        print("Errors:")
        for e in errs[:10]:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("All 200 scenarios are structurally valid and meet exact distribution!")
