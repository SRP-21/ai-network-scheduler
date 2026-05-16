"""
scheduler.py — Fake Network Scheduler
=======================================
Two scheduling modes:
  DUMB  (FIFO) — all traffic gets equal share, suffers equally under congestion.
  SMART (AI)   — priority-weighted allocation: audio 40 %, video 35 %, gaming 15 %, download 10 %.
                 Under congestion, downloads get throttled first.

Computes simulated QoS metrics: throughput, latency, jitter, packet loss.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Deque
from collections import deque

from traffic_generator import Packet, TRAFFIC_TYPES

# ─── Constants ────────────────────────────────────────────────────────
NORMAL_BANDWIDTH_MBPS = 100.0   # plenty of headroom
CONGESTED_BANDWIDTH_MBPS = 10.0 # hard cap during congestion

SMART_WEIGHTS: Dict[str, float] = {
    "AUDIO":    0.40,
    "VIDEO":    0.35,
    "GAMING":   0.15,
    "DOWNLOAD": 0.10,
}

# Baseline latency ranges per type (ms)
BASE_LATENCY: Dict[str, tuple] = {
    "VIDEO":    (5, 15),
    "AUDIO":    (3, 10),
    "GAMING":   (2, 8),
    "DOWNLOAD": (10, 30),
}


@dataclass
class QoSMetrics:
    """Quality-of-Service metrics for one tick."""
    throughput_mbps: float = 0.0
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    packet_loss_pct: float = 0.0


@dataclass
class SchedulerState:
    """Snapshot of the scheduler at a given tick."""
    mode: str  # "DUMB" or "SMART"
    congestion: bool
    bandwidth_cap_mbps: float
    per_type_metrics: Dict[str, QoSMetrics] = field(default_factory=dict)
    aggregate_metrics: QoSMetrics = field(default_factory=QoSMetrics)
    allocation_pct: Dict[str, float] = field(default_factory=dict)
    packets_processed: int = 0
    packets_dropped: int = 0


class NetworkScheduler:
    """
    Simulates FIFO (dumb) and priority-weighted (smart) packet scheduling
    with congestion effects on throughput, latency, jitter, and packet loss.
    """

    def __init__(self):
        self.smart_mode = False
        self.congestion = False
        self.history_dumb: Deque[QoSMetrics] = deque(maxlen=120)
        self.history_smart: Deque[QoSMetrics] = deque(maxlen=120)
        self._prev_latency: Dict[str, float] = {t: 0.0 for t in TRAFFIC_TYPES}

    @property
    def bandwidth_cap(self) -> float:
        return CONGESTED_BANDWIDTH_MBPS if self.congestion else NORMAL_BANDWIDTH_MBPS

    def set_smart_mode(self, enabled: bool):
        self.smart_mode = enabled

    def set_congestion(self, enabled: bool):
        self.congestion = enabled

    # ── Core scheduling logic ─────────────────────────────────────────
    def schedule(self, packets: List[Packet]) -> SchedulerState:
        """
        Process a tick's worth of packets through BOTH schedulers
        and return the active mode's state.
        Also records metrics for both modes for comparative graphing.
        """
        dumb_state = self._schedule_mode(packets, smart=False)
        smart_state = self._schedule_mode(packets, smart=True)

        self.history_dumb.append(dumb_state.aggregate_metrics)
        self.history_smart.append(smart_state.aggregate_metrics)

        return smart_state if self.smart_mode else dumb_state

    def _schedule_mode(self, packets: List[Packet], smart: bool) -> SchedulerState:
        """Run one scheduling pass (DUMB or SMART)."""
        cap = self.bandwidth_cap
        mode = "SMART" if smart else "DUMB"

        # Group packets by type
        by_type: Dict[str, List[Packet]] = {t: [] for t in TRAFFIC_TYPES}
        for pkt in packets:
            by_type[pkt.traffic_type].append(pkt)

        # Calculate total demand (bytes → Mbps in 1 sec window)
        demand: Dict[str, float] = {}
        for t in TRAFFIC_TYPES:
            total_bytes = sum(p.packet_size for p in by_type[t])
            demand[t] = (total_bytes * 8) / 1e6  # Mbps

        total_demand = sum(demand.values()) or 1e-9

        # Allocate bandwidth
        if smart:
            allocation = self._smart_allocate(demand, cap)
        else:
            allocation = self._dumb_allocate(demand, cap)

        # Compute per-type QoS
        per_type_metrics: Dict[str, QoSMetrics] = {}
        total_throughput = 0.0
        total_latency = 0.0
        total_jitter = 0.0
        total_loss = 0.0
        total_processed = 0
        total_dropped = 0

        for t in TRAFFIC_TYPES:
            alloc_mbps = allocation[t]
            demand_mbps = demand[t] or 1e-9
            utilisation = min(1.0, alloc_mbps / demand_mbps)

            # Throughput: what actually gets through
            throughput = demand_mbps * utilisation

            # Packet loss: proportional to unmet demand
            loss_pct = max(0.0, (1.0 - utilisation)) * 100.0
            # Add slight randomness
            loss_pct = max(0.0, loss_pct + random.uniform(-2, 2))
            loss_pct = min(100.0, loss_pct)

            # Latency: increases under congestion
            base_lat = random.uniform(*BASE_LATENCY[t])
            congestion_factor = 1.0
            if self.congestion:
                if smart:
                    # Smart mode: priority types barely impacted
                    weight = SMART_WEIGHTS.get(t, 0.25)
                    congestion_factor = 1.0 + (1.0 - weight) * random.uniform(3, 8)
                else:
                    # Dumb mode: everyone suffers
                    congestion_factor = 1.0 + random.uniform(5, 15)

            latency = base_lat * congestion_factor

            # Jitter: variance from previous latency
            prev = self._prev_latency.get(t, latency)
            jitter = abs(latency - prev) * random.uniform(0.3, 1.0)
            self._prev_latency[t] = latency

            n_pkts = len(by_type[t])
            n_dropped = int(n_pkts * (loss_pct / 100.0))
            n_processed = n_pkts - n_dropped

            per_type_metrics[t] = QoSMetrics(
                throughput_mbps=round(throughput, 3),
                latency_ms=round(latency, 2),
                jitter_ms=round(jitter, 2),
                packet_loss_pct=round(loss_pct, 2),
            )

            total_throughput += throughput
            total_latency += latency
            total_jitter += jitter
            total_loss += loss_pct
            total_processed += n_processed
            total_dropped += n_dropped

        n_types = len(TRAFFIC_TYPES)
        alloc_pct = {
            t: round(allocation[t] / (cap or 1e-9) * 100, 1) for t in TRAFFIC_TYPES
        }

        return SchedulerState(
            mode=mode,
            congestion=self.congestion,
            bandwidth_cap_mbps=cap,
            per_type_metrics=per_type_metrics,
            aggregate_metrics=QoSMetrics(
                throughput_mbps=round(total_throughput, 3),
                latency_ms=round(total_latency / n_types, 2),
                jitter_ms=round(total_jitter / n_types, 2),
                packet_loss_pct=round(total_loss / n_types, 2),
            ),
            allocation_pct=alloc_pct,
            packets_processed=total_processed,
            packets_dropped=total_dropped,
        )

    def _dumb_allocate(self, demand: Dict[str, float], cap: float) -> Dict[str, float]:
        """FIFO: split bandwidth equally among active flows."""
        active = [t for t in TRAFFIC_TYPES if demand[t] > 0]
        if not active:
            return {t: 0.0 for t in TRAFFIC_TYPES}
        share = cap / len(active)
        return {t: (share if demand[t] > 0 else 0.0) for t in TRAFFIC_TYPES}

    def _smart_allocate(self, demand: Dict[str, float], cap: float) -> Dict[str, float]:
        """AI-weighted: allocate by SMART_WEIGHTS, redistribute surplus."""
        allocation = {t: cap * SMART_WEIGHTS[t] for t in TRAFFIC_TYPES}

        # If a type doesn't need its full share, redistribute surplus
        surplus = 0.0
        deficit_types = []
        for t in TRAFFIC_TYPES:
            if demand[t] < allocation[t]:
                surplus += allocation[t] - demand[t]
                allocation[t] = demand[t]
            else:
                deficit_types.append(t)

        # Distribute surplus proportionally to deficit types
        if deficit_types and surplus > 0:
            total_deficit_weight = sum(SMART_WEIGHTS[t] for t in deficit_types)
            for t in deficit_types:
                extra = surplus * (SMART_WEIGHTS[t] / total_deficit_weight)
                allocation[t] += extra

        return allocation

    def get_history(self) -> Dict[str, List[QoSMetrics]]:
        """Return metric history for both modes."""
        return {
            "DUMB": list(self.history_dumb),
            "SMART": list(self.history_smart),
        }
