# 🧠 AI Network Intelligence Simulator

> Real-time ML-powered traffic classification & adaptive QoS scheduling — pure Python, no root, any OS.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![ML](https://img.shields.io/badge/scikit--learn-Random_Forest-F7931E?logo=scikit-learn&logoColor=white)

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

That's it. Open the URL Streamlit prints (usually `http://localhost:8501`).

---

## 📁 Project Structure

| File | Purpose |
|---|---|
| `traffic_generator.py` | Fake traffic engine — simulates VIDEO, AUDIO, GAMING, DOWNLOAD packets |
| `ml_classifier.py` | Random Forest classifier trained on packet features at startup |
| `scheduler.py` | FIFO (dumb) vs AI-weighted (smart) bandwidth scheduler |
| `network_viz.py` | Matplotlib network topology diagram & QoS comparison charts |
| `app.py` | Streamlit dashboard — dark theme, live updating, three-column layout |

---

## 🎮 How to Use

1. **Watch** the dashboard auto-update every second with new traffic data
2. **Click `⚡ ENABLE AI SCHEDULER`** to switch from FIFO to AI-weighted mode
3. **Click `🔴 START CONGESTION`** to simulate a bandwidth bottleneck (10 Mbps cap)
4. **Compare** the DUMB (grey) vs SMART (blue) lines on the QoS charts

### What Happens Under Congestion?

| Mode | Behaviour |
|---|---|
| **DUMB (FIFO)** | All traffic suffers equally — latency spikes, packet loss rises uniformly |
| **SMART (AI)** | Downloads get throttled first; audio/video stay smooth with minimal impact |

---

## 🧠 ML Model Details

- **Algorithm**: Random Forest (100 trees, max depth 12)
- **Features**: `packet_size`, `inter_arrival_time`, `burst_rate`, `protocol_number`
- **Labels**: `VIDEO`, `AUDIO`, `GAMING`, `DOWNLOAD`
- **Training**: 8,000 synthetic samples generated at startup
- **Accuracy**: Typically 95%+ on test set

---

## ⚙️ Requirements

- Python 3.9+
- No root / admin privileges needed
- No real network access required
- Works on Windows, macOS, and Linux

---

## 📝 No Real Networking

This project uses **zero** real network tools. No Mininet, no `tc`, no iptables, no Open vSwitch, no Scapy, no pyshark, no real sockets. Everything is pure Python simulation.
