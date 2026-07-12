#!/usr/bin/env python3
"""
OpenBell — Hadoop Streaming Mapper
Reads raw OHLCV data from HDFS, emits (ticker, day_data) pairs
"""

import sys
import csv
import json

reader = csv.DictReader(sys.stdin)
for row in reader:
    try:
        ticker = row.get("ticker", "UNKNOWN")
        date = row.get("date", "")
        close = float(row.get("close", 0))
        high = float(row.get("high", 0))
        low = float(row.get("low", 0))
        volume = float(row.get("volume", 0))
        open_price = float(row.get("open", 0))

        if close > 0 and ticker != "UNKNOWN":
            value = json.dumps({
                "date": date,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume
            })
            sys.stdout.write("{}\t{}\n".format(ticker, value))
    except (ValueError, KeyError):
        continue
