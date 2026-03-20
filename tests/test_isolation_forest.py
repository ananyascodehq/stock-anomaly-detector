import pytest
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.isolation_forest import IsolationForest

def test_isolation_forest(tmp_path):
    model = IsolationForest(contamination=0.01)
    
    np.random.seed(42)
    X_train = np.random.normal(0, 1, (100, 8))
    model.fit(X_train)
    
    assert model.fitted
    
    X_test = np.vstack([
        np.zeros(8),          
        np.array([10]*8)       
    ])
    
    scores = model.score(X_test)
    assert len(scores) == 2
    # Ensure scores are clipped
    assert scores[0] >= 0.0 and scores[0] <= 1.0
    assert scores[1] >= 0.0 and scores[1] <= 1.0
    
    save_path = str(tmp_path / "if_model.joblib")
    model.save(save_path)
    
    model2 = IsolationForest()
    model2.load(save_path)
    assert model2.fitted
