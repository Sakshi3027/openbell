#!/usr/bin/env python3
"""
OpenBell — Hadoop Streaming Reducer
Receives all rows for a ticker, computes technical indicators
Emits final signal for each stock
"""

import sys
import json
import math
from collections import defaultdict

def compute_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_sma(prices, period):
    if len(prices) < period:
        return prices[-1] if prices else 0
    return sum(prices[-period:]) / period

def compute_macd(prices):
    if len(prices) < 26:
        return 0, 0
    ema12 = prices[-1]
    ema26 = prices[-1]
    k12 = 2 / (12 + 1)
    k26 = 2 / (26 + 1)
    for p in prices[-26:]:
        ema12 = p * k12 + ema12 * (1 - k12)
        ema26 = p * k26 + ema26 * (1 - k26)
    return ema12 - ema26, ema26

def compute_bollinger(prices, period=20):
    if len(prices) < period:
        return prices[-1], prices[-1], prices[-1]
    window = prices[-period:]
    sma = sum(window) / period
    std = math.sqrt(sum((p - sma) ** 2 for p in window) / period)
    return sma + 2 * std, sma, sma - 2 * std

current_ticker = None
rows = []

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        ticker, value_json = line.split("\t", 1)
        row = json.loads(value_json)
    except (ValueError, json.JSONDecodeError):
        continue

    if ticker != current_ticker:
        if current_ticker and rows:
            # Process previous ticker
            rows.sort(key=lambda x: x["date"])
            closes = [r["close"] for r in rows]
            volumes = [r["volume"] for r in rows]

            rsi = compute_rsi(closes)
            ma7 = compute_sma(closes, 7)
            ma20 = compute_sma(closes, 20)
            ma50 = compute_sma(closes, 50)
            ma200 = compute_sma(closes, 200)
            macd, _ = compute_macd(closes)
            bb_upper, bb_mid, bb_lower = compute_bollinger(closes)
            current_price = closes[-1]
            vol_avg = sum(volumes[-20:]) / min(20, len(volumes))
            vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1.0
            momentum_7d = ((closes[-1] - closes[-8]) / closes[-8] * 100) if len(closes) >= 8 else 0
            bb_pos = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5

            # Generate signal
            score = 0
            if rsi < 30: score += 2
            elif rsi > 70: score -= 2
            if macd > 0: score += 1
            else: score -= 1
            if current_price > ma50 > ma200: score += 1
            elif current_price < ma50: score -= 1
            if bb_pos < 0.2: score += 1
            elif bb_pos > 0.8: score -= 1

            if score >= 3: signal = "STRONG BUY"
            elif score >= 1: signal = "BUY"
            elif score <= -3: signal = "STRONG SELL"
            elif score <= -1: signal = "SELL"
            else: signal = "HOLD"

            result = {
                "ticker": current_ticker,
                "close": round(current_price, 2),
                "rsi": round(rsi, 1),
                "macd": round(macd, 3),
                "ma7": round(ma7, 2),
                "ma50": round(ma50, 2),
                "ma200": round(ma200, 2),
                "bb_position": round(bb_pos, 3),
                "volume_ratio": round(vol_ratio, 2),
                "momentum_7d": round(momentum_7d, 2),
                "signal": signal,
                "signal_score": score,
                "confidence": min(95, 50 + abs(score) * 10),
                "days_processed": len(rows)
            }
            print(json.dumps(result))

        current_ticker = ticker
        rows = [row]
    else:
        rows.append(row)

# Process last ticker
if current_ticker and rows:
    rows.sort(key=lambda x: x["date"])
    closes = [r["close"] for r in rows]
    volumes = [r["volume"] for r in rows]
    rsi = compute_rsi(closes)
    ma50 = compute_sma(closes, 50)
    ma200 = compute_sma(closes, 200)
    macd, _ = compute_macd(closes)
    bb_upper, bb_mid, bb_lower = compute_bollinger(closes)
    current_price = closes[-1]
    vol_avg = sum(volumes[-20:]) / min(20, len(volumes))
    vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1.0
    momentum_7d = ((closes[-1] - closes[-8]) / closes[-8] * 100) if len(closes) >= 8 else 0
    bb_pos = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
    score = 0
    if rsi < 30: score += 2
    elif rsi > 70: score -= 2
    if macd > 0: score += 1
    else: score -= 1
    if current_price > ma50 > ma200: score += 1
    elif current_price < ma50: score -= 1
    if bb_pos < 0.2: score += 1
    elif bb_pos > 0.8: score -= 1
    if score >= 3: signal = "STRONG BUY"
    elif score >= 1: signal = "BUY"
    elif score <= -3: signal = "STRONG SELL"
    elif score <= -1: signal = "SELL"
    else: signal = "HOLD"
    result = {
        "ticker": current_ticker,
        "close": round(current_price, 2),
        "rsi": round(rsi, 1),
        "macd": round(macd, 3),
        "ma50": round(ma50, 2),
        "ma200": round(ma200, 2),
        "bb_position": round(bb_pos, 3),
        "volume_ratio": round(vol_ratio, 2),
        "momentum_7d": round(momentum_7d, 2),
        "signal": signal,
        "signal_score": score,
        "confidence": min(95, 50 + abs(score) * 10),
        "days_processed": len(rows)
    }
    print(json.dumps(result))
