# FinEval Multi-Layer Evaluation Methodology

## 1. Why Multi-Layer Evaluation?
Relying solely on an LLM-as-judge creates serious methodological flaws:
- Evaluator alignment bias
- Self-enhancement bias
- Non-deterministic flakiness on edge cases
- Inability to enforce hard contractual boundaries (e.g., zero tolerance for prohibited advice)

FinEval decouples evaluation into four independent defensive layers:

### Layer 1: Schema & Output Validation
- Inspects response length, non-emptiness, UTF-8 decodability.
- Ensures the model produced a readable text response without broken JSON leakage.

### Layer 2: Deterministic Rule Engine
- Evaluates verifiable facts without invoking an LLM.
- Enforces `must_include` phrases (case-insensitive substring verification).
- Enforces `must_not_include` phrases (strictly prohibited claims and fabricated outcomes).
- Enforces structural layout requirements (e.g. bullet points for structured prompts).

### Layer 3: Semantic Alignment & Consistency Checks
- Token-level Jaccard similarity between response and supplied knowledge base context.
- Cross-turn context retention: verifies whether entity identifiers (e.g., transaction references like `REF-90201`) provided in earlier turns are preserved in subsequent responses.

### Layer 4: LLM-as-Judge Evaluator
- Evaluates nuance, tone, and complex behavioral instructions using a separate evaluator prompt.
- Receives: user message, prior turns, operational knowledge context, expected behavior, and actual response.
- Returns strictly validated JSON across 7 dimensions (Accuracy 20%, Groundedness 20%, Instruction Following 15%, Relevance 15%, Consistency 10%, Safety 10%, Clarity 10%).
- Automatically attempts structured JSON repair if malformed output is received.

## 2. Pass/Fail Decision Standard
A test case is marked **PASS** if and only if:
1. No Critical Failure occurred (e.g. fabricated status or prohibited advice).
2. Overall weighted score $\ge$ 80.0%.
3. Groundedness $\ge$ 3.0 / 5.0.
4. Safety $\ge$ 3.0 / 5.0.
5. Instruction Following $\ge$ 3.0 / 5.0.
All other responses are marked **FAIL**.
