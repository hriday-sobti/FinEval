"""Layer 3: Semantic Alignment and Contextual Consistency Checks.

Evaluates semantic overlap, topic grounding, contextual relevance,
and multi-turn reference retention using token Jaccard and n-gram overlap.
"""

import re
from typing import List, Set

from pydantic import BaseModel, Field

from src.domain.scenario import ScenarioSchema


class Layer3Result(BaseModel):
    passed: bool
    relevance_score: float  # 0 to 5
    groundedness_score: float  # 0 to 5
    consistency_score: float  # 0 to 5
    context_loss_detected: bool = False
    evidence: List[str] = Field(default_factory=list)


def _tokenize(text: str) -> Set[str]:
    # Extract lowercased alphabetic/numeric tokens, filtering standard stopwords
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
        "is", "was", "are", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "can", "could", "will", "would", "should", "of", "about",
        "my", "your", "our", "their", "it", "this", "that", "these", "those", "i", "you"
    }
    words = re.findall(r"\b[a-zA-Z0-9_\-]+\b", text.lower())
    return {w for w in words if len(w) > 2 and w not in stopwords}


def evaluate_layer3_semantic(
    response_text: str,
    scenario: ScenarioSchema,
    prompt_version: str,
) -> Layer3Result:
    resp_tokens = _tokenize(response_text)
    user_tokens = _tokenize(scenario.user_input)
    context_tokens = _tokenize(scenario.context)

    # Multi-turn reference check
    context_loss = False
    evidence = []

    if scenario.conversation_type == "multi_turn" and len(scenario.turns) > 1:
        # Check if identifiers or key context terms from turn 0 exist in response
        prior_turn_tokens = _tokenize(scenario.turns[0].content)
        # Identify specific references like ref-*, id-*, or amounts
        ref_tokens = {t for t in prior_turn_tokens if any(prefix in t for prefix in ["ref", "id", "ln", "kb", "tx"])}
        if ref_tokens:
            has_ref = any(r in resp_tokens or r in response_text.lower() for r in ref_tokens)
            if not has_ref:
                context_loss = True
                evidence.append(f"Response failed to retain specific reference identifier: {list(ref_tokens)}")

    # 1. Relevance Score (User input token overlap)
    user_overlap = len(resp_tokens.intersection(user_tokens))
    user_union = len(resp_tokens.union(user_tokens)) if resp_tokens or user_tokens else 1
    jaccard_user = user_overlap / user_union if user_union > 0 else 0.0

    # Scale to 0-5
    # Even moderate overlap (0.15+) represents strong relevance in conversational Q&A
    relevance = min(5.0, max(1.0, jaccard_user * 12.0 + 1.5))
    if len(resp_tokens) < 5:
        relevance = 1.0

    # 2. Groundedness Score (Context token overlap)
    context_overlap = len(resp_tokens.intersection(context_tokens))
    context_union = len(resp_tokens.union(context_tokens)) if resp_tokens or context_tokens else 1
    jaccard_ctx = context_overlap / context_union if context_union > 0 else 0.0

    # Base groundedness
    groundedness = min(5.0, max(1.0, jaccard_ctx * 10.0 + 1.8))

    # Penalize if context specifies "Pending" but response says "Approved" or "Successful"
    if "pending" in scenario.context.lower():
        if "approved" in response_text.lower() or "successful" in response_text.lower() or "completed" in response_text.lower():
            groundedness = min(groundedness, 1.5)
            evidence.append("Response claims completed/approved status when context specifies pending.")

    # 3. Consistency Score
    consistency = 4.5
    if context_loss:
        consistency -= 2.0
    if "contradict" in scenario.tags:
        # If scenario is contradictory, check if response addressed both or explained ledger
        if not any(k in response_text.lower() for k in ["reconcil", "ledger", "status", "statement"]):
            consistency -= 1.5
            evidence.append("Failed to resolve contradictory status using reconciliation ledger.")

    passed = (relevance >= 2.5) and (groundedness >= 2.5) and (not context_loss)

    return Layer3Result(
        passed=passed,
        relevance_score=round(relevance, 2),
        groundedness_score=round(groundedness, 2),
        consistency_score=round(consistency, 2),
        context_loss_detected=context_loss,
        evidence=evidence,
    )
