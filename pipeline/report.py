"""
OpenBell — Pre-Market Report Generator
Combines MapReduce signals + ML predictions into a morning briefing
Runs automatically before market open at 8:30 AM ET
"""

import json
import os
from datetime import datetime
import pytz

ET = pytz.timezone("America/New_York")

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
        return "PRE-MARKET 🔔"
    elif now <= market_close:
        return "OPEN 🟢"
    else:
        return "AFTER-HOURS 🌙"

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

def signal_emoji(signal: str) -> str:
    return {
        "STRONG BUY": "🟢🟢",
        "BUY": "🟢",
        "HOLD": "🟡",
        "SELL": "🔴",
        "STRONG SELL": "🔴🔴"
    }.get(signal, "⚪")

def generate_report():
    now = datetime.now(ET)
    signals = load_signals()
    predictions = load_predictions()

    tickers = list(signals.keys())

    report_lines = []
    report_lines.append("=" * 65)
    report_lines.append("🔔  O P E N B E L L  —  P R E - M A R K E T  I N T E L L I G E N C E")
    report_lines.append("=" * 65)
    report_lines.append(f"  Generated : {now.strftime('%A, %B %d, %Y at %I:%M %p ET')}")
    report_lines.append(f"  Market    : {get_market_status()}")
    report_lines.append(f"  Coverage  : {len(tickers)} stocks tracked")
    report_lines.append("=" * 65)

    # Action summary
    buy_stocks = [t for t in tickers if "BUY" in signals[t]["signal"]]
    sell_stocks = [t for t in tickers if "SELL" in signals[t]["signal"]]
    hold_stocks = [t for t in tickers if signals[t]["signal"] == "HOLD"]

    report_lines.append("\n📊 MORNING SUMMARY")
    report_lines.append(f"  🟢 BUY signals  : {len(buy_stocks)} stocks {buy_stocks}")
    report_lines.append(f"  🔴 SELL signals : {len(sell_stocks)} stocks {sell_stocks}")
    report_lines.append(f"  🟡 HOLD signals : {len(hold_stocks)} stocks {hold_stocks}")

    # Detailed table
    report_lines.append("\n📈 STOCK-BY-STOCK ANALYSIS")
    report_lines.append("-" * 65)
    header = f"{'Stock':<6} {'Price':>8} {'Pred':>8} {'Chg%':>7} {'Signal':<14} {'RSI':>5} {'Conf':>5}"
    report_lines.append(header)
    report_lines.append("-" * 65)

    for ticker in tickers:
        sig = signals.get(ticker, {})
        pred = predictions.get(ticker, {})

        price = sig.get("close", 0)
        signal = sig.get("signal", "N/A")
        rsi = sig.get("rsi", 0)
        conf = sig.get("confidence", 0)
        pred_price = pred.get("predicted_price", price)
        pred_change = pred.get("predicted_change_pct", 0)
        emoji = signal_emoji(signal)
        arrow = "▲" if pred_change > 0 else "▼"

        line = f"{ticker:<6} ${price:>7.2f} ${pred_price:>7.2f} {arrow}{abs(pred_change):>5.1f}% {emoji} {signal:<11} {rsi:>5.1f} {conf:>4}%"
        report_lines.append(line)

    report_lines.append("-" * 65)

    # Technical deep dive
    report_lines.append("\n🔬 TECHNICAL SIGNALS")
    for ticker in tickers:
        sig = signals.get(ticker, {})
        reasons = sig.get("reasons", [])
        if reasons:
            report_lines.append(f"\n  {ticker}:")
            for r in reasons:
                report_lines.append(f"    • {r}")

    # Top opportunities
    report_lines.append("\n⚡ TOP OPPORTUNITIES")
    sorted_by_score = sorted(
        [(t, signals[t]["signal_score"]) for t in tickers],
        key=lambda x: x[1], reverse=True
    )
    for ticker, score in sorted_by_score[:3]:
        sig = signals[ticker]
        pred = predictions.get(ticker, {})
        report_lines.append(f"  {signal_emoji(sig['signal'])} {ticker}: {sig['signal']} | Score: {score:+d} | Predicted: {pred.get('predicted_change_pct', 0):+.2f}%")

    # Risk alerts
    high_volatility = [t for t in tickers if signals[t].get("volatility_20d", 0) > 0.4]
    if high_volatility:
        report_lines.append(f"\n⚠️  HIGH VOLATILITY ALERT: {high_volatility}")

    report_lines.append("\n" + "=" * 65)
    report_lines.append("  OpenBell rings before the market does. 🔔")
    report_lines.append("  Not financial advice. For educational purposes only.")
    report_lines.append("=" * 65)

    report = "\n".join(report_lines)

    # Save report
    os.makedirs("data/processed/reports", exist_ok=True)
    date_str = now.strftime("%Y-%m-%d")
    report_path = f"data/processed/reports/openbell_{date_str}.txt"
    with open(report_path, "w") as f:
        f.write(report)

    # Also save as JSON for dashboard
    report_data = {
        "generated_at": now.isoformat(),
        "market_status": get_market_status(),
        "summary": {
            "buy": buy_stocks,
            "sell": sell_stocks,
            "hold": hold_stocks
        },
        "signals": signals,
        "predictions": predictions
    }
    with open("data/processed/reports/latest_report.json", "w") as f:
        json.dump(report_data, f, indent=2)

    print(report)
    print(f"\n📄 Report saved to {report_path}")
    return report

if __name__ == "__main__":
    generate_report()
