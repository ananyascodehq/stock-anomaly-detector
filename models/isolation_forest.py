import numpy as np
import joblib
from sklearn.ensemble import IsolationForest as SklearnIF
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models.base import AnomalyDetector

class IsolationForest(AnomalyDetector):
    def __init__(self, contamination: float = None):
        if contamination is None:
            config = Config()
            self.contamination = config.IF_CONTAMINATION
        else:
            self.contamination = contamination
            
        self.model = SklearnIF(
            n_estimators=200,
            contamination=self.contamination,
            max_samples="auto",
            random_state=42
        )
        self.fitted = False
        
    def fit(self, X: np.ndarray) -> None:
        self.model.fit(X)
        self.fitted = True
        
    def score(self, X: np.ndarray) -> np.ndarray:
        if not self.fitted:
            raise ValueError("Model is not fitted.")
            
        # decision_function returns < 0 for anomalies, > 0 for normal.
        # We invert it so > 0 is anomalous.
        raw_scores = -self.model.decision_function(X)
        
        # Apply a sigmoid so 0 (the decision boundary) maps exactly to 0.5.
        # Multiply by 5.0 to make the slope steeper around the boundary.
        normalized_scores = 1.0 / (1.0 + np.exp(-raw_scores * 5.0))
        return np.clip(normalized_scores, 0.0, 1.0)
        
    def save(self, path: str) -> None:
        if not path.endswith('.joblib'):
            path += '.joblib'
        joblib.dump(self.model, path)
        
    def load(self, path: str) -> None:
        if not path.endswith('.joblib'):
            path += '.joblib'
        self.model = joblib.load(path)
        self.fitted = True
