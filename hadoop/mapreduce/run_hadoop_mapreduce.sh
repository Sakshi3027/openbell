#!/bin/bash
# OpenBell — Real Hadoop MapReduce Runner

echo "🔔 OpenBell — Hadoop MapReduce Job"
echo "===================================="

INPUT="/openbell/raw/stocks"
OUTPUT="/openbell/processed/indicators_$(date +%Y%m%d_%H%M%S)"

# Copy scripts to namenode
docker cp hadoop/mapreduce/streaming/mapper.py namenode:/tmp/mapper.py
docker cp hadoop/mapreduce/streaming/reducer.py namenode:/tmp/reducer.py

# Put scripts in HDFS so all nodes can access them
docker exec -it namenode bash -c "
hdfs dfs -rm -f /openbell/scripts/mapper.py /openbell/scripts/reducer.py 2>/dev/null
hdfs dfs -mkdir -p /openbell/scripts
hdfs dfs -put /tmp/mapper.py /openbell/scripts/mapper.py
hdfs dfs -put /tmp/reducer.py /openbell/scripts/reducer.py
echo 'Scripts uploaded to HDFS'
"

echo "📤 Running Hadoop Streaming MapReduce..."
docker exec -it namenode bash -c "
hadoop jar /opt/hadoop-3.2.1/share/hadoop/tools/lib/hadoop-streaming-3.2.1.jar \
  -files hdfs:///openbell/scripts/mapper.py,hdfs:///openbell/scripts/reducer.py \
  -mapper 'python3 mapper.py' \
  -reducer 'python3 reducer.py' \
  -input $INPUT \
  -output $OUTPUT \
  2>&1
"

STATUS=$?

if [ $STATUS -eq 0 ]; then
    echo ""
    echo "📥 Reading results from HDFS..."
    docker exec -it namenode bash -c "hdfs dfs -cat $OUTPUT/part-*" 2>/dev/null | python3 -c "
import sys, json
print()
print('  {:<6} {:>8} {:<14} {:>5} {:>6} {:>5}'.format('Stock','Price','Signal','RSI','Score','Days'))
print('  ' + '-'*50)
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
        print('  {:<6} \${:>7.2f} {:<14} {:>5.1f} {:>+6d} {:>5}'.format(
            data['ticker'], data['close'], data['signal'],
            data['rsi'], data['signal_score'], data['days_processed']))
    except:
        pass
"
else
    echo "❌ MapReduce job failed"
fi

echo ""
echo "✅ Results in HDFS: $OUTPUT"
