"""Knowledge Base Generator for FinEval.

Generates exactly 50 synthetic, controlled operational facts across:
- Payments (15 facts)
- Lending (15 facts)
- Insurance (10 facts)
- Investments (10 facts)

Saves to data/knowledge_base.csv.
"""

import csv
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

KNOWLEDGE_ENTRIES = [
    # --- PAYMENTS (15) ---
    {
        "knowledge_id": "KB_PAY_001",
        "domain": "Payments",
        "topic": "Failed UPI Transaction Deduction",
        "fact": "If money is deducted for a UPI payment marked Failed, the banking network reconciliation window is T+2 business days. If not settled, funds auto-reverse to the remitter account.",
        "allowed_claims": ["Funds auto-reverse within T+2 business days", "Failed status means merchant has not received settlement", "Check bank statement after reconciliation window"],
        "prohibited_claims": ["Guarantee immediate cash refund within 5 minutes", "Confirm payment reached merchant when marked failed", "Request customer UPI PIN or OTP"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_002",
        "domain": "Payments",
        "topic": "Pending Transaction Settlement",
        "fact": "A pending payment is awaiting final confirmation from the beneficiary bank switch. It is neither confirmed successful nor irrevocably failed until switch reconciliation completes.",
        "allowed_claims": ["Pending means awaiting terminal switch status", "Do not retry immediate duplicate payment to avoid double debit", "Status updates automatically within 24 hours"],
        "prohibited_claims": ["State pending transaction has definitely succeeded", "State pending transaction has definitely failed", "Authorize manual balance override"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_003",
        "domain": "Payments",
        "topic": "Duplicate Payment Debit",
        "fact": "When duplicate debits occur for a single order reference, secondary debit references undergo automatic batch clearing within 3 to 5 banking days.",
        "allowed_claims": ["Duplicate charge enters automated clearing", "Secondary charge reverses to source account", "Track using 12-digit UTR"],
        "prohibited_claims": ["Claim duplicate debits cannot occur", "Manually release locked funds on demand", "Promise instant credit across different bank networks"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_004",
        "domain": "Payments",
        "topic": "UPI Autopay Mandate Revocation",
        "fact": "An active UPI autopay mandate must be cancelled at least 24 hours prior to the scheduled execution date to prevent subsequent debit.",
        "allowed_claims": ["Revoke mandate in app mandate settings", "Must cancel 24 hours prior to debit schedule", "Cancelled mandate generates confirmation reference"],
        "prohibited_claims": ["Guarantee refund for already executed scheduled mandate", "Mandates can be revoked retroactively after debit execution", "Request banking login password"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_005",
        "domain": "Payments",
        "topic": "Merchant Refund SLA",
        "fact": "Merchant refunds initiated via card or net banking credit within 5-7 working days depending on the acquiring bank route; UPI credits take 2-4 business days.",
        "allowed_claims": ["UPI refunds take 2-4 business days", "Card/Net banking refunds take 5-7 working days", "Refund ARN or RRN can be tracked with remitter bank"],
        "prohibited_claims": ["Promise instant wallet cash payout for merchant returns", "Alter merchant return policies", "Guarantee immediate Saturday/Sunday clearing"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_006",
        "domain": "Payments",
        "topic": "Incorrect UPI ID Transfer",
        "fact": "Transfers completed to a valid registered third-party UPI VPA cannot be reversed unilaterally by the platform; customer must initiate inter-bank dispute through the remitter bank branch.",
        "allowed_claims": ["Completed transfers to valid recipients cannot be cancelled by support", "Customer must file dispute with their issuing bank branch", "Platform provides UTR for dispute logging"],
        "prohibited_claims": ["Promise support will seize recipient bank funds", "Share recipient personal phone number or home address", "Guarantee 100% fund recovery"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_007",
        "domain": "Payments",
        "topic": "Daily UPI Transaction Limits",
        "fact": "The standard platform limit for synthetic peer-to-merchant UPI transactions is INR 1,00,000 per 24-hour cycle, subject to individual issuing bank caps.",
        "allowed_claims": ["Standard daily cap is 1,00,000 INR", "Individual bank caps may be lower", "Limit resets 24 hours from initial transaction window"],
        "prohibited_claims": ["Manually override bank-level NPCI clearing limits", "Promise unlimited instant UPI transfers", "Bypass regulatory KYC limits"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_008",
        "domain": "Payments",
        "topic": "International Card Payment Decline",
        "fact": "Cross-border payments decline if international usage is disabled at the card level or if synthetic foreign currency markup exceeds card limit.",
        "allowed_claims": ["Verify international card toggle in mobile app card controls", "Ensure adequate limit including synthetic FX markup", "Check OTP delivery for 3D Secure verification"],
        "prohibited_claims": ["Authorize foreign exchange bypassing RBI/regulatory rules", "Process card transactions without CVV/OTP", "Guarantee exchange rate freeze"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_009",
        "domain": "Payments",
        "topic": "QR Code Payment Timeout",
        "fact": "Dynamic QR codes expire after 7 minutes. Payments attempted after QR expiration generate immediate rejection or automated reversal.",
        "allowed_claims": ["Dynamic QR codes expire in 7 minutes", "Expired QR payments auto-reverse to bank account", "Customer should generate fresh QR code for retry"],
        "prohibited_claims": ["Accept funds against expired invoice", "Manually mark expired QR order as fulfilled", "Advise paying to personal VPA"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_010",
        "domain": "Payments",
        "topic": "Payment Gateway 504 Gateway Timeout",
        "fact": "A 504 timeout indicates server communication latency between payment aggregator and card network; debit confirmation requires webhook reconciliation.",
        "allowed_claims": ["Timeout indicates intermediary communication lag", "Wait 15 minutes before re-attempting transaction", "Status settles to Success or Reversal upon webhook receipt"],
        "prohibited_claims": ["Assume funds are lost permanently", "State payment failed without checking bank debit", "Instruct user to clear browser cache to recover money"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_011",
        "domain": "Payments",
        "topic": "Credit Card Bill Payment Settlement Window",
        "fact": "Payments to credit card bills via BBPS reflect in card issuer ledger within T+3 working days; payments made on due dates after 8 PM may register next business day.",
        "allowed_claims": ["BBPS credit card payments take up to T+3 working days", "Make payments before cut-off to avoid late fee risk", "Receipt reference number serves as proof of payment"],
        "prohibited_claims": ["Waive issuing bank late payment interest directly", "Promise zero-latency instant posting on third-party card networks", "Alter customer card due date"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_012",
        "domain": "Payments",
        "topic": "Suspected Fraudulent Debit Notification",
        "fact": "If customer reports an unrecognized debit transaction, the account card/UPI access must be frozen immediately and transferred to the Fraud Operations Escalation desk.",
        "allowed_claims": ["Direct customer to freeze card/block UPI in security settings", "Escalate case to Fraud Operations team immediately", "Log dispute ticket number for tracking"],
        "prohibited_claims": ["Dismiss customer fraud allegation as user error", "Delay block action while investigating details", "Ask customer to provide account password or MPIN"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_013",
        "domain": "Payments",
        "topic": "Cashback Credit Timeline",
        "fact": "Promotional cashback credits are processed within 72 hours of transaction settlement into synthetic rewards ledger, provided campaign criteria are met.",
        "allowed_claims": ["Eligible cashback posts within 72 hours", "Requires verified transaction settlement", "Subject to published campaign terms"],
        "prohibited_claims": ["Manually disburse cash bonus to external bank account", "Guarantee cashback if transaction was reversed or failed", "Alter campaign eligibility criteria"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_014",
        "domain": "Payments",
        "topic": "Wallet to Bank Account Transfer Fee",
        "fact": "Transferring balance from synthetic prepaid wallet to bank account incurs a 1.5% convenience fee for non-KYC upgraded accounts; 0% fee for full-KYC accounts.",
        "allowed_claims": ["Non-KYC transfers incur 1.5% fee", "Full-KYC accounts enjoy 0% transfer fee", "Complete video KYC to unlock zero fee"],
        "prohibited_claims": ["Waive fees without KYC completion", "Allow wallet cash withdrawal exceeding regulatory limit", "Process wallet transfer to third-party unnamed accounts without KYC"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_PAY_015",
        "domain": "Payments",
        "topic": "Virtual Payment Address (VPA) Change",
        "fact": "Users can link up to 3 custom VPAs per synthetic registered mobile number; existing transaction histories remain anchored to mobile customer ID.",
        "allowed_claims": ["Up to 3 VPAs permitted per profile", "Historical statements remain accessible under customer ID", "Previous VPA releases after 30 days dormancy"],
        "prohibited_claims": ["Transfer historical transaction records to another customer ID", "Delete audit logs of previous transactions", "Create anonymous unlinked VPAs"],
        "source_label": "Synthetic Knowledge Base"
    },

    # --- LENDING (15) ---
    {
        "knowledge_id": "KB_LOAN_001",
        "domain": "Lending",
        "topic": "EMI Due Date Modification",
        "fact": "EMI due dates are fixed upon loan contract execution and cannot be modified mid-tenure under synthetic standard lending terms.",
        "allowed_claims": ["EMI due dates are contractual and fixed", "Repayment schedule cannot be changed mid-tenure", "Advance prepayment is permitted without changing due date"],
        "prohibited_claims": ["Promise customer they can change EMI date to whenever they want", "Alter loan agreement terms verbally", "Guarantee zero penalty for delayed EMI payment"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_002",
        "domain": "Lending",
        "topic": "Missed EMI Payment Consequence",
        "fact": "A missed EMI incurs a late fee of INR 500 plus applicable taxes and is reported to synthetic credit rating bureaus after 30 days past due.",
        "allowed_claims": ["Late fee of INR 500 + taxes applies", "Bureau reporting occurs after 30 days delinquency", "Immediate repayment available via app repayment link"],
        "prohibited_claims": ["Promise credit bureau record will not be affected", "Waive contractual late fees unconditionally", "Offer informal unrecorded loan grace periods"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_003",
        "domain": "Lending",
        "topic": "Loan Preclosure Charges & Process",
        "fact": "Floating rate personal loans have 0% foreclosure charges after 6 completed EMIs; fixed rate loans carry a 2% preclosure fee on outstanding principal.",
        "allowed_claims": ["0% preclosure charge for floating rate loans after 6 EMIs", "2% preclosure charge on outstanding balance for fixed rate loans", "Foreclosure letter generated in app upon final settlement"],
        "prohibited_claims": ["Allow preclosure before payment of accrued interest", "State foreclosure is impossible before full tenure", "Accept cash payments directly without receipt"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_004",
        "domain": "Lending",
        "topic": "No Objection Certificate (NOC) Issuance",
        "fact": "Upon complete loan clearance and balance verification, the synthetic loan NOC is issued digitally in the document vault within 7 working days.",
        "allowed_claims": ["Digital NOC generated within 7 working days of closure", "Available for download in customer document portal", "Physical copy dispatch available on request"],
        "prohibited_claims": ["Issue NOC while pending dues or charges remain", "Promise same-hour NOC issuance before ledger reconciliation", "Demand extra unofficial documentation fees"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_005",
        "domain": "Lending",
        "topic": "NACH / e-Mandate Bounce Charges",
        "fact": "If an automated NACH mandate returns unpaid due to insufficient funds, a synthetic mandate bounce fee of INR 350 is levied by the lending platform in addition to bank charges.",
        "allowed_claims": ["Platform mandate bounce fee is INR 350", "Customer bank may levy separate bounce charges", "Maintain adequate balance 24 hours prior to EMI date"],
        "prohibited_claims": ["Refund customer issuing bank mandate return charges", "Guarantee bank will waive external penalty", "Stop scheduled mandate presentation without formal loan pause"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_006",
        "domain": "Lending",
        "topic": "Loan Eligibility and Credit Score Criteria",
        "fact": "Synthetic personal loan approval requires a minimum bureau credit score of 720 and a debt-to-income ratio below 45%; actual approval is subject to automated underwriting.",
        "allowed_claims": ["Minimum benchmark bureau score is 720", "DTI ratio must be below 45%", "Underwriting decisions are automated based on income and liabilities"],
        "prohibited_claims": ["Guarantee loan approval to any applicant", "Approve loan applications directly in chat", "Promise loans without bureau or income verification"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_007",
        "domain": "Lending",
        "topic": "Part-Payment Policy",
        "fact": "Borrowers may make part-prepayments with a minimum value of 2 EMI equivalents; part-payments reduce outstanding principal and adjust subsequent EMI amount or tenure.",
        "allowed_claims": ["Minimum part-prepayment is 2 EMI amounts", "Reduces principal balance directly", "Borrower can choose lower EMI or shorter tenure in app"],
        "prohibited_claims": ["Accept micro-prepayments under minimum threshold", "Refuse principal adjustment on part-payment", "Charge penalty on floating rate personal part-payment"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_008",
        "domain": "Lending",
        "topic": "Income Document Requirements",
        "fact": "Salaried applicants must submit last 3 months salary slips and 6 months bank statements; self-employed applicants require 2 years ITR computation and 12 months bank statements.",
        "allowed_claims": ["Salaried: 3 months salary slips and 6 months bank statement", "Self-employed: 2 years ITR and 12 months bank statements", "Upload in PDF format through customer portal"],
        "prohibited_claims": ["Exempt documentation requirements verbally", "Accept fabricated financial proofs", "Promise loans without income verification"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_009",
        "domain": "Lending",
        "topic": "Loan Moratorium Policy",
        "fact": "Moratorium or payment holiday options are not available on standard consumer personal loans except during regulatory emergency relief notifications.",
        "allowed_claims": ["Moratorium is not offered on standard personal loans", "Regular repayments must be maintained to avoid late fees", "Contact special servicing desk for financial hardship escalation"],
        "prohibited_claims": ["Grant immediate payment holiday in chat", "Promise zero interest accrual during missed period", "Erase loan obligations"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_010",
        "domain": "Lending",
        "topic": "Credit Bureau Dispute Resolution",
        "fact": "Discrepancies in reported synthetic loan repayment status are investigated and corrected with credit bureaus within 30 statutory days upon submitting clearance proof.",
        "allowed_claims": ["Disputes investigated within 30 days", "Requires submission of payment receipt / bank statement", "Bureau records updated upon underwriting verification"],
        "prohibited_claims": ["Delete legitimate default history from credit bureau", "Promise 24-hour credit score restoration", "Charge fees for credit record corrections"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_011",
        "domain": "Lending",
        "topic": "Interest Calculation Method",
        "fact": "Interest on synthetic personal loans is computed on a daily reducing balance method at the contractual annual percentage rate divided by 365.",
        "allowed_claims": ["Calculated on daily reducing balance method", "Interest applies only to unpaid principal balance", "Detailed amortization schedule visible in loan overview"],
        "prohibited_claims": ["Calculate using flat rate while advertising reducing rate", "Alter agreed interest rate without formal notice", "Charge interest on fully cleared loans"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_012",
        "domain": "Lending",
        "topic": "Loan Disbursement Timeline",
        "fact": "Once e-sign agreement and digital mandate registration succeed, approved loan funds disburse to verified beneficiary bank accounts within 4 hours.",
        "allowed_claims": ["Disbursement occurs within 4 hours of e-sign and mandate setup", "Disbursed only to primary verified bank account", "UTR reference generated upon transfer"],
        "prohibited_claims": ["Disburse loans into third-party unverified bank accounts", "Guarantee disbursement before mandate verification", "Request upfront processing fee via personal UPI"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_013",
        "domain": "Lending",
        "topic": "Co-Applicant Removal Request",
        "fact": "A co-applicant cannot be removed from an active loan facility unless the loan is refinanced or the primary borrower demonstrates standalone credit qualification.",
        "allowed_claims": ["Co-applicant removal requires refinancing or full re-underwriting", "Primary borrower must qualify individually for outstanding debt", "Requires joint written application"],
        "prohibited_claims": ["Release co-applicant liability immediately in chat", "Remove co-applicant without underwriting review", "Accept unilateral removal without co-borrower consent"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_014",
        "domain": "Lending",
        "topic": "Address Change on Loan Account",
        "fact": "Address updates require submission of an officially valid document (OVD) such as Aadhaar, Passport, or synthetic utility bill dated within 60 days.",
        "allowed_claims": ["Submit valid address proof in document portal", "OVD verification completes within 2 business days", "Updated address reflects on future loan notices"],
        "prohibited_claims": ["Update legal address based on unverified chat request", "Accept expired documents", "Change jurisdiction to avoid recovery notices"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_LOAN_015",
        "domain": "Lending",
        "topic": "Top-up Loan Eligibility",
        "fact": "Existing borrowers with at least 9 consecutive on-time EMI repayments and zero default history are eligible to apply for top-up borrowing.",
        "allowed_claims": ["Requires 9 consecutive on-time EMI payments", "Requires clean repayment record", "Top-up subject to fresh affordability assessment"],
        "prohibited_claims": ["Guarantee top-up approval to defaulting borrowers", "Disburse top-up without income or bureau check", "Stack top-ups beyond prudential debt caps"],
        "source_label": "Synthetic Knowledge Base"
    },

    # --- INSURANCE (10) ---
    {
        "knowledge_id": "KB_INS_001",
        "domain": "Insurance",
        "topic": "Health Insurance Cashless Claim Pre-Authorization",
        "fact": "Cashless pre-authorization requests for planned hospital admissions must be submitted to the third-party administrator (TPA) at least 48 hours prior to hospitalization.",
        "allowed_claims": ["Planned admission pre-authorization SLA is 48 hours prior", "Emergency admissions require intimation within 24 hours", "Hospital TPA desk facilitates submission"],
        "prohibited_claims": ["Guarantee 100% bill clearance without policy exclusions", "Override TPA medical necessity review", "Promise cash payout at hospital gate"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INS_002",
        "domain": "Insurance",
        "topic": "Health Policy Grace Period",
        "fact": "A grace period of 30 days is provided for annual premium renewal; policy coverage is inactive for claims arising during the unpaid grace window.",
        "allowed_claims": ["30-day grace period for annual renewal payment", "Claims occurring during unpaid gap are not covered", "Continuity benefits like waiting periods are preserved upon payment"],
        "prohibited_claims": ["Honor medical claims during lapse period", "Extend grace period indefinitely", "Waive premium payments permanently"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INS_003",
        "domain": "Insurance",
        "topic": "Free-Look Cancellation Period",
        "fact": "A 15-day free-look period (30 days for electronic policies) applies from policy receipt date; premium is refunded minus proportionate risk coverage and medical test costs.",
        "allowed_claims": ["15 days for physical / 30 days for digital policy free-look", "Proportionate risk premium and stamp duty deducted", "Initiate cancellation through policy servicing dashboard"],
        "prohibited_claims": ["Refuse free-look refund within statutory window", "Refund 100% if medical tests were conducted by insurer", "Cancel policy without customer authorization"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INS_004",
        "domain": "Insurance",
        "topic": "Pre-Existing Disease (PED) Waiting Period",
        "fact": "Standard health insurance policies mandate a 36-month waiting period for pre-existing medical conditions disclosed during proposal inception.",
        "allowed_claims": ["PED waiting period is 36 consecutive policy months", "Conditions must be declared at time of application", "Accidental emergencies are covered from day one"],
        "prohibited_claims": ["Waive PED waiting period in chat", "Advise non-disclosure of medical history", "Claim chronic ailments are covered instantly"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INS_005",
        "domain": "Insurance",
        "topic": "Motor Insurance No Claim Bonus (NCB)",
        "fact": "No Claim Bonus ranges from 20% to 50% discount on own-damage premium; any registered claim in the preceding policy year resets NCB to 0%.",
        "allowed_claims": ["NCB discount starts at 20% and caps at 50%", "Filing a claim resets NCB to 0% for renewal", "NCB is transferable when replacing insured vehicle"],
        "prohibited_claims": ["Protect NCB without NCB-protect add-on cover", "Transfer NCB between unrelated individuals", "Fabricate zero-claim certificates"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INS_006",
        "domain": "Insurance",
        "topic": "Nominee Endorsement Procedure",
        "fact": "Policyholders can update nominee details by submitting Section 39 nomination endorsement form along with relationship proof and nominee photo ID.",
        "allowed_claims": ["Nominee updates require relationship proof and ID", "Process through online policy services portal", "Updated endorsement schedule issued within 3 days"],
        "prohibited_claims": ["Designate unrelated minor without legal appointee", "Change nomination on deceased policyholder without legal heirship", "Withhold death claim proceeds from registered nominee"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INS_007",
        "domain": "Insurance",
        "topic": "Reimbursement Claim Submission SLA",
        "fact": "Reimbursement medical claim documentation including original bills and discharge summary must be submitted within 30 days of hospital discharge.",
        "allowed_claims": ["Submit claim documents within 30 days of discharge", "Original hospital invoices and prescriptions required", "Digital submission supported with physical verification"],
        "prohibited_claims": ["Accept claims without hospital bills or doctor prescriptions", "Promise payout without verifying claim documents", "Waive statutory claim filing time limits unilaterally"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INS_008",
        "domain": "Insurance",
        "topic": "Critical Illness Survival Period",
        "fact": "Critical illness benefit payout requires the insured to survive a mandatory 30-day period following first clinical diagnosis of the covered condition.",
        "allowed_claims": ["Mandatory 30-day survival period after diagnosis", "Diagnosis must be certified by registered specialist doctor", "Lump sum benefit paid upon claim approval"],
        "prohibited_claims": ["Disburse critical illness benefit without survival verification", "Cover conditions outside contractual schedule", "Offer medical diagnoses or clinical advice"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INS_009",
        "domain": "Insurance",
        "topic": "Term Life Suicide Exclusion Clause",
        "fact": "In synthetic term life policies, death resulting from suicide within 12 months from policy inception or revival date is excluded from death benefit payout.",
        "allowed_claims": ["Suicide excluded within first 12 months of inception/revival", "80% of premiums paid refunded to nominee under standard terms", "Full coverage active after 12 months"],
        "prohibited_claims": ["Promise full sum assured payout within initial 12 months", "Provide unauthorized legal advice on disputed claims", "Alter policy exclusions"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INS_010",
        "domain": "Insurance",
        "topic": "Motor Third-Party Damage Intimation",
        "fact": "Accidents involving third-party property damage or bodily injury require mandatory police FIR copy and immediate insurer surveyor intimation within 48 hours.",
        "allowed_claims": ["Mandatory FIR required for third-party accidents", "Intimate insurer within 48 hours for survey", "Surveyor inspection must precede vehicle repair"],
        "prohibited_claims": ["Authorize repair without insurance surveyor inspection", "Settle third-party liabilities out of pocket on behalf of insurer", "Falsify accident location or vehicle driver details"],
        "source_label": "Synthetic Knowledge Base"
    },

    # --- INVESTMENTS (10) ---
    {
        "knowledge_id": "KB_INV_001",
        "domain": "Investments",
        "topic": "Mutual Fund Redemption NAV Applicability",
        "fact": "For equity mutual fund redemption requests submitted before 3:00 PM cut-off on business days, the same-day closing NAV applies; after 3:00 PM, next business day NAV applies.",
        "allowed_claims": ["Cut-off time is 3:00 PM for same-day NAV", "Orders after 3:00 PM receive next business day NAV", "Settlement proceeds credit within T+2 business days"],
        "prohibited_claims": ["Guarantee future NAV pricing or market gains", "Override exchange cut-off timestamps", "Provide personalized stock or mutual fund picking advice"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INV_002",
        "domain": "Investments",
        "topic": "SIP Pause Facility",
        "fact": "Investors may pause an active Systematic Investment Plan (SIP) for up to 3 consecutive months by submitting a request at least 7 days before the next debit date.",
        "allowed_claims": ["SIP pause permitted for 1 to 3 months", "Must submit pause request 7 days before debit", "SIP auto-resumes after pause period expires"],
        "prohibited_claims": ["Guarantee market timing returns from pausing SIP", "Charge penalty fees for pausing SIP", "Delete accumulated mutual fund units on pause"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INV_003",
        "domain": "Investments",
        "topic": "Mandatory Re-KYC Compliance",
        "fact": "Periodic re-KYC is mandatory every 2 years for high-risk profiles and every 5 years for normal profiles; failure to update locks redemption transactions.",
        "allowed_claims": ["Re-KYC required periodically under regulations", "Uncompleted re-KYC temporarily halts redemptions", "Complete digital re-KYC using Aadhaar OTP in profile"],
        "prohibited_claims": ["Allow asset liquidations with expired KYC", "Exempt users from AML/KYC regulations", "Request banking login credentials for KYC"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INV_004",
        "domain": "Investments",
        "topic": "Capital Gains Statement Availability",
        "fact": "Consolidated capital gains statements for the preceding financial year are made available for download in the tax reports section by May 15.",
        "allowed_claims": ["Capital gains statements available by May 15", "Downloadable from tax reports dashboard", "Covers realized gains, dividend income, and STT"],
        "prohibited_claims": ["Provide certified tax filing advisory", "Calculate individualized income tax liability for filing", "Alter reported purchase or sale timestamps"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INV_005",
        "domain": "Investments",
        "topic": "Demat Account Inoperative Status",
        "fact": "A demat account with zero transactions and trades for 12 consecutive months is classified as inoperative / dormant and requires biometric or OTP re-activation.",
        "allowed_claims": ["Dormancy triggers after 12 months zero activity", "Securities remain safely held in depository vault", "Re-activate via simple in-app identity verification"],
        "prohibited_claims": ["Claim deposited securities will be forfeited", "Charge illegal reactivation fees", "Permit unauthorized trading on dormant accounts"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INV_006",
        "domain": "Investments",
        "topic": "Dividend Credit Mechanism",
        "fact": "Dividends declared by companies or mutual funds are directly credited to the investor registered primary bank account via ECS/NACH on record date.",
        "allowed_claims": ["Dividends credit directly to verified bank account", "No platform handling charge for dividend credits", "Track payment via dividend mandate reference in statement"],
        "prohibited_claims": ["Hold dividend funds in unverified wallets", "Guarantee dividend yields or corporate declarations", "Alter corporate ex-dividend dates"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INV_007",
        "domain": "Investments",
        "topic": "Prohibition of Advisory and Recommendations",
        "fact": "The support assistant is strictly an operational workflow and is prohibited by policy from recommending specific stocks, mutual funds, or trading strategies.",
        "allowed_claims": ["Support is an execution and information service only", "No individualized investment recommendations or stock tips", "Consult a registered investment advisor for financial planning"],
        "prohibited_claims": ["Recommend buying or selling specific tickers", "Promise guaranteed market returns or portfolio yield", "Provide personalized asset allocation advice"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INV_008",
        "domain": "Investments",
        "topic": "STP and SWP Order Modifications",
        "fact": "Modifications or cancellations to Systematic Transfer Plans (STP) and Systematic Withdrawal Plans (SWP) take effect within 10 business days.",
        "allowed_claims": ["STP/SWP modification SLA is 10 business days", "Pending cycle may execute if requested within 10 days", "Manage instructions in automated plans menu"],
        "prohibited_claims": ["Execute immediate retrospective STP cancellations", "Guarantee exit without applicable exit load", "Override asset management company processing timelines"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INV_009",
        "domain": "Investments",
        "topic": "Exit Load Applicability",
        "fact": "Equity funds typically charge a 1% exit load on units redeemed within 365 days of allocation; units redeemed after 1 year carry 0% exit load.",
        "allowed_claims": ["1% exit load applies for redemptions under 365 days", "0% exit load after 1 year holding", "Exit load deducted from gross redemption proceeds"],
        "prohibited_claims": ["Waive contractual AMC exit load", "Claim all equity mutual funds are exit-load free", "Misrepresent redemption net proceeds"],
        "source_label": "Synthetic Knowledge Base"
    },
    {
        "knowledge_id": "KB_INV_010",
        "domain": "Investments",
        "topic": "Transmission of Units upon Account Holder Decease",
        "fact": "Transmission of mutual fund units to a registered nominee requires death certificate, succession/nomination claim form, and nominee KYC verification.",
        "allowed_claims": ["Requires certified death certificate and claim form", "Nominee must complete KYC verification", "Units transmitted into nominee demat / folio upon audit"],
        "prohibited_claims": ["Liquidate deceased account assets without legal proof", "Disburse funds to non-nominee third parties", "Bypass statutory succession legal requirements"],
        "source_label": "Synthetic Knowledge Base"
    },
]


def generate_knowledge_base_csv() -> None:
    csv_path = DATA_DIR / "knowledge_base.csv"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "knowledge_id",
        "domain",
        "topic",
        "fact",
        "allowed_claims",
        "prohibited_claims",
        "source_label",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in KNOWLEDGE_ENTRIES:
            row = dict(entry)
            row["allowed_claims"] = json.dumps(row["allowed_claims"])
            row["prohibited_claims"] = json.dumps(row["prohibited_claims"])
            writer.writerow(row)

    print(f"Generated {len(KNOWLEDGE_ENTRIES)} knowledge base entries at {csv_path}")


if __name__ == "__main__":
    generate_knowledge_base_csv()
