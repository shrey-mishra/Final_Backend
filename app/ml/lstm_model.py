import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import ccxt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_historical_data(symbol="BTC/USDT", timeframe="1h", limit=1000):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df[["close"]]

def prepare_data(data, look_back=60):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    X, y = [], []
    for i in range(look_back, len(scaled_data)):
        X.append(scaled_data[i-look_back:i, 0])
        y.append(scaled_data[i, 0])
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    return X, y, scaler

def build_lstm_model(look_back=60):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(look_back, 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model

def predict_next_price(symbol="BTC/USDT", look_back=60):
    try:
        # Fetch historical data
        df = fetch_historical_data(symbol)
        if len(df) < look_back:
            raise ValueError("Not enough data to make a prediction")
        
        # Prepare data
        X, y, scaler = prepare_data(df[["close"]], look_back)
        
        # Split data (80% train, 20% test)
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        # Build and train model
        model = build_lstm_model(look_back)
        model.fit(X_train, y_train, epochs=5, batch_size=32, verbose=0)
        
        # Predict next price
        last_sequence = X[-1:]
        predicted_scaled = model.predict(last_sequence, verbose=0)
        predicted_price = scaler.inverse_transform(predicted_scaled)[0][0]
        
        # Get current price
        current_price = df["close"].iloc[-1]
        
        return current_price, predicted_price
    except Exception as e:
        logger.error(f"Error in predict_next_price: {str(e)}")
        raise