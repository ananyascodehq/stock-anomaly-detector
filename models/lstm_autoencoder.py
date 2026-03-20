import numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, RepeatVector, TimeDistributed, Dense
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
import joblib
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models.base import AnomalyDetector

class LSTMAutoencoder(AnomalyDetector):
    def __init__(self, threshold: float = None, seq_length: int = 20, n_features: int = 8):
        # We now compute dynamic threshold during training using 95th percentile MSE if none provided
        self.threshold = threshold
        self.seq_length = seq_length
        self.n_features = n_features
        self.model = self._build_model()
        self.scaler = StandardScaler()
        self.fitted = False
        
    def _build_model(self):
        model = Sequential([
            LSTM(64, return_sequences=False, activation='tanh', input_shape=(self.seq_length, self.n_features)),
            RepeatVector(self.seq_length),
            LSTM(64, return_sequences=True, activation='tanh'),
            TimeDistributed(Dense(self.n_features))
        ])
        model.compile(optimizer='adam', loss='mse')
        return model
        
    def _create_sequences(self, X: np.ndarray) -> np.ndarray:
        sequences = []
        if len(X) < self.seq_length:
            raise ValueError(f"Input must have at least {self.seq_length} rows.")
        for i in range(len(X) - self.seq_length + 1):
            sequences.append(X[i:(i + self.seq_length)])
        return np.array(sequences)

    def fit(self, X: np.ndarray) -> None:
        X_scaled = self.scaler.fit_transform(X)
        X_seq = self._create_sequences(X_scaled)
        
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        self.model.fit(
            X_seq, X_seq,
            epochs=15,
            batch_size=32,
            validation_split=0.1,
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Calculate dynamic threshold based on training distribution
        train_pred = self.model.predict(X_seq, verbose=0)
        train_mse = np.mean(np.square(train_pred - X_seq), axis=(1, 2))
        
        # 95th percentile of training MSE
        if self.threshold is None:
            self.threshold = float(np.percentile(train_mse, 95))
            
        self.fitted = True
        
    def score(self, X: np.ndarray) -> np.ndarray:
        if not self.fitted:
             raise ValueError("Model is not fitted.")
             
        X_scaled = self.scaler.transform(X)
        X_seq = self._create_sequences(X_scaled)
        X_pred = self.model.predict(X_seq, verbose=0)
        
        mse_per_sample = np.mean(np.square(X_pred - X_seq), axis=(1, 2))
        
        # Normalize so threshold maps exactly to 0.5. Values above threshold -> anomalous
        # To avoid division by zero
        safe_threshold = max(self.threshold, 1e-9)
        normalized = mse_per_sample / (2.0 * safe_threshold)
        normalized = np.clip(normalized, 0.0, 1.0)
        
        # Pad beginning to match input length, as sequence processing creates a gap
        pad_len = self.seq_length - 1
        scores = np.concatenate([np.zeros(pad_len), normalized])
        return scores
        
    def save(self, path: str) -> None:
        if not path.endswith('.keras'):
            path += '.keras'
        self.model.save(path)
        # Save scaler and dynamic threshold state
        meta_data = {
            'scaler': self.scaler,
            'threshold': self.threshold
        }
        joblib.dump(meta_data, path + '.joblib')
        
    def load(self, path: str) -> None:
        if not path.endswith('.keras'):
            path += '.keras'
        self.model = load_model(path)
        
        meta_path = path + '.joblib'
        if os.path.exists(meta_path):
            meta_data = joblib.load(meta_path)
            self.scaler = meta_data.get('scaler', StandardScaler())
            self.threshold = meta_data.get('threshold', 0.05)
        self.fitted = True
