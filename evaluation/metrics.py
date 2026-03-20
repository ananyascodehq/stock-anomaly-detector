"""
evaluation/metrics.py

Evaluation metrics for anomaly detection models.
Computes precision, recall, F1, false positive rate, AUC-ROC,
and average detection latency against synthetic labeled datasets.
"""

import numpy as np
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models.base import AnomalyDetector


def evaluate_detector(
    detector: AnomalyDetector,
    X: np.ndarray,
    y_true: np.ndarray,
    flag_threshold: float,
) -> dict:
    """Evaluate an anomaly detector against ground-truth binary labels.

    Args:
        detector: A trained AnomalyDetector instance (must implement .score()).
        X: Feature matrix of shape (n_samples, 8).
        y_true: Binary labels array of shape (n_samples,).
                1 = anomaly, 0 = normal.
        flag_threshold: Score threshold above which a sample is flagged
                        as anomalous.

    Returns:
        Dictionary with keys:
            - precision (float)
            - recall (float)
            - f1 (float)
            - false_positive_rate (float)
            - auc_roc (float)
            - avg_detection_latency_bars (float):
                Mean number of bars between an injection index
                and the first subsequent flagged index.
    """
    # Get anomaly scores from the detector
    scores = detector.score(X)

    # Binary predictions based on threshold
    y_pred = (scores >= flag_threshold).astype(int)

    # Standard classification metrics
    precision = precision_score(y_true, y_pred, zero_division=0.0)
    recall = recall_score(y_true, y_pred, zero_division=0.0)
    f1 = f1_score(y_true, y_pred, zero_division=0.0)

    # False positive rate: FP / (FP + TN)
    fp = np.sum((y_pred == 1) & (y_true == 0))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    false_positive_rate = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    # AUC-ROC (requires at least one positive and one negative sample)
    if len(np.unique(y_true)) < 2:
        auc_roc = 0.0
    else:
        auc_roc = roc_auc_score(y_true, scores)

    # Average detection latency:
    # For each true anomaly index, find the first flagged index at or after it.
    # Latency = (first_flagged_index - anomaly_index) in bars.
    anomaly_indices = np.where(y_true == 1)[0]
    flagged_indices = np.where(y_pred == 1)[0]

    latencies = []
    for a_idx in anomaly_indices:
        # Find the first flagged index >= a_idx
        candidates = flagged_indices[flagged_indices >= a_idx]
        if len(candidates) > 0:
            latency = int(candidates[0]) - int(a_idx)
            latencies.append(latency)
        # If no flag found after this anomaly, skip (undetected)

    avg_detection_latency_bars = (
        float(np.mean(latencies)) if len(latencies) > 0 else float("inf")
    )

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "false_positive_rate": false_positive_rate,
        "auc_roc": float(auc_roc),
        "avg_detection_latency_bars": avg_detection_latency_bars,
    }
