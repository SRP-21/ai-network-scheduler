"""
traffic_generator.py — Fake Traffic Machine
=============================================
Simulates four traffic types (VIDEO, AUDIO, GAMING, DOWNLOAD) with
realistic packet characteristics. No real network calls — pure Python
number generation with randomised timing profiles.
"""

import random
import time
from dataclasses import dataclass, field
from typing import List, Dict

# ─── Traffic Profiles ────────────────────────────────────────────────
# Each profile defines statistical ranges for its traffic type.
TRAFFIC_PROFILES = {
    "VIDEO": {
        "packet_size_range": (800, 1500),      # bytes — large frames
        "inter_arrival_range": (0.008, 0.025),  # seconds — steady stream
        "burst_rate_range": (5, 15),            # packets per burst
        "protocol_number": 6,                   # TCP
        "base_bitrate_mbps": 8.0,              # typical HD stream
    },
    "AUDIO": {
        "packet_size_range": (60, 200),         # bytes — small VoIP frames
        "inter_arrival_range": (0.015, 0.030),  # seconds — consistent pacing
        "burst_rate_range": (1, 4),             # low burstiness
        "protocol_number": 17,                  # UDP
        "base_bitrate_mbps": 0.3,              # typical audio call
    },
    "GAMING": {
        "packet_size_range": (40, 300),         # bytes — small state updates
        "inter_arrival_range": (0.005, 0.015),  # seconds — very fast ticks
        "burst_rate_range": (8, 25),            # highly bursty
        "protocol_number": 17,                  # UDP
        "base_bitrate_mbps": 1.5,              # typical online game
    },
    "DOWNLOAD": {
        "packet_size_range": (1200, 1500),      # bytes — max MTU bulk
        "inter_arrival_range": (0.001, 0.005),  # seconds — aggressive send
        "burst_rate_range": (20, 50),           # massive bursts
        "protocol_number": 6,                   # TCP
        "base_bitrate_mbps": 15.0,             # greedy bulk download
    },
}

TRAFFIC_TYPES = list(TRAFFIC_PROFILES.keys())


@dataclass
class Packet:
    """Represents a single simulated network packet."""
    traffic_type: str
    packet_size: int            # bytes
    inter_arrival_time: float   # seconds since last packet of this flow
    burst_rate: int             # packets in current burst window
    protocol_number: int
    timestamp: float = field(default_factory=time.time)

    def feature_vector(self) -> List[float]:
        """Return ML-ready feature array."""
        return [
            float(self.packet_size),
            self.inter_arrival_time,
            float(self.burst_rate),
            float(self.protocol_number),
        ]


class TrafficFlow:
    """Generates a continuous stream of fake packets for one traffic type."""

    def __init__(self, traffic_type: str):
        if traffic_type not in TRAFFIC_PROFILES:
            raise ValueError(f"Unknown traffic type: {traffic_type}")
        self.traffic_type = traffic_type
        self.profile = TRAFFIC_PROFILES[traffic_type]
        self.packet_count = 0
        self.last_gen_time = time.time()
        self.total_bytes = 0

    def generate_packet(self) -> Packet:
        """Create one randomised packet matching this flow's profile."""
        now = time.time()
        p = self.profile

        packet_size = random.randint(*p["packet_size_range"])
        inter_arrival = random.uniform(*p["inter_arrival_range"])
        burst_rate = random.randint(*p["burst_rate_range"])

        # Add slight noise for realism
        packet_size = max(40, int(packet_size * random.uniform(0.85, 1.15)))
        inter_arrival = max(0.001, inter_arrival * random.uniform(0.8, 1.2))

        pkt = Packet(
            traffic_type=self.traffic_type,
            packet_size=packet_size,
            inter_arrival_time=round(inter_arrival, 6),
            burst_rate=burst_rate,
            protocol_number=p["protocol_number"],
            timestamp=now,
        )

        self.packet_count += 1
        self.total_bytes += packet_size
        self.last_gen_time = now
        return pkt

    def generate_burst(self) -> List[Packet]:
        """Generate a burst of packets (realistic traffic pattern)."""
        burst_size = random.randint(*self.profile["burst_rate_range"])
        return [self.generate_packet() for _ in range(burst_size)]


class TrafficEngine:
    """
    Central engine managing all four traffic flows.
    Call tick() every second to get the latest batch of fake packets.
    """

    def __init__(self):
        self.flows: Dict[str, TrafficFlow] = {
            t: TrafficFlow(t) for t in TRAFFIC_TYPES
        }
        self.tick_count = 0

    def tick(self) -> List[Packet]:
        """
        Generate one second's worth of traffic across all flows.
        Returns a shuffled list of packets (simulating interleaved arrival).
        """
        self.tick_count += 1
        all_packets: List[Packet] = []

        for traffic_type, flow in self.flows.items():
            # Number of bursts per tick varies by type
            profile = flow.profile
            # Roughly: bitrate / avg_packet_size => packets/sec, grouped into bursts
            avg_pkt = sum(profile["packet_size_range"]) / 2
            avg_burst = sum(profile["burst_rate_range"]) / 2
            target_pkts = int((profile["base_bitrate_mbps"] * 1e6 / 8) / avg_pkt)
            num_bursts = max(1, int(target_pkts / avg_burst))

            # Add randomness: ±15 %
            num_bursts = max(1, int(num_bursts * random.uniform(0.85, 1.15)))

            for _ in range(num_bursts):
                all_packets.extend(flow.generate_burst())

        random.shuffle(all_packets)
        return all_packets

    def get_stats(self) -> Dict[str, Dict]:
        """Return per-flow cumulative statistics."""
        return {
            t: {
                "packet_count": flow.packet_count,
                "total_bytes": flow.total_bytes,
                "total_MB": round(flow.total_bytes / 1e6, 2),
            }
            for t, flow in self.flows.items()
        }


def generate_training_data(n_samples: int = 5000):
    """
    Generate labelled feature vectors for ML training.
    Returns (X, y) where X is list of feature vectors, y is list of labels.
    """
    X, y = [], []
    for _ in range(n_samples):
        traffic_type = random.choice(TRAFFIC_TYPES)
        flow = TrafficFlow(traffic_type)
        pkt = flow.generate_packet()
        X.append(pkt.feature_vector())
        y.append(traffic_type)
    return X, y
