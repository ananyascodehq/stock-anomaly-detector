import os
import sys
from typing import Dict

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def combine(scores: Dict[str, float], weights: Dict[str, float] = None, min_agreeing: int = None) -> dict:
    """
    Input:
        scores:        {"zscore": float, "isolation_forest": float, "lstm": float}
        weights:       Config.ENSEMBLE_WEIGHTS
        min_agreeing:  Config.ENSEMBLE_MIN_AGREEING_MODELS

    Returns:
        {
            "ensemble_score":  float,   # weighted average of all 3 scores
            "is_flagged":      bool,    # True if ensemble_score > 0.5 AND len(agreeing) >= min_agreeing
            "agreeing_models": list,    # model names that individually crossed their threshold
            "scores":          dict     # passes through raw scores
        }
    """
    config = Config()
    if weights is None:
        weights = config.ENSEMBLE_WEIGHTS
    if min_agreeing is None:
        min_agreeing = config.ENSEMBLE_MIN_AGREEING_MODELS
        
    thresholds = {
        "zscore": 0.5,
        "isolation_forest": 0.5,
        "lstm": 0.5
    }
    
    ensemble_score = sum(scores.get(m, 0.0) * weights.get(m, 0.0) for m in scores)
    
    agreeing = [m for m in scores if scores.get(m, 0.0) > thresholds.get(m, 0.5)]
    is_flagged = (ensemble_score > 0.5) and (len(agreeing) >= min_agreeing)
    
    return {
        "ensemble_score": float(ensemble_score),
        "is_flagged": bool(is_flagged),
        "agreeing_models": agreeing,
        "scores": scores
    }
