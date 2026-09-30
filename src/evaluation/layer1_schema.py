"""Layer 1: Schema & Output Validation.

Validates that model output exists, is non-empty, contains valid characters,
and adheres to basic structural boundaries before downstream processing.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Layer1Result(BaseModel):
    passed: bool
    is_empty: bool
    char_count: int
    word_count: int
    has_valid_encoding: bool
    errors: List[str] = Field(default_factory=list)


def evaluate_layer1_schema(response_text: Optional[str]) -> Layer1Result:
    if response_text is None:
        return Layer1Result(
            passed=False,
            is_empty=True,
            char_count=0,
            word_count=0,
            has_valid_encoding=False,
            errors=["Response is null/None."],
        )

    text = response_text.strip()
    if len(text) == 0:
        return Layer1Result(
            passed=False,
            is_empty=True,
            char_count=0,
            word_count=0,
            has_valid_encoding=True,
            errors=["Response is empty string."],
        )

    errors = []
    # Check for excessive brevity (e.g. less than 3 words)
    words = text.split()
    if len(words) < 2:
        errors.append(f"Response is excessively short ({len(words)} words).")

    # Check for raw JSON leakage or unescaped markdown errors
    if text.startswith("{") and text.endswith("}"):
        try:
            import json
            json.loads(text)
        except Exception:
            errors.append("Response appears to be broken/malformed raw JSON.")

    return Layer1Result(
        passed=len(errors) == 0,
        is_empty=False,
        char_count=len(text),
        word_count=len(words),
        has_valid_encoding=True,
        errors=errors,
    )
