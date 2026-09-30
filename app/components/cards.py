"""Reusable KPI Cards, Badges, and Visual Components for FinEval."""

from typing import Optional

import streamlit as st


def render_header(title: str = "FinEval — Financial AI Quality & Prompt Operations Lab", benchmark_label: str = "Synthetic Dataset v1.0"):
    st.markdown(f"""
    <div class="fineval-header">
        <div>
            <div class="fineval-title">{title}</div>
            <div class="fineval-subtitle">Systematic Evaluation • Failure Diagnostics • Prompt Regression Testing</div>
        </div>
        <div>
            <span class="badge-info">Benchmark: {benchmark_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_card(label: str, value: str, subtext: Optional[str] = None):
    subtext_html = f'<div class="kpi-subtext">{subtext}</div>' if subtext else ""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {subtext_html}
    </div>
    """, unsafe_allow_html=True)


def render_badge(text: str, badge_type: str = "info") -> str:
    css_class = f"badge-{badge_type}"
    return f'<span class="{css_class}">{text}</span>'
