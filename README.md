cat > README.md << 'EOF'
# 🔔 OpenBell

> Pre-market stock intelligence platform — rings before the market does.

**Stack:** Python · Hadoop HDFS · MapReduce Streaming · Yahoo Finance · scikit-learn · Dagster · Matplotlib  
**Coverage:** AAPL · TSLA · NVDA · GOOGL · MSFT · AMZN · META  
**Schedule:** Runs automatically every trading day at 8:00 AM ET

---

## What It Does

OpenBell fetches real stock data, stores it in **Hadoop HDFS**, runs **real Hadoop Streaming MapReduce** to compute 15+ technical indicators across 7 stocks in parallel, trains an ensemble ML model on the results, and generates a pre-market intelligence report — all before 9:30 AM ET market open.

---

## Global Asset Lineage (Dagster)

![OpenBell Asset Lineage](docs/lineage.png)

---

## Analytics Dashboard

![OpenBell Dashboard](docs/dashboard.png)

---

## Architecture
```
Every trading day at 8:00 AM ET
↓
┌─────────────────────────────┐
│  Data Fetch                 │  Yahoo Finance API → 501 days OHLCV
│  pipeline/fetch_data.py     │  7 stocks: AAPL TSLA NVDA GOOGL MSFT AMZN META
└───────────┬─────────────────┘
↓
┌─────────────────────────────┐
│  HDFS Ingestion             │  Raw CSVs uploaded to Hadoop HDFS
│  /openbell/raw/stocks/      │  hdfs dfs -put → distributed storage
└───────────┬─────────────────┘
↓
┌─────────────────────────────┐
│  Hadoop Streaming MapReduce │  Real MapReduce on Hadoop cluster
│  hadoop/mapreduce/          │  7 mapper tasks run in parallel
│  mapper.py + reducer.py     │  RSI · MACD · Bollinger Bands · ATR
│                             │  Results written back to HDFS
└───────────┬─────────────────┘
↓
┌─────────────────────────────┐
│  HDFS Reader                │  Reads MapReduce output from HDFS
│  hadoop/hdfs_reader.py      │  Converts to signals.json for ML pipeline
└───────────┬─────────────────┘
↓
┌─────────────────────────────┐
│  ML Predictions             │  Random Forest + Gradient Boosting ensemble
│  pipeline/predict.py        │  14 features · 80/20 time-series split
│                             │  Predicts next-day price + % change
└───────────┬─────────────────┘
↓
┌─────────────────────────────┐
│  Pre-Market Report          │  Full intelligence briefing
│  pipeline/report.py         │  Signals + predictions + opportunities
└───────────┬─────────────────┘
↓
┌─────────────────────────────┐
│  Dashboard                  │  6-panel dark-theme visual analytics
│  dashboard/                 │  Prices · RSI · Momentum · Signals
└─────────────────────────────┘
```

---

## Real Hadoop MapReduce

This is **real Hadoop Streaming** — not a simulation. The pipeline runs actual MapReduce jobs on a Hadoop 3.2.1 cluster with HDFS storage, YARN resource management, and distributed task execution.

**MAP phase** — 7 mapper tasks run in parallel, one per stock file in HDFS:
HDFS /openbell/raw/stocks/AAPL.csv → mapper.py → AAPL  {"close": 315.32, "rsi": 61.9, ...}
HDFS /openbell/raw/stocks/TSLA.csv → mapper.py → TSLA  {"close": 407.76, "rsi": 52.0, ...}
... (7 tasks in parallel)

**REDUCE phase** — 1 reducer aggregates all signals:
AAPL {"rsi": 61.9, "macd": 0.45, "bb_pos": 0.87} → AAPL BUY  score: +1
TSLA {"rsi": 52.0, "macd": -1.2, "bb_pos": 0.32} → TSLA HOLD score: 0
...
Results written to HDFS /openbell/processed/indicators_YYYYMMDD/

**Hadoop cluster (Docker):**
- namenode (HDFS master)
- datanode (HDFS storage)
- resourcemanager (YARN)
- nodemanager (task execution)
- historyserver
---

## Sample Pre-Market Report
=================================================================
O P E N B E L L  —  P R E - M A R K E T  I N T E L L I G E N C E
Generated : Friday, July 12, 2026 at 08:00 AM ET
Market    : PRE-MARKET
Coverage  : 7 stocks tracked
BUY  signals : 1 stock  ['AAPL']
SELL signals : 2 stocks ['MSFT', 'NVDA']
HOLD signals : 4 stocks ['TSLA', 'GOOGL', 'META', 'AMZN']
Stock     Price     Pred    Chg% Signal    RSI  Conf
AAPL   $ 315.32 $ 311.97 ▼  1.1% BUY      61.9   60%
MSFT   $ 385.10 $ 379.34 ▼  1.5% SELL     52.9   60%
META   $ 669.21 $ 676.41 ▲  1.1% HOLD     68.7   50%
HIGH VOLATILITY ALERT: ['TSLA', 'META']
---

## Technical Indicators (MapReduce)

| Indicator | Period | Description |
|-----------|--------|-------------|
| RSI | 14 | Relative Strength Index |
| MACD | 12/26/9 | Moving Average Convergence Divergence |
| Bollinger Bands | 20, 2σ | Price volatility bands |
| ATR | 14 | Average True Range |
| Moving Averages | 7/20/50/200 | Trend direction |
| Volume Ratio | 20 | Current vs average volume |
| Momentum | 7d/30d | Price change over period |
| Volatility | 20d | Annualized rolling volatility |

---

## ML Model

- **Algorithm:** Random Forest + Gradient Boosting (50/50 ensemble)
- **Input:** MapReduce output from HDFS (14 technical indicators)
- **Target:** Next-day return → price prediction
- **Split:** 80/20 time-series (no data leakage)
- **Honest metrics:** MAE $2-7 per stock

---

## Running Locally

```bash
# 1. Clone
git clone https://github.com/Sakshi3027/openbell.git
cd openbell

# 2. Install
pip install -r requirements.txt

# 3. Start Hadoop cluster (Docker)
docker-compose up -d  # or use existing Hadoop containers

# 4. Run full pipeline
python3 pipeline/run_full_pipeline.py

# 5. Or run steps individually
python3 pipeline/fetch_data.py
bash hadoop/mapreduce/run_hadoop_mapreduce.sh
python3 hadoop/hdfs_reader.py
python3 pipeline/predict.py
python3 pipeline/report.py
python3 dashboard/openbell_dashboard.py

# 6. Run with Dagster (asset lineage UI)
dagster dev -w workspace.yaml
# Open http://localhost:3000

# 7. Daily scheduler (8:00 AM ET)
python3 scheduler/morning_bell.py
```

---

## Project Structure
```
openbell/
├── pipeline/
│   ├── fetch_data.py              # Yahoo Finance ingestion
│   ├── predict.py                 # ML ensemble predictions
│   ├── report.py                  # Pre-market intelligence report
│   └── run_full_pipeline.py       # Full pipeline orchestrator
├── hadoop/
│   ├── mapreduce/
│   │   ├── streaming/
│   │   │   ├── mapper.py          # Hadoop Streaming mapper
│   │   │   └── reducer.py         # Hadoop Streaming reducer
│   │   └── run_hadoop_mapreduce.sh # Hadoop job runner
│   └── hdfs_reader.py             # Reads MapReduce output from HDFS
├── dagster_pipeline/
│   ├── assets.py                  # 5 Dagster software-defined assets
│   ├── schedules.py               # 8:00 AM ET Mon-Fri schedule
│   └── definitions.py             # Dagster definitions
├── dashboard/
│   └── openbell_dashboard.py      # 6-panel dark-theme dashboard
├── scheduler/
│   └── morning_bell.py            # Daily scheduler
├── docs/
│   ├── lineage.png                # Dagster asset lineage
│   └── dashboard.png              # Analytics dashboard
└── workspace.yaml                 # Dagster workspace config
```
---

Built by [Sakshi Chavan](https://github.com/Sakshi3027) · MS Data Science
AI Engineer · Data Engineer · RAG systems · Distributed pipelines · Actively interviewing

