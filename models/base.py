from abc import ABC, abstractmethod
import numpy as np

class AnomalyDetector(ABC):
    @abstractmethod
    def fit(self, X: np.ndarray) -> None:
        """Train on historical feature matrix. X shape: (n_samples, 8)."""
        pass

    @abstractmethod
    def score(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores in [0.0, 1.0] for each row. Shape: (n_samples,)."""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Persist model to disk."""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Load model from disk."""
        pass
