"""
OpenBell — Dagster Assets
"""

import dagster as dg
import pandas as pd
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pipeline.fetch_data import fetch_all_stocks, get_market_status
from hadoop.mapreduce.technical_indicators import run_mapreduce
from pipeline.predict import run_predictions
from pipeline.report import generate_report

@dg.asset(
    name="raw_stock_data",
    group_name="openbell",
    description="Fetches 2 years of OHLCV data for 7 stocks from Yahoo Finance",
    compute_kind="Yahoo Finance"
)
def raw_stock_data(context: dg.AssetExecutionContext) -> dg.Output[dict]:
    data = fetch_all_stocks()
    total_rows = sum(len(df) for df in data.values())
    return dg.Output(
        value={"stocks": list(data.keys()), "total_rows": int(total_rows)},
        metadata={
            "stocks_fetched": int(len(data)),
            "total_rows": int(total_rows),
            "market_status": get_market_status(),
            "tickers": ", ".join(data.keys())
        }
    )

@dg.asset(
    name="technical_indicators",
    group_name="openbell",
    description="MapReduce engine computing RSI, MACD, Bollinger Bands, ATR, Moving Averages",
    compute_kind="MapReduce",
    deps=[raw_stock_data]
)
def technical_indicators(context: dg.AssetExecutionContext) -> dg.Output[dict]:
    signals = run_mapreduce()
    # Convert numpy types to native Python
    clean_signals = json.loads(json.dumps(signals, default=str))
    signal_summary = {t: s["signal"] for t, s in clean_signals.items()}
    return dg.Output(
        value=clean_signals,
        metadata={
            "stocks_processed": int(len(clean_signals)),
            "signals": str(signal_summary),
            "buy_count": int(sum(1 for s in clean_signals.values() if "BUY" in s["signal"])),
            "sell_count": int(sum(1 for s in clean_signals.values() if "SELL" in s["signal"])),
            "hold_count": int(sum(1 for s in clean_signals.values() if s["signal"] == "HOLD"))
        }
    )

@dg.asset(
    name="ml_predictions",
    group_name="openbell",
    description="Random Forest + Gradient Boosting ensemble predicting next-day closing prices",
    compute_kind="scikit-learn",
    deps=[technical_indicators]
)
def ml_predictions(context: dg.AssetExecutionContext) -> dg.Output[dict]:
    predictions = run_predictions()
    # Convert numpy types to native Python
    clean_preds = json.loads(json.dumps(predictions, default=str))
    avg_mae = sum(float(p["mae"]) for p in clean_preds.values()) / len(clean_preds)
    return dg.Output(
        value=clean_preds,
        metadata={
            "stocks_predicted": int(len(clean_preds)),
            "avg_mae_usd": round(float(avg_mae), 2),
            "bullish": str([t for t, p in clean_preds.items() if float(p["predicted_change_pct"]) > 0]),
            "bearish": str([t for t, p in clean_preds.items() if float(p["predicted_change_pct"]) < 0])
        }
    )

@dg.asset(
    name="pre_market_report",
    group_name="openbell",
    description="Full pre-market intelligence report combining signals and predictions",
    compute_kind="Python",
    deps=[ml_predictions]
)
def pre_market_report(context: dg.AssetExecutionContext) -> dg.Output[str]:
    report = generate_report()
    lines = report.split("\n")
    return dg.Output(
        value=report,
        metadata={
            "report_lines": int(len(lines)),
            "preview": dg.MetadataValue.md(f"```\n{chr(10).join(lines[:20])}\n```")
        }
    )

@dg.asset(
    name="openbell_dashboard",
    group_name="openbell",
    description="6-panel dark-theme visual dashboard saved to docs/dashboard.png",
    compute_kind="Matplotlib",
    deps=[pre_market_report]
)
def openbell_dashboard(context: dg.AssetExecutionContext) -> dg.Output[str]:
    import matplotlib
    matplotlib.use("Agg")
    from dashboard.openbell_dashboard import build_dashboard
    build_dashboard()
    return dg.Output(
        value="docs/dashboard.png",
        metadata={
            "path": "docs/dashboard.png",
            "charts": 6
        }
    )
