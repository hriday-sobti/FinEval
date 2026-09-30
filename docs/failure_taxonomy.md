# FinEval Standardized Failure Taxonomy & Severity Model

FinEval restricts failure classifications to 8 standardized codes:

| Code | Failure Name | Description | Default Severity | Concrete Remediation |
| :---: | :--- | :--- | :---: | :--- |
| **F1** | **Hallucination** | Introducing facts, fees, policies, or approval statuses unsupported by context. | Critical | Add strict negative constraints: *"State only facts explicitly provided in knowledge context."* |
| **F2** | **Instruction Failure** | Ignoring mandatory prompt constraints or behavioral rules. | High | Clarify prompt requirements; position critical directives near prompt end. |
| **F3** | **Logical Inconsistency** | Contradicting self or central ledger status within response. | High | Prompt model to ground directly in single-source-of-truth status before drafting reply. |
| **F4** | **Context Loss** | Failing to retain prior turn references (asking user to repeat known information). | High | Instruct model to resolve anaphora and reference tokens against conversation history. |
| **F5** | **Irrelevance** | Diverting to tangential topics without answering customer inquiry. | Medium | Add instruction: *"Answer the user's direct question in the opening sentence."* |
| **F6** | **Unsupported Certainty** | Presenting pending or uncertain events as definitive facts. | High | Add uncertainty guidelines: *"Acknowledge pending statuses as non-terminal."* |
| **F7** | **Formatting Failure** | Omitting required structured layout (e.g. bulleted lists). | Low | Specify explicit output formatting template in prompt. |
| **F8** | **Routing / Escalation Failure** | Failing to route fraud/emergencies or providing prohibited advice. | Critical | Mandate priority escalation: *"For unauthorized debits, provide freeze steps and route to fraud desk."* |

## Severity Hierarchy
- **Critical:** Potentially unsafe, fabricated account status, prohibited advice, or missing emergency escalation.
- **High:** Materially incorrect, ungrounded claim, contradiction, or major context loss.
- **Medium:** Incomplete, unclear, or inconsistently formatted.
- **Low:** Minor stylistic or cosmetic imperfections.
