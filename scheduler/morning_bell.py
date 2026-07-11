"""
OpenBell — Morning Bell Scheduler
Runs automatically every trading day at 8:00 AM ET
Fetches data → MapReduce → Predictions → Report
"""

import schedule
import time
import subprocess
import sys
import os
from datetime import datetime
import pytz

ET = pytz.timezone("America/New_York")

def is_trading_day():
    now = datetime.now(ET)
    return now.weekday() < 5  # Monday=0, Friday=4

def run_pipeline():
    now = datetime.now(ET)
    print(f"\n{'='*60}")
    print(f"🔔 OPENBELL MORNING BELL — {now.strftime('%Y-%m-%d %H:%M ET')}")
    print(f"{'='*60}")

    if not is_trading_day():
        print("📅 Weekend — market closed. Skipping pipeline.")
        return

    steps = [
        ("📥 Fetching stock data...",    "pipeline/fetch_data.py"),
        ("⚡ Running MapReduce...",       "hadoop/mapreduce/technical_indicators.py"),
        ("🤖 Generating predictions...", "pipeline/predict.py"),
        ("📄 Generating report...",      "pipeline/report.py"),
    ]

    for msg, script in steps:
        print(f"\n{msg}")
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"  ✅ Done")
            # Print last 3 lines of output
            lines = result.stdout.strip().split("\n")
            for line in lines[-3:]:
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"  ❌ Failed: {result.stderr[-200:]}")
            return

    print(f"\n✅ OpenBell pipeline complete!")
    print(f"   Report: data/processed/reports/openbell_{now.strftime('%Y-%m-%d')}.txt")

def run_now():
    """Run pipeline immediately — for testing."""
    run_pipeline()

def start_scheduler():
    """Start the daily 8:00 AM ET scheduler."""
    print("🔔 OpenBell Scheduler Started")
    print("   Runs every trading day at 8:00 AM ET")
    print("   Press Ctrl+C to stop\n")

    # Schedule at 8:00 AM ET daily
    schedule.every().day.at("08:00").do(run_pipeline)

    # Show next run
    print(f"   Next run: {schedule.next_run()}")

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        run_now()
    else:
        start_scheduler()
