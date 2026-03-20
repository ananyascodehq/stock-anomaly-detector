import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from features.engineer import compute_features

def test_compute_features_basic():
    np.random.seed(42)
    n = 60
    df = pd.DataFrame({
        'timestamp': pd.date_range("2020-01-01", periods=n, freq="T"),
        'open': np.random.uniform(100, 150, n),
        'high': np.random.uniform(150, 200, n),
        'low': np.random.uniform(50, 100, n),
        'close': np.random.uniform(100, 150, n),
        'volume': np.random.uniform(1000, 5000, n),
    })
    
    features = compute_features(df, window=20, rsi_period=14)
    
    assert not features.empty
    
    expected_cols = [
        'log_return', 'rolling_mean_return', 'rolling_std_return',
        'volume_zscore', 'price_volume_divergence', 'rsi_14',
        'vwap_deviation', 'spread_proxy'
    ]
    assert list(features.columns) == expected_cols
    
    for col in expected_cols:
        assert features[col].dtype == 'float64'
        
    assert features.isnull().sum().sum() == 0

def test_compute_features_too_short():
    df = pd.DataFrame({
        'timestamp': pd.date_range("2020-01-01", periods=10, freq="T"),
        'open': [100]*10,
        'high': [100]*10,
        'low': [100]*10,
        'close': [100]*10,
        'volume': [1000]*10,
    })
    
    with pytest.raises(ValueError):
        compute_features(df, window=20, rsi_period=14)
