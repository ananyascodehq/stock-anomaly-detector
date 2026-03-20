"""
evaluation/injector.py

Synthetic anomaly injection for creating labeled evaluation datasets.
Since there are no ground-truth labels in live market data, this module
injects known anomalies to produce a labeled set for measuring model performance.
"""

import numpy as np
import pandas as pd
from typing import Tuple


def inject_price_spike(
    df: pd.DataFrame, idx: int, magnitude: float = 5.0
) -> pd.DataFrame:
    """Multiply close[idx] by (1 + magnitude * rolling_std_at_idx).
    Label row as anomaly=1.

    Args:
        df: DataFrame with at least a 'close' column.
        idx: Integer index of the row to inject the spike into.
        magnitude: Multiplier for the rolling standard deviation.

    Returns:
        Modified DataFrame with an 'anomaly' column (1 at injected row).
    """
    df = df.copy()

    if "anomaly" not in df.columns:
        df["anomaly"] = 0

    # Compute rolling std of close prices (window=20) at the target index
    rolling_std = df["close"].rolling(window=20).std()
    std_at_idx = rolling_std.iloc[idx]

    # Fallback if std is NaN (e.g., idx < 20)
    if pd.isna(std_at_idx) or std_at_idx == 0:
        std_at_idx = df["close"].std()

    df.iloc[idx, df.columns.get_loc("close")] *= 1 + magnitude * std_at_idx
    df.iloc[idx, df.columns.get_loc("anomaly")] = 1

    return df


def inject_volume_surge(
    df: pd.DataFrame, idx: int, magnitude: float = 8.0
) -> pd.DataFrame:
    """Multiply volume[idx] by magnitude. Label row as anomaly=1.

    Args:
        df: DataFrame with at least a 'volume' column.
        idx: Integer index of the row to inject the surge into.
        magnitude: Factor to multiply the volume by.

    Returns:
        Modified DataFrame with an 'anomaly' column (1 at injected row).
    """
    df = df.copy()

    if "anomaly" not in df.columns:
        df["anomaly"] = 0

    df.iloc[idx, df.columns.get_loc("volume")] *= magnitude
    df.iloc[idx, df.columns.get_loc("anomaly")] = 1

    return df


def inject_flash_crash(
    df: pd.DataFrame, idx: int, drop_pct: float = 0.03
) -> pd.DataFrame:
    """Drop close[idx] by drop_pct fraction, recover at idx+1.
    Label both rows anomaly=1.

    Args:
        df: DataFrame with at least a 'close' column.
        idx: Integer index of the row where the crash starts.
        drop_pct: Fractional drop in price (e.g. 0.03 = 3% drop).

    Returns:
        Modified DataFrame with an 'anomaly' column (1 at both injected rows).

    Raises:
        ValueError: If idx+1 exceeds the DataFrame length.
    """
    df = df.copy()

    if idx + 1 >= len(df):
        raise ValueError(
            f"inject_flash_crash requires idx+1 < len(df). "
            f"Got idx={idx}, len(df)={len(df)}"
        )

    if "anomaly" not in df.columns:
        df["anomaly"] = 0

    original_close = df.iloc[idx, df.columns.get_loc("close")]

    # Drop at idx
    df.iloc[idx, df.columns.get_loc("close")] = original_close * (1 - drop_pct)
    df.iloc[idx, df.columns.get_loc("anomaly")] = 1

    # Recovery at idx+1 (restore to original price)
    df.iloc[idx + 1, df.columns.get_loc("close")] = original_close
    df.iloc[idx + 1, df.columns.get_loc("anomaly")] = 1

    return df


def create_labeled_dataset(
    df: pd.DataFrame,
    anomaly_rate: float = 0.02,
    seed: int = 42,
) -> Tuple[pd.DataFrame, np.ndarray]:
    """Randomly inject anomalies at anomaly_rate fraction of rows.

    Injection types are distributed roughly equally among:
    price_spike, volume_surge, and flash_crash.

    Args:
        df: Raw OHLCV DataFrame with columns
            [timestamp, open, high, low, close, volume].
        anomaly_rate: Fraction of rows to inject anomalies into.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (modified_df, binary_labels) where binary_labels
        is a numpy array of shape (n_rows,) with 1 at anomaly positions.
    """
    df = df.copy()
    rng = np.random.RandomState(seed)

    n_rows = len(df)
    n_anomalies = max(1, int(n_rows * anomaly_rate))

    # Select candidate indices — avoid the first 20 rows (rolling window warmup)
    # and the last row (flash crash needs idx+1)
    candidate_start = 20
    candidate_end = n_rows - 2  # leave room for flash_crash recovery row
    candidate_indices = list(range(candidate_start, candidate_end))

    if len(candidate_indices) < n_anomalies:
        n_anomalies = len(candidate_indices)

    selected_indices = sorted(
        rng.choice(candidate_indices, size=n_anomalies, replace=False)
    )

    # Distribute injection types equally
    injection_types = ["price_spike", "volume_surge", "flash_crash"]

    if "anomaly" not in df.columns:
        df["anomaly"] = 0

    for i, idx in enumerate(selected_indices):
        injection_type = injection_types[i % len(injection_types)]

        if injection_type == "price_spike":
            df = inject_price_spike(df, idx)
        elif injection_type == "volume_surge":
            df = inject_volume_surge(df, idx)
        elif injection_type == "flash_crash":
            df = inject_flash_crash(df, idx)

    labels = df["anomaly"].values.astype(np.int32)

    return df, labels
