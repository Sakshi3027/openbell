"""
OpenBell — ML Price Predictor
Trains Random Forest + Gradient Boosting ensemble
Predicts next day's closing price using technical indicators
"""

import pandas as pd
import numpy as np
import json
import os
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from datetime import datetime

FEATURES = [
    "rsi", "macd", "macd_signal", "macd_histogram",
    "bb_position", "atr", "volume_ratio",
    "daily_return", "volatility_20d",
    "momentum_7d", "momentum_30d",
    "ma7", "ma20", "ma50"
]

def prepare_features(df: pd.DataFrame) -> tuple:
    df = df.copy()
    df.loc[:, "target_return"] = df["close"].pct_change().shift(-1)
    df = df.dropna()
    available = [f for f in FEATURES if f in df.columns]
    X = df[available]
    y = df["target_return"]
    closes = df["close"]
    return X, y, available, closes

def train_model(ticker: str, df: pd.DataFrame) -> dict:
    X, y, features, closes = prepare_features(df)
    if len(X) < 100:
        return None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    closes_test = closes.iloc[len(X_train):]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    gb = GradientBoostingRegressor(n_estimators=200, random_state=42, learning_rate=0.05)

    rf.fit(X_train_scaled, y_train)
    gb.fit(X_train_scaled, y_train)

    rf_pred = rf.predict(X_test_scaled)
    gb_pred = gb.predict(X_test_scaled)
    ensemble_pred = (rf_pred * 0.5) + (gb_pred * 0.5)

    # Convert returns back to prices for MAE
    actual_prices = closes_test.values[1:] if len(closes_test) > len(ensemble_pred) else closes_test.values
    pred_prices = closes_test.values[:len(ensemble_pred)] * (1 + ensemble_pred)
    actual_prices = actual_prices[:len(pred_prices)]

    mae = mean_absolute_error(actual_prices, pred_prices)
    r2 = r2_score(y_test, ensemble_pred)
    mape = np.mean(np.abs((actual_prices - pred_prices) / actual_prices)) * 100

    # Predict next day
    latest_features = X.iloc[-1:].copy()
    latest_scaled = scaler.transform(latest_features)
    rf_next = rf.predict(latest_scaled)[0]
    gb_next = gb.predict(latest_scaled)[0]
    predicted_return = (rf_next * 0.5) + (gb_next * 0.5)

    current_price = float(df["close"].iloc[-1])
    predicted_price = current_price * (1 + predicted_return)
    predicted_change = predicted_return * 100

    os.makedirs("data/processed/models", exist_ok=True)
    with open(f"data/processed/models/{ticker}_model.pkl", "wb") as f:
        pickle.dump({"rf": rf, "gb": gb, "scaler": scaler, "features": features}, f)

    return {
        "ticker": ticker,
        "current_price": round(current_price, 2),
        "predicted_price": round(predicted_price, 2),
        "predicted_change_pct": round(predicted_change, 2),
        "mae": round(mae, 2),
        "r2": round(r2, 4),
        "mape": round(mape, 2),
        "training_samples": len(X_train),
        "features_used": len(features)
    }

def run_predictions():
    print("\n🤖 OpenBell ML Predictions")
    print("=" * 60)

    predictions = {}

    for ticker in ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT", "AMZN", "META"]:
        path = f"data/processed/{ticker}_indicators.csv"
        if not os.path.exists(path):
            print(f"  ⚠️  {ticker}: Run MapReduce first")
            continue

        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"])
        print(f"\n  Training {ticker}...")
        result = train_model(ticker, df)

        if result:
            predictions[ticker] = result
            direction = "📈" if result["predicted_change_pct"] > 0 else "📉"
            print(f"  {direction} {ticker}: ${result['current_price']} → ${result['predicted_price']} ({result['predicted_change_pct']:+.2f}%) | MAE: ${result['mae']} | R²: {result['r2']}")

    output = {
        "generated_at": datetime.now().isoformat(),
        "predictions": predictions
    }
    with open("data/processed/predictions.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\n🔔 OpenBell Pre-Market Price Predictions")
    print("=" * 70)
    print(f"{'Stock':<8} {'Current':>10} {'Predicted':>10} {'Change':>8} {'MAE':>8} {'R²':>6}")
    print("-" * 70)
    for ticker, p in predictions.items():
        arrow = "▲" if p["predicted_change_pct"] > 0 else "▼"
        print(f"{ticker:<8} ${p['current_price']:>9.2f} ${p['predicted_price']:>9.2f} {arrow}{abs(p['predicted_change_pct']):>6.2f}% ${p['mae']:>6.2f} {p['r2']:>6.4f}")

    print(f"\n✅ Predictions saved to data/processed/predictions.json")
    return predictions

if __name__ == "__main__":
    run_predictions()
