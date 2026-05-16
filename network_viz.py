"""
network_viz.py — Network Diagram Visualisation
================================================
Generates a matplotlib figure showing a simple network topology
with animated packet flow indicators.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from typing import Dict, Optional

# ─── Colour Palette (dark-theme friendly) ────────────────────────────
COLOURS = {
    "VIDEO":    "#818cf8",   # indigo-400
    "AUDIO":    "#34d399",   # emerald-400
    "GAMING":   "#fb923c",   # orange-400
    "DOWNLOAD": "#f87171",   # red-400
    "bg":       "#0f172a",   # slate-900
    "node":     "#1e293b",   # slate-800
    "edge":     "#475569",   # slate-500
    "text":     "#e2e8f0",   # slate-200
    "accent":   "#38bdf8",   # sky-400
}

PRIORITY_EMOJIS = {
    "VIDEO":    "🎬",
    "AUDIO":    "🎵",
    "GAMING":   "🎮",
    "DOWNLOAD": "📥",
}


def create_network_diagram(
    packet_counts: Dict[str, int],
    predictions: Dict[str, int],
    scheduler_mode: str = "DUMB",
    congestion: bool = False,
    tick: int = 0,
) -> plt.Figure:
    """
    Draw a network topology diagram with packet flow indicators.

    Layout:
        [Sources] ──► [AI Classifier] ──► [Scheduler] ──► [Destination]

    Packet dots animate along the edges based on counts.
    """
    fig, ax = plt.subplots(1, 1, figsize=(8, 5), facecolor=COLOURS["bg"])
    ax.set_facecolor(COLOURS["bg"])
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-1, 6)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Node positions ────────────────────────────────────────────────
    source_positions = {
        "VIDEO":    (0.5, 4.5),
        "AUDIO":    (0.5, 3.0),
        "GAMING":   (0.5, 1.5),
        "DOWNLOAD": (0.5, 0.0),
    }
    classifier_pos = (4.0, 2.25)
    scheduler_pos  = (7.0, 2.25)
    dest_pos       = (9.5, 2.25)

    # ── Helper: draw a rounded box ────────────────────────────────────
    def draw_node(x, y, label, colour=COLOURS["node"], w=1.6, h=0.8, fontsize=8):
        box = FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.12",
            facecolor=colour,
            edgecolor=COLOURS["accent"],
            linewidth=1.2,
            alpha=0.92,
        )
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=COLOURS["text"],
                family="monospace")

    # ── Draw source nodes ─────────────────────────────────────────────
    for t_type, (sx, sy) in source_positions.items():
        count = packet_counts.get(t_type, 0)
        emoji = PRIORITY_EMOJIS[t_type]
        label = f"{emoji} {t_type}\n{count:,} pkts"
        draw_node(sx, sy, label, colour=COLOURS["node"], w=1.8, h=0.85, fontsize=7)

    # ── Draw central nodes ────────────────────────────────────────────
    draw_node(*classifier_pos, "🧠 AI\nClassifier", w=1.6, h=1.0, fontsize=8)

    sched_colour = "#064e3b" if scheduler_mode == "SMART" else "#1e293b"
    sched_label = f"{'⚡' if scheduler_mode == 'SMART' else '📦'} {scheduler_mode}\nScheduler"
    draw_node(*scheduler_pos, sched_label, colour=sched_colour, w=1.6, h=1.0, fontsize=8)

    draw_node(*dest_pos, "🌐\nNetwork", w=1.2, h=0.9, fontsize=8)

    # ── Draw edges with animated packet dots ──────────────────────────
    for t_type, (sx, sy) in source_positions.items():
        cx, cy = classifier_pos
        colour = COLOURS[t_type]

        # Source → Classifier
        ax.annotate(
            "", xy=(cx - 0.8, cy + (sy - cy) * 0.15),
            xytext=(sx + 0.9, sy),
            arrowprops=dict(arrowstyle="-|>", color=colour, lw=1.5, alpha=0.7),
        )

        # Animate dots along the edge
        count = packet_counts.get(t_type, 0)
        n_dots = min(5, max(1, count // 200))
        for i in range(n_dots):
            phase = ((tick * 0.3 + i * 0.2) % 1.0)
            dx = sx + 0.9 + (cx - 0.8 - sx - 0.9) * phase
            dy = sy + (cy + (sy - cy) * 0.15 - sy) * phase
            ax.plot(dx, dy, "o", color=colour, markersize=4 + (i % 2) * 2, alpha=0.9)

    # Classifier → Scheduler
    ax.annotate(
        "", xy=(scheduler_pos[0] - 0.8, scheduler_pos[1]),
        xytext=(classifier_pos[0] + 0.8, classifier_pos[1]),
        arrowprops=dict(arrowstyle="-|>", color=COLOURS["accent"], lw=2.0, alpha=0.8),
    )

    # Scheduler → Destination
    ax.annotate(
        "", xy=(dest_pos[0] - 0.6, dest_pos[1]),
        xytext=(scheduler_pos[0] + 0.8, scheduler_pos[1]),
        arrowprops=dict(arrowstyle="-|>", color=COLOURS["accent"], lw=2.0, alpha=0.8),
    )

    # Animated dots on central path
    for i in range(3):
        phase = ((tick * 0.25 + i * 0.33) % 1.0)
        dx = classifier_pos[0] + 0.8 + (dest_pos[0] - 0.6 - classifier_pos[0] - 0.8) * phase
        ax.plot(dx, classifier_pos[1], "D", color=COLOURS["accent"],
                markersize=5, alpha=0.7 + 0.3 * np.sin(phase * np.pi))

    # ── Congestion indicator ──────────────────────────────────────────
    if congestion:
        ax.text(5.5, 5.3, "⚠️  CONGESTION — 10 Mbps CAP",
                ha="center", va="center", fontsize=11, fontweight="bold",
                color="#fbbf24", family="monospace",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#7c2d12", edgecolor="#f59e0b", alpha=0.9))

    # ── Legend ────────────────────────────────────────────────────────
    handles = [
        mpatches.Patch(color=COLOURS[t], label=f"{PRIORITY_EMOJIS[t]} {t}")
        for t in ["VIDEO", "AUDIO", "GAMING", "DOWNLOAD"]
    ]
    ax.legend(
        handles=handles, loc="lower center", ncol=4,
        fontsize=7, framealpha=0.3, facecolor=COLOURS["bg"],
        edgecolor=COLOURS["edge"], labelcolor=COLOURS["text"],
    )

    fig.tight_layout(pad=0.5)
    return fig


def create_metric_charts(
    history_dumb: list,
    history_smart: list,
    metric_name: str,
    ylabel: str,
    title: str,
    colour_dumb: str = "#FF4444",
    colour_smart: str = "#00FF88",
    congestion_start_idx: Optional[int] = None,
) -> plt.Figure:
    """
    Create a single line chart comparing DUMB vs SMART for one metric.
    """
    fig, ax = plt.subplots(1, 1, figsize=(4, 2.2), facecolor=COLOURS["bg"])
    ax.set_facecolor(COLOURS["bg"])

    x = list(range(len(history_dumb)))
    y_dumb = [getattr(m, metric_name, 0) for m in history_dumb]
    y_smart = [getattr(m, metric_name, 0) for m in history_smart]

    ax.plot(x, y_dumb, color=colour_dumb, linewidth=1.5, alpha=0.8, label="DUMB (FIFO)")
    ax.fill_between(x, y_dumb, alpha=0.1, color=colour_dumb)
    ax.plot(x, y_smart, color=colour_smart, linewidth=1.5, alpha=0.8, label="SMART (AI)")
    ax.fill_between(x, y_smart, alpha=0.1, color=colour_smart)

    if congestion_start_idx is not None and 0 <= congestion_start_idx < len(x):
        ax.axvline(x=congestion_start_idx, color='red', linestyle='--', alpha=0.8, linewidth=1.5)
        ax.text(congestion_start_idx + 1, ax.get_ylim()[1] * 0.85, "CONGESTION START",
                color='red', fontsize=6, fontweight='bold', rotation=90)

    ax.set_title(title, fontsize=9, fontweight="bold", color=COLOURS["text"], pad=6)
    ax.set_ylabel(ylabel, fontsize=7, color=COLOURS["text"])
    ax.set_xlabel("Time (s)", fontsize=7, color=COLOURS["text"])
    ax.tick_params(colors=COLOURS["text"], labelsize=6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLOURS["edge"])
    ax.spines["bottom"].set_color(COLOURS["edge"])
    ax.legend(fontsize=6, loc="upper right", framealpha=0.3,
              facecolor=COLOURS["bg"], edgecolor=COLOURS["edge"], labelcolor=COLOURS["text"])
    ax.grid(True, alpha=0.15, color=COLOURS["edge"])

    fig.tight_layout(pad=0.8)
    return fig
