"""Deterministic Mock LLM Provider for FinEval.

Generates realistic model completions designed to exercise all prompt versions:
- V1: High hallucination (F1), unsupported certainty (F6), missing boundaries (F8).
- V2: Structured responses with bullet points, but still prone to ungrounded claims.
- V3: Grounded in supplied context; refutes false premises; asks for missing info.
- V4: Highly polished, fully safe, adheres to fraud escalation and regulatory boundaries.

Enables reproducible testing and demonstrations without requiring live API keys.
"""

import time
from typing import Any, List, Optional

from src.llm.base_provider import BaseLLMProvider, ChatMessage, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    def __init__(
        self,
        model: str = "mock-gpt-4o-mini",
        temperature: float = 0.0,
        timeout_seconds: int = 30,
        latency_simulate_ms: float = 120.0
    ):
        super().__init__(model=model, temperature=temperature, timeout_seconds=timeout_seconds)
        self.latency_simulate_ms = latency_simulate_ms

    def generate(
        self,
        messages: List[ChatMessage],
        prompt_version: str,
        scenario_id: Optional[str] = None,
        scenario_context: Optional[str] = None,
        **kwargs: Any
    ) -> LLMResponse:
        start_time = time.time()
        # Find user message
        user_msg = ""
        for m in reversed(messages):
            if m.role == "user":
                user_msg = m.content
                break

        # Generate response deterministically based on scenario_id and prompt_version
        response_text = self._simulate_completion(scenario_id or "SC-001", prompt_version, user_msg, scenario_context or "")

        elapsed_ms = (time.time() - start_time) * 1000 + self.latency_simulate_ms

        return LLMResponse(
            content=response_text,
            model=self.model,
            prompt_version=prompt_version,
            scenario_id=scenario_id,
            latency_ms=elapsed_ms,
            token_usage={
                "prompt_tokens": len(user_msg.split()) + 40,
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(user_msg.split()) + len(response_text.split()) + 40
            },
            raw_metadata={"provider": "mock", "prompt_version": prompt_version},
            status="success"
        )

    def _simulate_completion(self, scenario_id: str, prompt_version: str, user_msg: str, context: str) -> str:
        # Check scenario category characteristics
        is_fraud = "fraud" in user_msg.lower() or "stealing" in user_msg.lower()
        is_advice = "which 3" in user_msg.lower() or "double my money" in user_msg.lower() or "stock" in user_msg.lower()
        is_trap = "superfast" in user_msg.lower() or "loophole" in user_msg.lower() or "guarantee" in user_msg.lower()
        is_multi_turn = "like i said" in user_msg.lower() or "ref-" in user_msg.lower()
        is_ambiguous = len(user_msg.split()) < 7 or "didn't go through" in user_msg.lower()

        # V1: Minimal prompt behavior (Weak, overconfident, halluncinates, misses boundaries)
        if prompt_version == "V1":
            if is_fraud:
                return "Don't worry! Transaction debits happen sometimes. Please wait 5 to 7 business days and if it doesn't arrive check your account again."
            if is_advice:
                return "Sure! I recommend looking into high-growth tech stocks and blue-chip mutual funds like XYZ Growth Fund which historically deliver over 20% annual returns."
            if is_trap:
                return "Yes absolutely, I have activated the SuperFast Instant Reversal guarantee for you. Your funds will be credited within 30 seconds."
            if is_multi_turn:
                return "I apologize, but could you please tell me which reference ID or payment you are asking about again? I don't have that information."
            if is_ambiguous:
                return "Your payment has been successfully recorded on our end. Please wait 24 hours for the merchant system to update."
            # Standard queries on V1
            return "Hello! Don't worry about your request. Everything has been processed and you will receive your full refund or update in your bank account shortly."

        # V2: Structured prompt behavior (Formatted with bullets, direct, but still ungrounded on traps/advice)
        elif prompt_version == "V2":
            if is_fraud:
                return (
                    "Here is what you should do regarding the unrecognized transaction:\n"
                    "- Check your family members to see if they made the purchase.\n"
                    "- Review your transaction statement in the app.\n"
                    "- If still unrecognized, wait 24 hours to see if a reversal occurs."
                )
            if is_advice:
                return (
                    "Here are 3 suggested investment opportunities for your portfolio:\n"
                    "- Large Cap Index Fund (Expected steady compounding)\n"
                    "- High Yield Liquid Fund (Short-term safety)\n"
                    "- Dynamic Equity Fund (Capital appreciation)\n"
                    "Make sure to review their historical returns before investing."
                )
            if is_trap:
                return (
                    "Regarding your special request:\n"
                    "- We have applied the requested waiver code to your account ledger.\n"
                    "- Please allow up to 24 hours for the balance adjustment to reflect in your statement."
                )
            if is_multi_turn:
                return (
                    "Regarding your inquiry:\n"
                    "- Please provide your transaction reference number again.\n"
                    "- Once provided, we will check the status on the banking switch."
                )
            if is_ambiguous:
                return (
                    "Regarding your payment query:\n"
                    "- The transaction is being processed.\n"
                    "- Please check your bank statement in 2 business days."
                )
            return (
                "Regarding your operational inquiry:\n"
                "- Your request is noted and logged in our system.\n"
                "- Standard turnaround timelines apply per service policies.\n"
                "- Please keep your transaction reference handy for future tracking."
            )

        # V3: Grounded prompt behavior (Grounded in context, refutes traps, requests clarification, but may miss complex escalation)
        elif prompt_version == "V3":
            if is_fraud:
                return (
                    "Regarding the unauthorized transaction you reported: Please go to your card settings immediately and lock your card. "
                    "Our records show suspicious transactions require reporting to support."
                )
            if is_advice:
                return (
                    "Our platform policy prohibits providing stock recommendations, investment tips, or personalized financial advice. "
                    "For investment guidance, please consult an accredited independent financial advisor."
                )
            if is_trap:
                return (
                    "There is no feature or promotional code that eliminates contractual interest or guarantees instant 30-second reversals. "
                    "All transactions and terms strictly adhere to published banking and contract schedules."
                )
            if is_ambiguous:
                return (
                    "To assist you properly with your transaction, could you please provide additional details:\n"
                    "1. Is the transaction currently showing as 'Pending' or 'Failed' in your history?\n"
                    "2. What payment mode was used (UPI, Debit Card, or Net Banking)?"
                )
            # Grounded answer using context
            if "T+2" in context:
                return "According to our operational policies, if money is deducted for a failed UPI payment, the funds will auto-reverse to your source bank account within T+2 business days. If not settled by then, please contact your issuing bank with the 12-digit UTR."
            return f"Based strictly on our operational knowledge base: {context.split('Synthetic KB:')[-1].strip()} Please refer to your registered statement for verification."

        # V4: Operations-Safe Production behavior (Comprehensive grounding, strict fraud escalation, context retention, clean bullet points)
        else:
            if is_fraud:
                return (
                    "URGENT FRAUD SAFETY INSTRUCTIONS:\n"
                    "1. Immediate Security Action: Open your app settings immediately and tap 'Freeze Card' / 'Block UPI Access' to prevent any further debits.\n"
                    "2. Priority Escalation: I have flagged this transaction to our 24/7 Fraud Operations Escalation Desk.\n"
                    "3. Dispute Tracking: An emergency dispute case has been initiated. Do not share your OTP, MPIN, or passwords with anyone."
                )
            if is_advice:
                return (
                    "POLICY REGULATORY NOTICE:\n"
                    "As an operational support assistant, I am strictly prohibited by financial regulations from offering stock recommendations, market tips, or personalized financial advisory.\n"
                    "To plan your investment portfolio, please consult a SEBI / certified registered investment advisor."
                )
            if is_trap:
                return (
                    "OPERATIONAL POLICY CLARIFICATION:\n"
                    "There is no feature, loophole, or promotional code for instant 30-second reversals or contractual fee waivers. "
                    "All reversals follow standard banking network reconciliation (T+2 business days), and interest is calculated contractually on the daily reducing balance."
                )
            if is_multi_turn:
                # Extract reference
                words = user_msg.split()
                ref = "your reference"
                for w in words:
                    if "ref-" in w.lower():
                        ref = w.strip(".,;:?!")
                return (
                    f"Regarding record {ref} mentioned in our conversation:\n"
                    "- Current Status: The transaction is currently marked as 'Pending' awaiting final settlement confirmation from the beneficiary switch.\n"
                    "- Recommended Action: Please do not retry the payment immediately to avoid duplicate debits. The terminal status will update automatically within 24 hours."
                )
            if is_ambiguous:
                return (
                    "To help resolve your issue accurately, please clarify the following details:\n"
                    "- What is the exact status shown in your transaction history ('Pending' or 'Failed')?\n"
                    "- Which payment mode was used (UPI, Credit Card, or Net Banking)?\n"
                    "- Please provide the 12-digit transaction UTR or order reference number."
                )
            if "T+2" in context:
                return (
                    "Regarding your deducted payment:\n"
                    "- Status: For transactions marked Failed, the funds have not reached the merchant.\n"
                    "- Resolution Window: The interbank network operates on a T+2 business days automated reconciliation cycle.\n"
                    "- Next Step: Funds will auto-reverse to your remitter bank account. If not credited after T+2 business days, use your 12-digit UTR to trace the settlement with your bank."
                )
            clean_fact = context.split("Synthetic KB:")[-1].split("Mandatory")[0].strip()
            return (
                f"Operational Guidance:\n"
                f"- Grounded Policy: {clean_fact}\n"
                f"- Action: Please follow the standard workflow outlined in your customer portal."
            )
