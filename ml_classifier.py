"""
ml_classifier.py — Traffic Brain (Random Forest)
==================================================
Trains a Random Forest classifier on synthetic packet features at startup.
Provides real-time prediction on live traffic every tick.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from typing import List, Tuple, Dict

from traffic_generator import generate_training_data, Packet, TRAFFIC_TYPES


class TrafficClassifier:
    """
    Random Forest model that classifies packets into
    VIDEO / AUDIO / GAMING / DOWNLOAD based on four features:
      - packet_size
      - inter_arrival_time
      - burst_rate
      - protocol_number
    """

    FEATURE_NAMES = ["packet_size", "inter_arrival_time", "burst_rate", "protocol_number"]

    def __init__(self, n_estimators: int = 100, n_training_samples: int = 8000):
        self.n_estimators = n_estimators
        self.n_training_samples = n_training_samples
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=12,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
        )
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(TRAFFIC_TYPES)
        self.is_trained = False
        self.train_accuracy = 0.0
        self.test_accuracy = 0.0
        self.feature_importances: Dict[str, float] = {}

    def train(self) -> Dict[str, float]:
        """
        Generate synthetic data and train the model.
        Returns a dict with train/test accuracy and feature importances.
        """
        print("[ML] Generating training data …")
        X_raw, y_raw = generate_training_data(self.n_training_samples)

        X = np.array(X_raw, dtype=np.float32)
        y = self.label_encoder.transform(y_raw)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"[ML] Training Random Forest ({self.n_estimators} trees) on {len(X_train)} samples …")
        self.model.fit(X_train, y_train)
        self.is_trained = True

        self.train_accuracy = accuracy_score(y_train, self.model.predict(X_train))
        self.test_accuracy = accuracy_score(y_test, self.model.predict(X_test))

        self.feature_importances = {
            name: round(float(imp), 4)
            for name, imp in zip(self.FEATURE_NAMES, self.model.feature_importances_)
        }

        metrics = {
            "train_accuracy": round(self.train_accuracy, 4),
            "test_accuracy": round(self.test_accuracy, 4),
            "feature_importances": self.feature_importances,
            "n_training_samples": self.n_training_samples,
        }
        print(f"[ML] Training complete — test accuracy: {self.test_accuracy:.2%}")
        return metrics

    def predict_packet(self, packet: Packet) -> str:
        """Classify a single packet. Returns label string."""
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")
        features = np.array([packet.feature_vector()], dtype=np.float32)
        pred_idx = self.model.predict(features)[0]
        return self.label_encoder.inverse_transform([pred_idx])[0]

    def predict_batch(self, packets: List[Packet]) -> List[str]:
        """Classify a batch of packets. Returns list of label strings."""
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")
        if not packets:
            return []
        features = np.array([p.feature_vector() for p in packets], dtype=np.float32)
        pred_indices = self.model.predict(features)
        return list(self.label_encoder.inverse_transform(pred_indices))

    def predict_with_confidence(self, packet: Packet) -> Tuple[str, float]:
        """Classify a packet and return (label, confidence)."""
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")
        features = np.array([packet.feature_vector()], dtype=np.float32)
        proba = self.model.predict_proba(features)[0]
        pred_idx = np.argmax(proba)
        label = self.label_encoder.inverse_transform([pred_idx])[0]
        return label, float(proba[pred_idx])

    def get_confusion_summary(self, packets: List[Packet]) -> Dict[str, Dict[str, int]]:
        """
        Compare true labels vs predictions for a batch.
        Returns {true_label: {predicted_label: count}}.
        """
        predictions = self.predict_batch(packets)
        summary: Dict[str, Dict[str, int]] = {t: {t2: 0 for t2 in TRAFFIC_TYPES} for t in TRAFFIC_TYPES}
        for pkt, pred in zip(packets, predictions):
            summary[pkt.traffic_type][pred] += 1
        return summary
