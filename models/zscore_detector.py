import numpy as np
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models.base import AnomalyDetector

class ZScoreDetector(AnomalyDetector):
    def __init__(self, threshold: float = None):
        if threshold is None:
            config = Config()
            self.threshold = config.ZSCORE_THRESHOLD
        else:
            self.threshold = threshold
        self.mean = None
        self.std = None
        
    def fit(self, X: np.ndarray) -> None:
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0)
        # Avoid zero division
        self.std[self.std == 0] = 1e-9
        
    def score(self, X: np.ndarray) -> np.ndarray:
        if self.mean is None or self.std is None:
            raise ValueError("Model is not fitted.")
            
        z_scores_all_features = np.abs(X - self.mean) / self.std
        raw_z = np.max(z_scores_all_features, axis=1)
        
        # score = sigmoid(raw_z - ZSCORE_THRESHOLD)
        score = 1.0 / (1.0 + np.exp(-(raw_z - self.threshold)))
        return score
        
    def save(self, path: str) -> None:
        if not path.endswith('.npz'):
            path += '.npz'
        np.savez(path, mean=self.mean, std=self.std)
        
    def load(self, path: str) -> None:
        if not path.endswith('.npz'):
            path += '.npz'
        data = np.load(path)
        self.mean = data['mean']
        self.std = data['std']
