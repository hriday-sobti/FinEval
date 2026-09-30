"""Prompt Version Manager and Seed Metadata for FinEval."""

import csv
import json

from src.utils.config import DATA_DIR, PROMPTS_DIR

PROMPT_METADATA = [
    {
        "version": "V1",
        "name": "Minimal Baseline",
        "purpose": "Establish weak baseline with under-specified prompt instructions.",
        "created_at": "2026-09-01 09:00:00",
        "prompt_file": "v1_minimal.txt",
        "change_type": "baseline_creation",
        "hypothesis": "Under-specified baseline will exhibit high hallucination (F1), unsupported certainty (F6), and weak boundary adherence.",
        "target_failure_types": ["F1", "F2", "F6", "F8"],
    },
    {
        "version": "V2",
        "name": "Structured Output",
        "purpose": "Introduce structured response guidance, concise direct answers, and bullet points.",
        "created_at": "2026-09-05 11:30:00",
        "prompt_file": "v2_structured.txt",
        "change_type": "structure_refinement",
        "hypothesis": "Formatting and clarity instructions will improve relevance and reduce F7, but unsupported claims (F1/F6) will persist without strict grounding constraints.",
        "target_failure_types": ["F7", "F5"],
    },
    {
        "version": "V3",
        "name": "Grounded Knowledge",
        "purpose": "Introduce strict grounding constraints, distinguishing known vs unknown facts, and requiring clarification over guessing.",
        "created_at": "2026-09-12 14:15:00",
        "prompt_file": "v3_grounded.txt",
        "change_type": "grounding_rules",
        "hypothesis": "Explicit grounding constraints and requirement to acknowledge missing data will sharply reduce F1 (hallucination) and F6 (unsupported certainty).",
        "target_failure_types": ["F1", "F6"],
    },
    {
        "version": "V4",
        "name": "Operations-Safe Production",
        "purpose": "Comprehensive operational safety: anti-hallucination, mandatory fraud escalation, conversational context retention, and strict financial advice refusal.",
        "created_at": "2026-09-20 16:45:00",
        "prompt_file": "v4_operations_safe.txt",
        "change_type": "operational_safety_hardening",
        "hypothesis": "Comprehensive operational boundaries will minimize critical failures (F8 routing/escalation, F1 hallucination, F4 context loss), achieving enterprise-grade pass rates.",
        "target_failure_types": ["F1", "F4", "F8", "F6", "F2"],
    },
]


def load_prompt_text(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def generate_prompt_versions_csv() -> None:
    csv_path = DATA_DIR / "prompt_versions.csv"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "version",
        "name",
        "purpose",
        "created_at",
        "prompt_text",
        "change_type",
        "hypothesis",
        "target_failure_types",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in PROMPT_METADATA:
            text = load_prompt_text(p["prompt_file"])
            writer.writerow({
                "version": p["version"],
                "name": p["name"],
                "purpose": p["purpose"],
                "created_at": p["created_at"],
                "prompt_text": text,
                "change_type": p["change_type"],
                "hypothesis": p["hypothesis"],
                "target_failure_types": json.dumps(p["target_failure_types"]),
            })
    print(f"Generated prompt versions CSV at {csv_path}")


if __name__ == "__main__":
    generate_prompt_versions_csv()
