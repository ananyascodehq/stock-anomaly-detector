import pytest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.ensemble import combine

def test_ensemble_combine():
    scores = {
        "zscore": 0.6,          # Flags
        "isolation_forest": 0.4, # Does not flag
        "lstm": 0.8             # Flags
    }
    weights = {
        "zscore": 0.3,
        "isolation_forest": 0.3,
        "lstm": 0.4
    }
    
    result = combine(scores, weights=weights, min_agreeing=2)
    
    # ensemble score = 0.6*0.3 + 0.4*0.3 + 0.8*0.4 = 0.18 + 0.12 + 0.32 = 0.62
    assert abs(result["ensemble_score"] - 0.62) < 1e-5
    
    # Agreeing models > thresholds: zscore (>0.5), lstm (>0.5)
    assert "zscore" in result["agreeing_models"]
    assert "lstm" in result["agreeing_models"]
    assert "isolation_forest" not in result["agreeing_models"]
    
    assert result["is_flagged"] is True
    
    # Check negative case
    scores_low = {
        "zscore": 0.2,
        "isolation_forest": 0.2,
        "lstm": 0.2
    }
    result_low = combine(scores_low, weights=weights, min_agreeing=2)
    assert result_low["is_flagged"] is False
    assert len(result_low["agreeing_models"]) == 0
