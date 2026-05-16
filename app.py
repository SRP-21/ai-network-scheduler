"""
app.py — Streamlit Dashboard
==============================
Dark-themed, three-column live dashboard that shows AI making a
simulated network smarter in real time.

Run with:  streamlit run app.py
"""

import streamlit as st
import time
import sys
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import defaultdict

# ── Ensure local imports work ─────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traffic_generator import TrafficEngine, TRAFFIC_TYPES
from ml_classifier import TrafficClassifier
from scheduler import NetworkScheduler
from network_viz import create_network_diagram, create_metric_charts, COLOURS

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG & DARK THEME
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Network Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# FIX: Added min-width:0 and overflow-wrap to all metric cards to prevent text truncation
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');

/* ── Global dark theme ─────────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    color: #e2e8f0;
    font-family: 'Inter', sans-serif;
}

/* ── Headers ───────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
h1 {
    background: linear-gradient(90deg, #38bdf8, #818cf8, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2rem !important;
}

/* ── Metric cards — FIX: prevent truncation ────────── */
div[data-testid="stMetric"] {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 12px;
    padding: 10px 10px;
    backdrop-filter: blur(8px);
    min-width: 0;
    overflow: visible;
}
div[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.65rem !important;
    white-space: nowrap;
    overflow: visible;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #38bdf8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.1rem !important;
    white-space: nowrap;
    overflow: visible;
}

/* ── Buttons ───────────────────────────────────────── */
.stButton > button {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.3s ease !important;
    border: none !important;
    font-size: 0.75rem !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(56, 189, 248, 0.3);
}

/* ── Sidebar ───────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0f172a !important;
}

/* ── Dividers ──────────────────────────────────────── */
hr { border-color: rgba(56, 189, 248, 0.15) !important; }

/* ── Status badges ─────────────────────────────────── */
.badge-smart {
    background: linear-gradient(135deg, #059669, #10b981);
    padding: 4px 14px; border-radius: 20px;
    color: white; font-weight: 700; font-size: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    display: inline-block;
}
.badge-dumb {
    background: linear-gradient(135deg, #64748b, #94a3b8);
    padding: 4px 14px; border-radius: 20px;
    color: white; font-weight: 700; font-size: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    display: inline-block;
}
.badge-congestion {
    background: linear-gradient(135deg, #dc2626, #f87171);
    padding: 4px 14px; border-radius: 20px;
    color: white; font-weight: 700; font-size: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    display: inline-block;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* ── Glassmorphism panels ──────────────────────────── */
.glass-panel {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(56, 189, 248, 0.12);
    border-radius: 12px;
    padding: 16px;
    backdrop-filter: blur(12px);
    margin-bottom: 12px;
}

/* ── HTML traffic table ────────────────────────── */
table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    margin-bottom: 12px;
}
table th {
    background: rgba(56, 189, 248, 0.15);
    color: #94a3b8;
    padding: 6px 8px;
    text-align: left;
    border-bottom: 1px solid rgba(56, 189, 248, 0.2);
    font-weight: 700;
    white-space: nowrap;
}
table td {
    padding: 5px 8px;
    color: #e2e8f0;
    border-bottom: 1px solid rgba(56, 189, 248, 0.08);
    white-space: nowrap;
}
table tr:hover td {
    background: rgba(56, 189, 248, 0.05);
}

/* FIX: Force Streamlit column children to not truncate */
div[data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
    overflow: visible !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════
if "engine" not in st.session_state:
    st.session_state.engine = TrafficEngine()

if "classifier" not in st.session_state:
    clf = TrafficClassifier()
    clf.train()
    st.session_state.classifier = clf
    st.session_state.ml_metrics = {
        "train_accuracy": clf.train_accuracy,
        "test_accuracy": clf.test_accuracy,
        "feature_importances": clf.feature_importances,
    }

if "scheduler" not in st.session_state:
    st.session_state.scheduler = NetworkScheduler()

if "tick" not in st.session_state:
    st.session_state.tick = 0

if "is_paused" not in st.session_state:
    st.session_state.is_paused = False

if "congestion_start_tick" not in st.session_state:
    st.session_state.congestion_start_tick = None

if "prediction_counts" not in st.session_state:
    st.session_state.prediction_counts = defaultdict(int)

if "last_ui_state" not in st.session_state:
    st.session_state.last_ui_state = {
        "pred_counts": defaultdict(int),
        "live_accuracy": 0.0
    }

# Shorthand
engine = st.session_state.engine
classifier = st.session_state.classifier
scheduler = st.session_state.scheduler

# ══════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════
st.markdown("# 🧠 AI Network Intelligence Dashboard")
st.markdown(
    '<p style="color:#94a3b8; font-family: JetBrains Mono, monospace; font-size:0.85rem; margin-top:-10px;">'
    'Real-time ML-powered traffic classification & adaptive QoS scheduling</p>',
    unsafe_allow_html=True,
)

# ── Summary Status Bar ───────────────────────────────────────────────
# FIX: Moved to its own row with 3 evenly-spaced columns for full readability
total_pkts = sum(flow.packet_count for flow in engine.flows.values())
status_cols = st.columns(3)
with status_cols[0]:
    mode_str = "SMART (AI)" if scheduler.smart_mode else "DUMB (FIFO)"
    st.metric("Mode", mode_str)
with status_cols[1]:
    st.metric("Total Pkts", f"{total_pkts:,}")
with status_cols[2]:
    st.metric("Congestion", "YES" if scheduler.congestion else "NO")

st.divider()

# ── Control bar ───────────────────────────────────────────────────────
# FIX: Reduced from 7 columns to 5 — merged badges into buttons, wider ratios
ctrl_cols = st.columns([1, 1.5, 1.5, 1, 1])

with ctrl_cols[0]:
    if st.button(
        "▶ PLAY" if st.session_state.is_paused else "⏸ PAUSE",
        key="btn_pause",
        type="primary" if st.session_state.is_paused else "secondary",
        use_container_width=True,
    ):
        st.session_state.is_paused = not st.session_state.is_paused

with ctrl_cols[1]:
    if st.button(
        "🔴 CONGESTION" if not scheduler.congestion else "🟢 STOP CONGEST",
        key="btn_congestion",
        type="primary" if not scheduler.congestion else "secondary",
        use_container_width=True,
    ):
        new_state = not scheduler.congestion
        scheduler.set_congestion(new_state)
        if new_state:
            st.session_state.congestion_start_tick = st.session_state.tick
        else:
            st.session_state.congestion_start_tick = None

with ctrl_cols[2]:
    if st.button(
        "⚡ AI SCHED" if not scheduler.smart_mode else "📦 FIFO MODE",
        key="btn_mode",
        type="primary" if not scheduler.smart_mode else "secondary",
        use_container_width=True,
    ):
        scheduler.set_smart_mode(not scheduler.smart_mode)

with ctrl_cols[3]:
    st.metric("Accuracy", f"{classifier.test_accuracy:.0%}")

with ctrl_cols[4]:
    st.metric("Tick", st.session_state.tick)

st.divider()

# ══════════════════════════════════════════════════════════════════════
# MAIN LAYOUT — TWO ROWS
# Row 1: Traffic Table (left) + Network Diagram (right)
# Row 2: Bandwidth/Stats (left) + 4 QoS Charts (right, 2x2 grid)
# FIX: Replaced cramped 3-column layout with a 2-column approach
# ══════════════════════════════════════════════════════════════════════

# ── ROW 1: Traffic Table + Network Diagram ────────────────────────────
row1_left, row1_right = st.columns([1, 1.2])

with row1_left:
    st.markdown("### 📊 Traffic Monitor")
    table_placeholder = st.empty()

with row1_right:
    st.markdown("### 🌐 Network Topology")
    diagram_placeholder = st.empty()

# ── ROW 2: Bandwidth/Stats + QoS Charts ──────────────────────────────
row2_left, row2_right = st.columns([1, 1.2])

with row2_left:
    alloc_placeholder = st.empty()
    stats_placeholder = st.empty()
    info_placeholder = st.empty()

with row2_right:
    st.markdown("### 📈 QoS — DUMB vs SMART")
    chart_placeholders = {
        "throughput": st.empty(),
        "latency": st.empty(),
        "jitter": st.empty(),
        "packet_loss": st.empty(),
    }

# ══════════════════════════════════════════════════════════════════════
# LIVE UPDATE LOOP
# ══════════════════════════════════════════════════════════════════════
PRIORITY_HTML = {
    "AUDIO": "<span style='color: cyan; font-weight: bold;'>REALTIME</span>",
    "VIDEO": "<span style='color: #00FF88; font-weight: bold;'>HIGH</span>",
    "GAMING": "<span style='color: yellow; font-weight: bold;'>MEDIUM</span>",
    "DOWNLOAD": "<span style='color: #FF4444; font-weight: bold;'>LOW</span>"
}
TYPE_EMOJIS = {"VIDEO": "🎬", "AUDIO": "🎵", "GAMING": "🎮", "DOWNLOAD": "📥"}

try:
    if not st.session_state.is_paused:
        st.session_state.tick += 1
        tick = st.session_state.tick

        # ── 1. Generate traffic ───────────────────────────────────────────
        packets = engine.tick()

        # ── 2. ML prediction ──────────────────────────────────────────────
        predictions = classifier.predict_batch(packets)

        # Count predictions
        pred_counts = defaultdict(int)
        correct = 0
        for pkt, pred in zip(packets, predictions):
            pred_counts[pred] += 1
            st.session_state.prediction_counts[pred] += 1
            if pred == pkt.traffic_type:
                correct += 1
        live_accuracy = correct / len(packets) if packets else 0

        st.session_state.last_ui_state["pred_counts"] = pred_counts
        st.session_state.last_ui_state["live_accuracy"] = live_accuracy

        # ── 3. Schedule ───────────────────────────────────────────────────
        state = scheduler.schedule(packets)
        st.session_state.last_ui_state["last_state"] = state

    else:
        # Paused: freeze UI at last known values without advancing tick
        tick = st.session_state.tick
        pred_counts = st.session_state.last_ui_state["pred_counts"]
        live_accuracy = st.session_state.last_ui_state["live_accuracy"]
        state = st.session_state.last_ui_state.get("last_state", scheduler._schedule_mode([], smart=scheduler.smart_mode))

    history = scheduler.get_history()

    # ── 4. Update traffic table ───────────────────────────────────────
    with table_placeholder.container():
        stats = engine.get_stats()
        rows = []
        for t in TRAFFIC_TYPES:
            rows.append({
                "Type": f"{TYPE_EMOJIS[t]} {t}",
                "Pkts": f"{stats[t]['packet_count']:,}",
                "Tick": f"{pred_counts.get(t, 0):,}",
                "ML": f"{st.session_state.prediction_counts[t]:,}",
                "Priority": PRIORITY_HTML.get(t, "—"),
            })
        df = pd.DataFrame(rows)
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # ── 5. Update bandwidth allocation + stats ────────────────────────
    with alloc_placeholder.container():
        # FIX: Dynamic label reads from state.mode which changes per scheduler mode
        mode_label = "SMART AI MODE" if state.mode == "SMART" else "DUMB FIFO MODE"
        st.markdown(
            f'<div class="glass-panel">'
            f'<b style="color:#38bdf8; font-family: JetBrains Mono;">📡 Bandwidth — {mode_label}</b>'
            f'</div>',
            unsafe_allow_html=True,
        )
        # FIX: Using 2x2 grid instead of 4-across to give each card more width
        ac1, ac2 = st.columns(2)
        with ac1:
            st.metric("VID", f"{state.allocation_pct.get('VIDEO', 0):.0f}%")
        with ac2:
            st.metric("AUD", f"{state.allocation_pct.get('AUDIO', 0):.0f}%")
        ac3, ac4 = st.columns(2)
        with ac3:
            st.metric("GAME", f"{state.allocation_pct.get('GAMING', 0):.0f}%")
        with ac4:
            st.metric("DL", f"{state.allocation_pct.get('DOWNLOAD', 0):.0f}%")

    with stats_placeholder.container():
        sc = st.columns(3)
        sc[0].metric("Proc'd", f"{state.packets_processed:,}")
        sc[1].metric("Drop'd", f"{state.packets_dropped:,}")
        sc[2].metric("Acc", f"{live_accuracy:.0%}")

    # ── 6. Update info metrics ────────────────────────────────────────
    with info_placeholder.container():
        agg = state.aggregate_metrics
        # FIX: 2x2 grid instead of 4 across. Shortened labels to prevent clipping.
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Thru", f"{agg.throughput_mbps:.1f} Mb")
        with m2:
            st.metric("Lat", f"{agg.latency_ms:.1f} ms")
        m3, m4 = st.columns(2)
        with m3:
            st.metric("Jitter", f"{agg.jitter_ms:.1f} ms")
        with m4:
            st.metric("Loss", f"{agg.packet_loss_pct:.1f}%")

    # ── 7. Update network diagram ─────────────────────────────────────
    with diagram_placeholder.container():
        pkt_counts = {t: stats[t]["packet_count"] for t in TRAFFIC_TYPES}
        fig_net = create_network_diagram(
            packet_counts=pkt_counts,
            predictions=dict(pred_counts),
            scheduler_mode="SMART" if scheduler.smart_mode else "DUMB",
            congestion=scheduler.congestion,
            tick=tick,
        )
        st.pyplot(fig_net, use_container_width=True)
        plt.close(fig_net)

    # ── 8. Update QoS comparison charts ───────────────────────────────
    metric_configs = [
        ("throughput_mbps", "Mbps", "⬆ Throughput"),
        ("latency_ms",      "ms",   "⏱ Latency"),
        ("jitter_ms",       "ms",   "〰 Jitter"),
        ("packet_loss_pct", "%",    "📉 Pkt Loss"),
    ]

    chart_keys = ["throughput", "latency", "jitter", "packet_loss"]

    congestion_idx = None
    if st.session_state.congestion_start_tick is not None and len(history["DUMB"]) > 0:
        congestion_idx = len(history["DUMB"]) - 1 - (tick - st.session_state.congestion_start_tick)

    for (metric_attr, unit, title), key in zip(metric_configs, chart_keys):
        with chart_placeholders[key].container():
            fig_m = create_metric_charts(
                history_dumb=history["DUMB"],
                history_smart=history["SMART"],
                metric_name=metric_attr,
                ylabel=unit,
                title=title,
                congestion_start_idx=congestion_idx
            )
            st.pyplot(fig_m, use_container_width=True)
            plt.close(fig_m)

except Exception as e:
    st.error(f"Error during simulation tick: {e}")

# ── Sleep and Rerun ───────────────────────────────────────────────
if not st.session_state.is_paused:
    time.sleep(1.0)
    st.rerun()
else:
    time.sleep(0.5)
    st.rerun()
