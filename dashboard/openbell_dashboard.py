"""
OpenBell — Analytics Dashboard
Visual dashboard from pre-market intelligence report
"""

import json
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime
import pytz

ET = pytz.timezone("America/New_York")

def load_report():
    path = "data/processed/reports/latest_report.json"
    if not os.path.exists(path):
        print("❌ No report found. Run pipeline first.")
        return None
    with open(path) as f:
        return json.load(f)

def signal_color(signal: str) -> str:
    return {
        "STRONG BUY": "#00b300",
        "BUY": "#66cc66",
        "HOLD": "#ffcc00",
        "SELL": "#ff6666",
        "STRONG SELL": "#cc0000"
    }.get(signal, "#888888")

def build_dashboard():
    report = load_report()
    if not report:
        return

    signals = report["signals"]
    predictions = report["predictions"]
    tickers = list(signals.keys())
    now = datetime.now(ET)

    fig = plt.figure(figsize=(20, 12))
    fig.patch.set_facecolor("#0d1117")
    fig.suptitle(
        f"🔔 OpenBell — Pre-Market Intelligence Dashboard\n"
        f"{now.strftime('%A, %B %d, %Y')} | Market: {report['market_status']}",
        fontsize=16, fontweight="bold", color="white", y=0.98
    )

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

    ax_style = {"facecolor": "#161b22", "alpha": 1.0}

    # ── Chart 1: Current Prices ──
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor("#161b22")
    prices = [signals[t]["close"] for t in tickers]
    colors = [signal_color(signals[t]["signal"]) for t in tickers]
    bars = ax1.bar(tickers, prices, color=colors, edgecolor="#30363d", linewidth=0.5)
    ax1.set_title("Current Prices ($)", color="white", fontweight="bold", pad=10)
    ax1.tick_params(colors="white")
    ax1.set_facecolor("#161b22")
    for spine in ax1.spines.values():
        spine.set_edgecolor("#30363d")
    for bar, price in zip(bars, prices):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f"${price:.0f}", ha="center", va="bottom", color="white", fontsize=8)

    # ── Chart 2: Predicted Change % ──
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor("#161b22")
    changes = [predictions.get(t, {}).get("predicted_change_pct", 0) for t in tickers]
    bar_colors = ["#66cc66" if c > 0 else "#ff6666" for c in changes]
    bars2 = ax2.bar(tickers, changes, color=bar_colors, edgecolor="#30363d", linewidth=0.5)
    ax2.axhline(y=0, color="#58a6ff", linewidth=0.8, linestyle="--", alpha=0.5)
    ax2.set_title("Predicted Change (%)", color="white", fontweight="bold", pad=10)
    ax2.tick_params(colors="white")
    for spine in ax2.spines.values():
        spine.set_edgecolor("#30363d")
    for bar, val in zip(bars2, changes):
        ypos = bar.get_height() + 0.05 if val >= 0 else bar.get_height() - 0.15
        ax2.text(bar.get_x() + bar.get_width()/2, ypos,
                f"{val:+.1f}%", ha="center", va="bottom", color="white", fontsize=8)

    # ── Chart 3: RSI Gauge ──
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_facecolor("#161b22")
    rsi_values = [signals[t]["rsi"] for t in tickers]
    rsi_colors = ["#cc0000" if r > 70 else "#00b300" if r < 30 else "#ffcc00" for r in rsi_values]
    bars3 = ax3.barh(tickers, rsi_values, color=rsi_colors, edgecolor="#30363d", linewidth=0.5)
    ax3.axvline(x=70, color="#ff6666", linewidth=1, linestyle="--", alpha=0.7, label="Overbought (70)")
    ax3.axvline(x=30, color="#66cc66", linewidth=1, linestyle="--", alpha=0.7, label="Oversold (30)")
    ax3.axvline(x=50, color="#888888", linewidth=0.5, linestyle=":", alpha=0.5)
    ax3.set_xlim(0, 100)
    ax3.set_title("RSI Values", color="white", fontweight="bold", pad=10)
    ax3.tick_params(colors="white")
    for spine in ax3.spines.values():
        spine.set_edgecolor("#30363d")
    legend = ax3.legend(fontsize=7, facecolor="#161b22", labelcolor="white", loc="lower right")
    for rsi, bar in zip(rsi_values, bars3):
        ax3.text(rsi + 1, bar.get_y() + bar.get_height()/2,
                f"{rsi:.1f}", va="center", color="white", fontsize=8)

    # ── Chart 4: Signal Summary (pie) ──
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.set_facecolor("#161b22")
    signal_counts = {"STRONG BUY": 0, "BUY": 0, "HOLD": 0, "SELL": 0, "STRONG SELL": 0}
    for t in tickers:
        s = signals[t]["signal"]
        if s in signal_counts:
            signal_counts[s] += 1
    labels = [k for k, v in signal_counts.items() if v > 0]
    sizes = [v for v in signal_counts.values() if v > 0]
    pie_colors = [signal_color(l) for l in labels]
    wedges, texts, autotexts = ax4.pie(
        sizes, labels=labels, colors=pie_colors,
        autopct="%1.0f%%", startangle=90,
        textprops={"color": "white", "fontsize": 9}
    )
    for at in autotexts:
        at.set_color("black")
        at.set_fontweight("bold")
    ax4.set_title("Signal Distribution", color="white", fontweight="bold", pad=10)

    # ── Chart 5: Confidence Scores ──
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.set_facecolor("#161b22")
    confidences = [signals[t]["confidence"] for t in tickers]
    conf_colors = ["#58a6ff" if c >= 65 else "#ffcc00" if c >= 55 else "#888888" for c in confidences]
    bars5 = ax5.bar(tickers, confidences, color=conf_colors, edgecolor="#30363d", linewidth=0.5)
    ax5.set_ylim(0, 100)
    ax5.axhline(y=65, color="#58a6ff", linewidth=0.8, linestyle="--", alpha=0.5)
    ax5.set_title("Signal Confidence (%)", color="white", fontweight="bold", pad=10)
    ax5.tick_params(colors="white")
    for spine in ax5.spines.values():
        spine.set_edgecolor("#30363d")
    for bar, val in zip(bars5, confidences):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{val}%", ha="center", va="bottom", color="white", fontsize=8)

    # ── Chart 6: 7-day Momentum ──
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.set_facecolor("#161b22")
    momentum = [signals[t].get("momentum_7d", 0) for t in tickers]
    mom_colors = ["#66cc66" if m > 0 else "#ff6666" for m in momentum]
    bars6 = ax6.bar(tickers, momentum, color=mom_colors, edgecolor="#30363d", linewidth=0.5)
    ax6.axhline(y=0, color="#888888", linewidth=0.8, linestyle="-", alpha=0.5)
    ax6.set_title("7-Day Momentum (%)", color="white", fontweight="bold", pad=10)
    ax6.tick_params(colors="white")
    for spine in ax6.spines.values():
        spine.set_edgecolor("#30363d")
    for bar, val in zip(bars6, momentum):
        ypos = bar.get_height() + 0.1 if val >= 0 else bar.get_height() - 0.5
        ax6.text(bar.get_x() + bar.get_width()/2, ypos,
                f"{val:+.1f}%", ha="center", color="white", fontsize=8)

    os.makedirs("docs", exist_ok=True)
    plt.savefig("docs/dashboard.png", dpi=150, bbox_inches="tight",
                facecolor="#0d1117", edgecolor="none")
    print("✅ Dashboard saved to docs/dashboard.png")
    plt.show()

if __name__ == "__main__":
    build_dashboard()
