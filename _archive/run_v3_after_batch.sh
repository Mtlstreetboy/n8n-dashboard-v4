#!/bin/sh
# Wait for batch_loader_v2.py to finish, then run advanced_sentiment_engine_v3 for all tickers
SLEEP_INTERVAL=10
LOG_DIR=/data/scripts/logs
LOG_FILE=${LOG_DIR}/engine_v3_run.log
PYTHON=python3
SCRIPT_DIR=/data/scripts

mkdir -p "$LOG_DIR"
echo "[run_v3_after_batch] starting at $(date -u)" >> "$LOG_FILE"

while pgrep -f batch_loader_v2.py >/dev/null 2>&1; do
  echo "[run_v3_after_batch] batch_loader_v2 running, sleeping $SLEEP_INTERVALs... $(date -u)" >> "$LOG_FILE"
  sleep $SLEEP_INTERVAL
done

echo "[run_v3_after_batch] batch finished or not running. Starting V3 analysis... $(date -u)" >> "$LOG_FILE"

cd "$SCRIPT_DIR" || exit 1
export PYTHONPATH="$SCRIPT_DIR"

# Run V3 engine sequentially for all companies
python3 - <<'PY' >> "$LOG_FILE" 2>&1
import sys, time
sys.path.insert(0, '/data/scripts')
from companies_config import get_all_companies
import subprocess, os
companies = get_all_companies()
print('[run_v3_after_batch] companies to process:', len(companies))
for c in companies:
    ticker = c['ticker']
    try:
        print('\n[run_v3_after_batch] Running V3 for', ticker)
        subprocess.run(["python3", "/data/scripts/advanced_sentiment_engine_v3.py", ticker], check=True, timeout=600)
        print('[run_v3_after_batch] Done', ticker)
    except subprocess.TimeoutExpired:
        print('[run_v3_after_batch] TIMEOUT for', ticker)
    except Exception as e:
        print('[run_v3_after_batch] ERROR for', ticker, e)
    time.sleep(1)
print('\n[run_v3_after_batch] All done at', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
PY

echo "[run_v3_after_batch] finished at $(date -u)" >> "$LOG_FILE"
