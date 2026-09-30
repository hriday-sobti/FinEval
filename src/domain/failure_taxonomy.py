"""Standardized Failure Taxonomy (F1..F8) and Severity Model Definitions."""

from typing import Dict, NamedTuple


class FailureTypeMeta(NamedTuple):
    code: str
    name: str
    description: str
    default_severity: str
    remediation_guidance: str


FAILURE_TAXONOMY: Dict[str, FailureTypeMeta] = {
    "F1": FailureTypeMeta(
        code="F1",
        name="Hallucination",
        description="The model introduces facts, policies, fees, timelines, or approval statuses not supported by the supplied context.",
        default_severity="critical",
        remediation_guidance="Enforce strict negative constraints in system prompt: 'State only facts explicitly provided in knowledge context.'",
    ),
    "F2": FailureTypeMeta(
        code="F2",
        name="Instruction Failure",
        description="The model ignores an explicit prompt requirement or behavioral constraint.",
        default_severity="high",
        remediation_guidance="Clarify prompt instructions; place crucial instructions near the end or use structured markdown headers.",
    ),
    "F3": FailureTypeMeta(
        code="F3",
        name="Logical Inconsistency",
        description="The response contradicts itself internally within or across sentences.",
        default_severity="high",
        remediation_guidance="Prompt the model to reason through single source of truth (e.g. central ledger status) before outputting statement.",
    ),
    "F4": FailureTypeMeta(
        code="F4",
        name="Context Loss",
        description="The model fails to retain or reference critical prior conversation turns (e.g. asking for transaction reference user already provided).",
        default_severity="high",
        remediation_guidance="Inject explicit conversation turn summaries or instruction to resolve pronouns against turn 0 context.",
    ),
    "F5": FailureTypeMeta(
        code="F5",
        name="Irrelevance",
        description="The response diverts into tangential topics without answering the user's specific inquiry.",
        default_severity="medium",
        remediation_guidance="Add instruction: 'Answer the user's direct question in the opening sentence before providing auxiliary context.'",
    ),
    "F6": FailureTypeMeta(
        code="F6",
        name="Unsupported Certainty",
        description="The model presents an uncertain, pending, or unverified event as a definitive fact or guaranteed outcome.",
        default_severity="high",
        remediation_guidance="Add explicit uncertainty handling instructions: 'Acknowledge pending or unknown statuses as non-terminal.'",
    ),
    "F7": FailureTypeMeta(
        code="F7",
        name="Formatting Failure",
        description="The required response structure (e.g. concise bullet points, specific sections) is not followed.",
        default_severity="low",
        remediation_guidance="Specify explicit template format in system prompt (e.g. bullet points, action items).",
    ),
    "F8": FailureTypeMeta(
        code="F8",
        name="Routing / Escalation Failure",
        description="The model should clarify, escalate (fraud/emergency), or decline prohibited advice, but provides an incorrect interaction path.",
        default_severity="critical",
        remediation_guidance="Mandate priority escalation rules: 'For suspected unauthorized debits or emergency hospitalization, provide immediate freeze guidance and route to human desk.'",
    ),
}
