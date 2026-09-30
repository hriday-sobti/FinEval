"""Custom Analyst Theme and Professional Styling for Streamlit.

Enforces:
- Clean, compact internal tool feel
- Restrained color system (off-white, slate gray, subtle green, subtle amber, subtle red)
- High information density, compact cards, crisp tables
- Zero flashy animations or AI hype gradients
"""

ANALYST_CSS = """
<style>
/* Main Container & Typography */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
}

.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Header Banner */
.fineval-header {
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 0.8rem 1.2rem;
    margin-bottom: 1.2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 4px;
}

.fineval-title {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #0f172a;
    margin: 0;
}

.fineval-subtitle {
    font-size: 0.82rem;
    color: #64748b;
    margin: 0;
}

/* Compact KPI Cards */
.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 0.8rem;
    margin-bottom: 1.2rem;
}

.kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 0.75rem 1rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.kpi-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.05em;
    color: #64748b;
    margin-bottom: 0.25rem;
}

.kpi-value {
    font-size: 1.45rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.2;
}

.kpi-subtext {
    font-size: 0.72rem;
    color: #94a3b8;
    margin-top: 0.2rem;
}

/* Badges */
.badge-pass {
    background-color: #ecfdf5;
    color: #065f46;
    border: 1px solid #a7f3d0;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-fail {
    background-color: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-warning {
    background-color: #fffbeb;
    color: #92400e;
    border: 1px solid #fde68a;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-info {
    background-color: #f8fafc;
    color: #334155;
    border: 1px solid #cbd5e1;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Diff Styling */
.diff-equal {
    background-color: #ffffff;
    color: #334155;
    font-family: monospace;
    font-size: 0.82rem;
    padding: 2px 6px;
    border-left: 3px solid #cbd5e1;
    margin: 1px 0;
}

.diff-insert {
    background-color: #f0fdf4;
    color: #166534;
    font-family: monospace;
    font-size: 0.82rem;
    padding: 2px 6px;
    border-left: 3px solid #22c55e;
    margin: 1px 0;
}

.diff-delete {
    background-color: #fef2f2;
    color: #991b1b;
    font-family: monospace;
    font-size: 0.82rem;
    padding: 2px 6px;
    border-left: 3px solid #ef4444;
    margin: 1px 0;
}

/* Clean code block */
pre, code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace !important;
    font-size: 0.85rem !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #f8fafc;
    border-right: 1px solid #e2e8f0;
}
</style>
"""


def apply_analyst_styling():
    import streamlit as st
    st.markdown(ANALYST_CSS, unsafe_allow_html=True)
