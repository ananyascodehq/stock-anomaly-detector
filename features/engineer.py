import pandas as pd
import numpy as np

def compute_features(df: pd.DataFrame, window: int = 20, rsi_period: int = 14) -> pd.DataFrame:
    """
    Input:  DataFrame with columns [timestamp, open, high, low, close, volume]
            sorted ascending by timestamp.
    Output: DataFrame with 8 feature columns. Rows with insufficient history
            (first `window` rows) are dropped. Do not forward-fill or impute.
    Raises: ValueError if input has fewer than (window + rsi_period) rows.
    """
    if len(df) < (window + rsi_period):
        raise ValueError(f"Input requires at least {window + rsi_period} rows.")
        
    features = pd.DataFrame(index=df.index)
    close = df['close']
    volume = df['volume']
    high = df['high']
    low = df['low']
    
    # 1. log_return
    features['log_return'] = np.log(close / close.shift(1))
    
    # 2. rolling_mean_return
    features['rolling_mean_return'] = features['log_return'].rolling(window=window).mean()
    
    # 3. rolling_std_return
    features['rolling_std_return'] = features['log_return'].rolling(window=window).std()
    
    # 4. volume_zscore
    vol_mean = volume.rolling(window=window).mean()
    vol_std = volume.rolling(window=window).std().replace(0.0, 1e-9)
    features['volume_zscore'] = (volume - vol_mean) / vol_std
    
    # 5. price_volume_divergence
    features['price_volume_divergence'] = features['log_return'] / (features['volume_zscore'] + 1e-9)
    
    # 6. rsi_14
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(alpha=1/rsi_period, adjust=False).mean()
    ema_down = down.ewm(alpha=1/rsi_period, adjust=False).mean()
    rs = ema_up / ema_down
    features['rsi_14'] = 100 - (100 / (1 + rs))
    features.loc[ema_down == 0, 'rsi_14'] = 100
    
    # 7. vwap_deviation
    rolling_vp = (close * volume).rolling(window=window).sum()
    rolling_v = volume.rolling(window=window).sum().replace(0.0, 1e-9)
    vwap = rolling_vp / rolling_v
    features['vwap_deviation'] = (close - vwap) / vwap
    
    # 8. spread_proxy
    features['spread_proxy'] = (high - low) / close
    
    # Select specific columns in designated order
    ordered_cols = [
        'log_return', 'rolling_mean_return', 'rolling_std_return',
        'volume_zscore', 'price_volume_divergence', 'rsi_14',
        'vwap_deviation', 'spread_proxy'
    ]
    features = features[ordered_cols]
    
    # Drop rows with insufficient history
    features = features.dropna()
    
    if features.isnull().sum().sum() > 0:
        raise ValueError("NaNs present after dropping initial window.")
        
    features = features.astype('float64')
    return features
