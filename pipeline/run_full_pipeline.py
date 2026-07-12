"""
OpenBell — Full Pipeline Runner
Orchestrates: HDFS upload → Hadoop MapReduce → ML Predictions → Report → Dashboard
"""

import subprocess
import sys
import os
from datetime import datetime
import pytz

ET = pytz.timezone("America/New_York")

def run_step(name, script):
    print(f"\n{'='*55}")
    print(f"  {name}")
    print(f"{'='*55}")
    result = subprocess.run([sys.executable, script], capture_output=False)
    if result.returncode != 0:
        print(f"❌ {name} failed")
        return False
    return True

def upload_to_hdfs():
    """Upload fresh stock data to HDFS."""
    print(f"\n{'='*55}")
    print("  📤 Uploading stock data to HDFS...")
    print(f"{'='*55}")
    tickers = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT", "AMZN", "META"]
    for ticker in tickers:
        path = f"data/raw/{ticker}.csv"
        if os.path.exists(path):
            subprocess.run(["docker", "cp", path, f"namenode:/tmp/{ticker}.csv"],
                         capture_output=True)
            subprocess.run(["docker", "exec", "namenode", "hdfs", "dfs",
                          "-put", "-f", f"/tmp/{ticker}.csv",
                          f"/openbell/raw/stocks/{ticker}.csv"],
                         capture_output=True)
            print(f"  ✅ {ticker} → HDFS")
    return True

def run_hadoop_mapreduce():
    """Run real Hadoop Streaming MapReduce."""
    print(f"\n{'='*55}")
    print("  ⚡ Running Hadoop Streaming MapReduce...")
    print(f"{'='*55}")
    result = subprocess.run(
        ["bash", "hadoop/mapreduce/run_hadoop_mapreduce.sh"],
        capture_output=True, text=True
    )
    if "Streaming Command Failed" in result.stdout or result.returncode != 0:
        print("❌ Hadoop MapReduce failed")
        print(result.stdout[-500:])
        return False
    print("  ✅ MapReduce complete")
    return True

def read_hdfs_results():
    """Read MapReduce results from HDFS."""
    print(f"\n{'='*55}")
    print("  📥 Reading results from HDFS...")
    print(f"{'='*55}")
    result = subprocess.run([sys.executable, "hadoop/hdfs_reader.py"],
                          capture_output=False)
    return result.returncode == 0

def main():
    now = datetime.now(ET)
    print("\n" + "="*55)
    print("  🔔 OPENBELL — FULL PIPELINE")
    print(f"  {now.strftime('%A, %B %d, %Y at %I:%M %p ET')}")
    print("="*55)

    steps = [
        ("📥 Fetching stock data", "pipeline/fetch_data.py"),
    ]

    # Step 1: Fetch data
    for name, script in steps:
        if not run_step(name, script):
            sys.exit(1)

    # Step 2: Upload to HDFS
    upload_to_hdfs()

    # Step 3: Hadoop MapReduce
    run_hadoop_mapreduce()

    # Step 4: Read HDFS results
    read_hdfs_results()

    # Step 5: ML Predictions
    if not run_step("🤖 ML Predictions", "pipeline/predict.py"):
        sys.exit(1)

    # Step 6: Generate Report
    if not run_step("📄 Pre-Market Report", "pipeline/report.py"):
        sys.exit(1)

    # Step 7: Dashboard
    if not run_step("📊 Dashboard", "dashboard/openbell_dashboard.py"):
        sys.exit(1)

    print("\n" + "="*55)
    print("  ✅ OPENBELL PIPELINE COMPLETE!")
    print(f"  Report: data/processed/reports/openbell_{now.strftime('%Y-%m-%d')}.txt")
    print("="*55)

if __name__ == "__main__":
    main()
