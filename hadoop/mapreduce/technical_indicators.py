"""
OpenBell — MapReduce Technical Indicators
Computes RSI, MACD, Bollinger Bands, Moving Averages
Simulates Hadoop MapReduce pattern locally
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(prices: pd.Series):
    ema12 = prices.ewm(span=12).mean()
    ema26 = prices.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    histogram = macd - signal
    return macd, signal, histogram

def compute_bollinger_bands(prices: pd.Series, period: int = 20):
    sma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    return upper, sma, lower

def compute_atr(high, low, close, period: int = 14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# ─────────────────────────────────────────
# MAPPER — processes one stock at a time
# ─────────────────────────────────────────
def mapper(ticker: str, df: pd.DataFrame) -> dict:
    """MAP phase: compute all indicators for one stock."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # Moving averages
    df["ma7"] = close.rolling(7).mean()
    df["ma20"] = close.rolling(20).mean()
    df["ma50"] = close.rolling(50).mean()
    df["ma200"] = close.rolling(200).mean()

    # RSI
    df["rsi"] = compute_rsi(close)

    # MACD
    df["macd"], df["macd_signal"], df["macd_histogram"] = compute_macd(close)

    # Bollinger Bands
    df["bb_upper"], df["bb_middle"], df["bb_lower"] = compute_bollinger_bands(close)
    df["bb_position"] = (close - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    # ATR (volatility)
    df["atr"] = compute_atr(high, low, close)

    # Volume indicators
    df["volume_ma20"] = volume.rolling(20).mean()
    df["volume_ratio"] = volume / df["volume_ma20"]

    # Daily returns
    df["daily_return"] = close.pct_change()
    df["volatility_20d"] = df["daily_return"].rolling(20).std() * np.sqrt(252)

    # Price momentum
    df["momentum_7d"] = close.pct_change(7)
    df["momentum_30d"] = close.pct_change(30)

    return {ticker: df}

# ─────────────────────────────────────────
# REDUCER — aggregates across all stocks
# ─────────────────────────────────────────
def reducer(mapped_results: dict) -> dict:
    """REDUCE phase: combine results and generate signals."""
    signals = {}

    for ticker, df in mapped_results.items():
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # Generate trading signal
        signal_score = 0
        reasons = []

        # RSI signal
        rsi = latest["rsi"]
        if rsi < 30:
            signal_score += 2
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > 70:
            signal_score -= 2
            reasons.append(f"RSI overbought ({rsi:.1f})")

        # MACD signal
        if latest["macd"] > latest["macd_signal"] and prev["macd"] <= prev["macd_signal"]:
            signal_score += 2
            reasons.append("MACD bullish crossover")
        elif latest["macd"] < latest["macd_signal"] and prev["macd"] >= prev["macd_signal"]:
            signal_score -= 2
            reasons.append("MACD bearish crossover")

        # Bollinger Band signal
        bb_pos = latest["bb_position"]
        if bb_pos < 0.2:
            signal_score += 1
            reasons.append(f"Near lower BB ({bb_pos:.2f})")
        elif bb_pos > 0.8:
            signal_score -= 1
            reasons.append(f"Near upper BB ({bb_pos:.2f})")

        # Moving average signal
        if latest["close"] > latest["ma50"] > latest["ma200"]:
            signal_score += 1
            reasons.append("Above MA50 and MA200")
        elif latest["close"] < latest["ma50"] < latest["ma200"]:
            signal_score -= 1
            reasons.append("Below MA50 and MA200")

        # Volume confirmation
        if latest["volume_ratio"] > 1.5:
            reasons.append(f"High volume ({latest['volume_ratio']:.1f}x avg)")

        # Determine signal
        if signal_score >= 3:
            signal = "STRONG BUY"
        elif signal_score >= 1:
            signal = "BUY"
        elif signal_score <= -3:
            signal = "STRONG SELL"
        elif signal_score <= -1:
            signal = "SELL"
        else:
            signal = "HOLD"

        confidence = min(95, 50 + abs(signal_score) * 10 + (5 if latest["volume_ratio"] > 1.5 else 0))

        signals[ticker] = {
            "ticker": ticker,
            "date": str(latest["date"])[:10],
            "close": round(float(latest["close"]), 2),
            "signal": signal,
            "signal_score": signal_score,
            "confidence": confidence,
            "rsi": round(float(rsi), 1),
            "macd": round(float(latest["macd"]), 3),
            "bb_position": round(float(bb_pos), 3),
            "ma50": round(float(latest["ma50"]), 2),
            "ma200": round(float(latest["ma200"]), 2),
            "volatility_20d": round(float(latest["volatility_20d"]), 3),
            "momentum_7d": round(float(latest["momentum_7d"]) * 100, 2),
            "momentum_30d": round(float(latest["momentum_30d"]) * 100, 2),
            "volume_ratio": round(float(latest["volume_ratio"]), 2),
            "reasons": reasons
        }

    return signals

def run_mapreduce():
    """Run the full MapReduce pipeline."""
    print("\n⚡ OpenBell MapReduce — Technical Indicators")
    print("=" * 50)

    # Load raw data
    tickers = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT", "AMZN", "META"]
    raw_data = {}
    for ticker in tickers:
        path = f"data/raw/{ticker}.csv"
        if os.path.exists(path):
            df = pd.read_csv(path)
            df["date"] = pd.to_datetime(df["date"])
            raw_data[ticker] = df
            print(f"  📂 Loaded {ticker}: {len(df)} rows")

    # MAP phase
    print("\n🗺️  MAP phase: computing indicators...")
    mapped = {}
    for ticker, df in raw_data.items():
        result = mapper(ticker, df.copy())
        mapped.update(result)
        print(f"  ✅ {ticker}: RSI={df['close'].pipe(compute_rsi).iloc[-1]:.1f}")

    # REDUCE phase
    print("\n🔀 REDUCE phase: generating signals...")
    signals = reducer(mapped)

    # Save results
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/signals.json", "w") as f:
        json.dump(signals, f, indent=2)

    # Save processed DFs
    for ticker, df in mapped.items():
        df.to_csv(f"data/processed/{ticker}_indicators.csv", index=False)

    # Print summary
    print("\n🔔 OpenBell Pre-Market Signals")
    print("=" * 60)
    print(f"{'Stock':<8} {'Price':>8} {'Signal':<14} {'Conf':>6} {'RSI':>6} {'Mom7d':>7}")
    print("-" * 60)
    for ticker, sig in signals.items():
        print(f"{ticker:<8} ${sig['close']:>7.2f} {sig['signal']:<14} {sig['confidence']:>5}% {sig['rsi']:>6.1f} {sig['momentum_7d']:>6.1f}%")

    print(f"\n✅ MapReduce complete! Signals saved to data/processed/signals.json")
    return signals

if __name__ == "__main__":
    run_mapreduce()
