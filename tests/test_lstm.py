import pytest
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.lstm_autoencoder import LSTMAutoencoder

def test_lstm_autoencoder(tmp_path):
    # Given limited test context, setting sequence length short provides faster tests
    model = LSTMAutoencoder(seq_length=5, n_features=8)
    
    np.random.seed(42)
    # Using 30 samples to provide adequate window slices
    X_train = np.random.normal(0, 1, (30, 8))
    model.fit(X_train)
    
    assert model.fitted
    
    X_test = np.random.normal(0, 1, (10, 8))
    scores = model.score(X_test)
    
    assert len(scores) == 10
    
    # First `seq_length - 1` elements are 0 padding due to the windowing
    for i in range(4):
        assert scores[i] == 0.0
        
    save_path = str(tmp_path / "lstm_model")
    model.save(save_path)
    
    model2 = LSTMAutoencoder(seq_length=5, n_features=8)
    model2.load(save_path)
    assert model2.fitted
