"""
OpenBell — HDFS Results Reader
Reads MapReduce output from HDFS into Python dict
for use by the prediction and report pipeline
"""

import subprocess
import json
import os

def read_hdfs_signals():
    """Read latest MapReduce results from HDFS."""
    try:
        # Find latest output directory
        result = subprocess.run(
            ["docker", "exec", "namenode", "hdfs", "dfs", "-ls", "/openbell/processed/"],
            capture_output=True, text=True
        )
        
        lines = result.stdout.strip().split("\n")
        indicator_dirs = [l.split()[-1] for l in lines if "indicators_" in l]
        
        if not indicator_dirs:
            print("  ⚠️  No HDFS results found. Run Hadoop MapReduce first.")
            return {}
        
        latest_dir = sorted(indicator_dirs)[-1]
        print(f"  📂 Reading from HDFS: {latest_dir}")
        
        # Read results
        result = subprocess.run(
            ["docker", "exec", "namenode", "hdfs", "dfs", "-cat", f"{latest_dir}/part-*"],
            capture_output=True, text=True
        )
        
        signals = {}
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                ticker = data["ticker"]
                signals[ticker] = data
                print(f"  ✅ {ticker}: {data['signal']} (RSI: {data['rsi']})")
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Save locally for report/dashboard
        os.makedirs("data/processed", exist_ok=True)
        with open("data/processed/signals.json", "w") as f:
            json.dump(signals, f, indent=2)
        
        print(f"\n  📊 {len(signals)} stocks read from HDFS")
        return signals
        
    except Exception as e:
        print(f"  ❌ HDFS read error: {e}")
        return {}

if __name__ == "__main__":
    print("\n🔔 OpenBell — Reading MapReduce Results from HDFS")
    print("=" * 50)
    signals = read_hdfs_signals()
    
    if signals:
        print("\n🔔 Signals from Hadoop:")
        print(f"  {'Stock':<6} {'Price':>8} {'Signal':<14} {'RSI':>5}")
        print("  " + "-"*40)
        for ticker, sig in signals.items():
            print(f"  {ticker:<6} ${sig['close']:>7.2f} {sig['signal']:<14} {sig['rsi']:>5.1f}")
