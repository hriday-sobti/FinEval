"""Chart generation utilities for FinEval report.

Produces publication-quality PNG charts from database metrics.
Charts are embedded into the PDF report via ReportLab Image.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── Palette ──────────────────────────────────────────────────────────────────
PALETTE = {
    "V1": "#ef4444",
    "V2": "#f97316",
    "V3": "#eab308",
    "V4": "#22c55e",
    "primary": "#1e3a5f",
    "accent": "#3b82f6",
    "bg": "#f8fafc",
    "text": "#1e293b",
    "muted": "#64748b",
    "critical": "#dc2626",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#22c55e",
}


def _fig() -> tuple[plt.Figure, plt.Axes]:
    """Return a fig+axis with clean styling."""
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=150)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    for spine in ax.spines.values():
        spine.set_color("#cbd5e1")
    ax.tick_params(colors="#475569", labelsize=9)
    ax.grid(color="#e2e8f0", linestyle="-", axis="y", zorder=0)
    return fig, ax


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", dpi=150, facecolor="#ffffff")
    plt.close(fig)
    print(f"  Chart: {path.name}")


def generate_charts(reports_dir: Path) -> dict[str, Path]:
    """Generate all chart PNGs. Returns {name: path} mapping."""
    charts: dict[str, Path] = {}
    charts_dir = reports_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Score Trajectory ────────────────────────────────────────────────
    fig, ax = _fig()
    versions = ["V1", "V2", "V3", "V4"]
    scores = [48.52, 61.19, 76.48, 84.27]
    colors = [PALETTE[v] for v in versions]

    ax.plot(versions, scores, marker="o", markersize=8, linewidth=2.5,
            color=PALETTE["primary"], zorder=3, label="Avg Quality Score")
    for i, (v, s) in enumerate(zip(versions, scores)):
        ax.annotate(f"{s:.1f}%", (v, s), textcoords="offset points",
                    xytext=(0, 12), ha="center", fontsize=9, fontweight="bold",
                    color=colors[i])

    ax.set_ylabel("Average Quality Score (%)", fontsize=10)
    ax.set_xlabel("Prompt Version", fontsize=10)
    ax.set_title("Score Progression Across Prompt Versions", fontsize=12, fontweight="bold", pad=10)
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right", framealpha=0.9)
    _save(fig, charts_dir / "01_score_trajectory.png")
    charts["score_trajectory"] = charts_dir / "01_score_trajectory.png"

    # ── 2. Category Pass Rates (V4) ────────────────────────────────────────
    fig, ax = _fig()
    cats = ["Standard", "Contradictory", "Ambiguous", "Multi-turn",
            "Policy / Escalation", "Edge Case", "Adversarial", "Hallucination Trap"]
    rates = [100.0, 100.0, 97.0, 97.0, 94.7, 93.9, 88.0, 0.0]
    pass_counts = [65, 26, 32, 32, 18, 31, 22, 0]
    totals = [65, 26, 33, 33, 19, 33, 25, 26]
    # Color: green if >=90, yellow if 80-89, red if <80, orange for trap
    bar_colors = []
    for r in rates:
        if r >= 95:
            bar_colors.append(PALETTE["V4"])
        elif r >= 85:
            bar_colors.append(PALETTE["V3"])
        elif r >= 80:
            bar_colors.append(PALETTE["V2"])
        else:
            bar_colors.append(PALETTE["V1"])
    # Hallucination Trap gets special red
    bar_colors[-1] = PALETTE["critical"]

    bars = ax.bar(cats, rates, color=bar_colors, edgecolor="#e2e8f0", linewidth=0.5)
    for bar, pc, tc in zip(bars, pass_counts, totals):
        if tc > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                    f"{pc}/{tc}", ha="center", va="bottom", fontsize=8, color=PALETTE["text"])

    ax.set_ylabel("Pass Rate (%)", fontsize=10)
    ax.set_xlabel("Category (V4, 200 cases)", fontsize=10)
    ax.set_title("V4 Pass Rate by Scenario Category", fontsize=12, fontweight="bold", pad=10)
    ax.set_ylim(0, 110)
    ax.axhline(y=80, color=PALETTE["critical"], linestyle="--", alpha=0.6, linewidth=1, label="Pass threshold (80%)")
    ax.legend(fontsize=8)
    plt.xticks(rotation=25, ha="right")
    _save(fig, charts_dir / "02_category_pass_rates.png")
    charts["category_pass_rates"] = charts_dir / "02_category_pass_rates.png"

    # ── 3. Failure Composition Stacked Bar ──────────────────────────────────
    fig, ax = _fig()
    fail_types = ["F1\nHallucination", "F4\nContext Loss", "F6\nOverconfidence", "F7\nFormatting"]
    v1_counts = [3, 4, 11, 0]
    v2_counts = [0, 4, 0, 0]
    v3_counts = [4, 0, 0, 0]
    v4_counts = [21, 1, 0, 15]

    x = np.arange(len(fail_types))
    w = 0.2
    ax.bar(x - 1.5 * w, v1_counts, w, label="V1 (60 cases)", color=PALETTE["V1"], edgecolor="#e2e8f0", linewidth=0.5)
    ax.bar(x - 0.5 * w, v2_counts, w, label="V2 (60 cases)", color=PALETTE["V2"], edgecolor="#e2e8f0", linewidth=0.5)
    ax.bar(x + 0.5 * w, v3_counts, w, label="V3 (60 cases)", color=PALETTE["V3"], edgecolor="#e2e8f0", linewidth=0.5)
    ax.bar(x + 1.5 * w, v4_counts, w, label="V4 (200 cases)", color=PALETTE["V4"], edgecolor="#e2e8f0", linewidth=0.5)

    # Annotate counts
    for i, (v1, v2, v3, v4) in enumerate(zip(v1_counts, v2_counts, v3_counts, v4_counts)):
        vals = [v1, v2, v3, v4]
        positions = [i - 1.5 * w, i - 0.5 * w, i + 0.5 * w, i + 1.5 * w]
        colors_label = [PALETTE["V1"], PALETTE["V2"], PALETTE["V3"], PALETTE["V4"]]
        for pos, val, col in zip(positions, vals, colors_label):
            if val > 0:
                ax.text(pos, val / 2, str(val), ha="center", va="center",
                        fontsize=7, color="white", fontweight="bold")

    ax.set_ylabel("Failure Count", fontsize=10)
    ax.set_xlabel("Failure Type", fontsize=10)
    ax.set_title("Failure Composition Across Prompt Versions", fontsize=12, fontweight="bold", pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(fail_types, fontsize=9)
    ax.legend(fontsize=8, loc="upper right")
    _save(fig, charts_dir / "03_failure_composition.png")
    charts["failure_composition"] = charts_dir / "03_failure_composition.png"

    # ── 4. V4 Radar Chart (7 Dimensions) ────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5.5, 5.5), dpi=150, subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#ffffff")

    dims = ["Accuracy\n(20%)", "Grounded-\nness (20%)", "Instruction\nFollowing (15%)",
            "Relevance\n(15%)", "Consistency\n(10%)", "Safety\n(10%)", "Clarity\n(10%)"]
    # Normalize to 0-100 scale (scores are out of 5.0)
    raw = [4.59, 4.59, 4.74, 1.80, 4.49, 4.82, 4.67]
    vals = [r / 5.0 * 100 for r in raw]
    vals.append(vals[0])  # close the loop
    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]

    ax.plot(angles, vals, "o-", linewidth=2, color=PALETTE["primary"], markersize=6)
    ax.fill(angles, vals, color=PALETTE["accent"], alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dims, fontsize=9)
    ax.set_ylim(0, 110)
    ax.set_title("V4 Dimension Profile (7-Rubric, normalized %)", fontsize=12, fontweight="bold", pad=20)

    # Annotate each point
    for angle, val, dim_name in zip(angles[:-1], vals[:-1], dims):
        ax.annotate(f"{val:.0f}%", (angle, val), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8, fontweight="bold")

    # Add concentric circles at 20% intervals
    for level in [20, 40, 60, 80, 100]:
        ax.axhline(y=level, color="#e2e8f0", linestyle="-", linewidth=0.5)
    ax.grid(True, color="#cbd5e1", linestyle="-", linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_color("#cbd5e1")
    ax.tick_params(colors="#475569", labelsize=9)

    _save(fig, charts_dir / "04_v4_radar.png")
    charts["v4_radar"] = charts_dir / "04_v4_radar.png"

    # ── 5. Severity Distribution Donut ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5, 4.5), dpi=150)
    fig.patch.set_facecolor("#ffffff")

    sev_labels = ["Critical\n(27)", "Low\n(23)", "High\n(12)", "Medium\n(1)"]
    sev_sizes = [27, 23, 12, 1]
    sev_colors = [PALETTE["critical"], PALETTE["low"], PALETTE["high"], PALETTE["medium"]]

    wedges, texts, autotexts = ax.pie(sev_sizes, labels=sev_labels, colors=sev_colors,
                                       autopct="%1.1f%%", startangle=90,
                                       explode=(0.02, 0, 0, 0),
                                       wedgeprops=dict(width=0.55, edgecolor="#ffffff", linewidth=2))
    for t in autotexts:
        t.set_fontsize(10)
        t.set_fontweight("bold")
    ax.set_title("Failure Severity Distribution\n(63 total events across all versions)",
                 fontsize=12, fontweight="bold", pad=10)

    _save(fig, charts_dir / "05_severity_donut.png")
    charts["severity_donut"] = charts_dir / "05_severity_donut.png"

    # ── 6. Dimension Heatmap (V1-V4 by dimension) ───────────────────────────
    fig, ax = _fig()
    dim_short = ["Accuracy", "Grounded-\nness", "Instr.\nFollow.", "Rele-\nvance", "Consis-\ntency", "Safety", "Clarity"]
    # All versions, normalized to 0-100 (out of 5.0)
    heatmap_data = np.array([
        [2.72, 1.87, 2.00, 1.73, 2.98, 3.50, 3.00],  # V1
        [3.48, 2.05, 3.50, 1.56, 3.45, 4.00, 4.50],  # V2
        [4.05, 4.25, 4.20, 1.87, 4.00, 4.33, 4.20],  # V3
        [4.59, 4.59, 4.74, 1.80, 4.49, 4.82, 4.67],  # V4
    ])
    heatmap_data_pct = heatmap_data / 5.0 * 100

    im = ax.imshow(heatmap_data_pct, cmap="RdYlGn", aspect="auto", vmin=0, vmax=100)
    ax.set_xticks(np.arange(len(dim_short)))
    ax.set_xticklabels(dim_short, fontsize=9)
    ax.set_yticks(np.arange(4))
    ax.set_yticklabels(["V1 (60 cases)", "V2 (60 cases)", "V3 (60 cases)", "V4 (200 cases)"], fontsize=9)
    ax.set_title("Dimension Scores by Version (Heatmap, 0–100%)", fontsize=12, fontweight="bold", pad=10)

    # Annotate cells
    for i in range(4):
        for j in range(7):
            val = heatmap_data_pct[i, j]
            color = "white" if val > 55 else "black"
            ax.text(j, i, f"{val:.0f}%", ha="center", va="center", color=color, fontsize=8, fontweight="bold")

    plt.colorbar(im, ax=ax, label="Score (%)", shrink=0.8)
    _save(fig, charts_dir / "06_dimension_heatmap.png")
    charts["dimension_heatmap"] = charts_dir / "06_dimension_heatmap.png"

    return charts
