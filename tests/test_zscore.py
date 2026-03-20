import pytest
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.zscore_detector import ZScoreDetector

def test_zscore_detector(tmp_path):
    model = ZScoreDetector(threshold=2.0)
    
    # Fake training data
    np.random.seed(42)
    X_train = np.random.normal(0, 1, (100, 8))
    model.fit(X_train)
    
    assert model.mean is not None
    assert model.std is not None
    
    # Fake inference data, one normal one anomaly
    X_test = np.vstack([
        np.zeros(8),          # should score low
        np.array([5]*8)       # should score high (5 std dev)
    ])
    
    scores = model.score(X_test)
    assert len(scores) == 2
    assert scores[0] < 0.5
    assert scores[1] > 0.5
    
    save_path = str(tmp_path / "zscore.npz")
    model.save(save_path)
    
    model2 = ZScoreDetector(threshold=2.0)
    model2.load(save_path)
    assert np.allclose(model.mean, model2.mean)
    assert np.allclose(model.std, model2.std)
