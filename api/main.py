"""
OpenBell — FastAPI Backend
Serves pre-market intelligence data from latest pipeline run
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import os
from datetime import datetime
import pytz

ET = pytz.timezone("America/New_York")

app = FastAPI(
    title="OpenBell API",
    description="Pre-market stock intelligence platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_market_status():
    now = datetime.now(ET)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    pre_market = now.replace(hour=4, minute=0, second=0, microsecond=0)
    is_weekend = now.weekday() >= 5
    if is_weekend:
        return "WEEKEND"
    elif now < pre_market:
        return "CLOSED"
    elif now < market_open:
        return "PRE-MARKET"
    elif now <= market_close:
        return "OPEN"
    else:
        return "AFTER-HOURS"

def load_signals():
    path = "data/processed/signals.json"
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)

def load_predictions():
    path = "data/processed/predictions.json"
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)
        return data.get("predictions", {})

def load_report():
    path = "data/processed/reports/latest_report.json"
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)

@app.get("/")
def root():
    return {
        "name": "OpenBell",
        "tagline": "Pre-market stock intelligence — rings before the market does",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/market-status")
def market_status():
    now = datetime.now(ET)
    return {
        "status": get_market_status(),
        "time_et": now.strftime("%Y-%m-%d %H:%M:%S ET"),
        "next_open": "Monday 9:30 AM ET" if now.weekday() >= 4 else "Tomorrow 9:30 AM ET"
    }

@app.get("/signals")
def signals():
    data = load_signals()
    predictions = load_predictions()
    now = datetime.now(ET)

    result = []
    for ticker, sig in data.items():
        pred = predictions.get(ticker, {})
        result.append({
            "ticker": ticker,
            "close": sig.get("close", 0),
            "signal": sig.get("signal", "HOLD"),
            "signal_score": sig.get("signal_score", 0),
            "confidence": sig.get("confidence", 50),
            "rsi": sig.get("rsi", 50),
            "macd": sig.get("macd", 0),
            "bb_position": sig.get("bb_position", 0.5),
            "momentum_7d": sig.get("momentum_7d", 0),
            "volume_ratio": sig.get("volume_ratio", 1),
            "predicted_price": pred.get("predicted_price", 0),
            "predicted_change_pct": pred.get("predicted_change_pct", 0),
            "mae": pred.get("mae", 0),
        })

    return {
        "generated_at": now.isoformat(),
        "market_status": get_market_status(),
        "total_stocks": len(result),
        "stocks": result
    }

@app.get("/summary")
def summary():
    data = load_signals()
    now = datetime.now(ET)

    buy = [t for t, s in data.items() if "BUY" in s.get("signal", "")]
    sell = [t for t, s in data.items() if "SELL" in s.get("signal", "")]
    hold = [t for t, s in data.items() if s.get("signal", "") == "HOLD"]

    high_vol = [t for t, s in data.items() if s.get("volatility_20d", 0) > 0.4]

    return {
        "generated_at": now.isoformat(),
        "market_status": get_market_status(),
        "buy": buy,
        "sell": sell,
        "hold": hold,
        "high_volatility_alert": high_vol,
        "total_tracked": len(data)
    }

@app.get("/stock/{ticker}")
def stock(ticker: str):
    ticker = ticker.upper()
    signals = load_signals()
    predictions = load_predictions()

    if ticker not in signals:
        return {"error": f"{ticker} not found"}

    sig = signals[ticker]
    pred = predictions.get(ticker, {})

    return {
        "ticker": ticker,
        "close": sig.get("close", 0),
        "signal": sig.get("signal", "HOLD"),
        "signal_score": sig.get("signal_score", 0),
        "confidence": sig.get("confidence", 50),
        "technical": {
            "rsi": sig.get("rsi", 50),
            "macd": sig.get("macd", 0),
            "bb_position": sig.get("bb_position", 0.5),
            "ma50": sig.get("ma50", 0),
            "ma200": sig.get("ma200", 0),
            "momentum_7d": sig.get("momentum_7d", 0),
            "momentum_30d": sig.get("momentum_30d", 0),
            "volume_ratio": sig.get("volume_ratio", 1),
            "volatility_20d": sig.get("volatility_20d", 0)
        },
        "prediction": {
            "predicted_price": pred.get("predicted_price", 0),
            "predicted_change_pct": pred.get("predicted_change_pct", 0),
            "mae": pred.get("mae", 0),
            "r2": pred.get("r2", 0)
        },
        "reasons": sig.get("reasons", [])
    }

@app.get("/pipeline-info")
def pipeline_info():
    return {
        "pipeline": "OpenBell Pre-Market Intelligence",
        "stages": [
            {"step": 1, "name": "Data Fetch", "description": "Yahoo Finance API → 501 days OHLCV per stock", "tech": "yfinance"},
            {"step": 2, "name": "HDFS Ingestion", "description": "Raw CSVs uploaded to Hadoop HDFS", "tech": "Hadoop 3.2.1"},
            {"step": 3, "name": "MapReduce", "description": "7 parallel mapper tasks compute RSI, MACD, Bollinger Bands, ATR", "tech": "Hadoop Streaming"},
            {"step": 4, "name": "ML Predictions", "description": "Random Forest + Gradient Boosting ensemble predicts next-day price", "tech": "scikit-learn"},
            {"step": 5, "name": "Pre-Market Report", "description": "BUY/SELL/HOLD signals with confidence scores", "tech": "Python"},
            {"step": 6, "name": "Dashboard", "description": "6-panel visual analytics", "tech": "Matplotlib"}
        ],
        "schedule": "Every trading day at 8:00 AM ET",
        "stocks_tracked": ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT", "AMZN", "META"],
        "hadoop_cluster": {
            "namenode": "HDFS master",
            "datanode": "HDFS storage",
            "resourcemanager": "YARN",
            "nodemanager": "Task execution"
        }
    }
