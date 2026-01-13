#!/bin/sh
# Wait until batch loader and any heavy V2 analyzers finish, then call the existing V3 runner.
LOGDIR=/data/scripts/logs
mkdir -p "$LOGDIR"
echo "[run_v3_when_idle] started at $(date -u)" >> "$LOGDIR/run_v3_when_idle.log"

check_heavy() {
  # return 0 if any heavy process is running
  # We only wait for the batch loader and any V2 batch analyzer (if still used).
  ps aux | grep -E "[b]atch_loader_v2.py|[a]nalyze_all_sentiment.py" >/dev/null 2>&1
  return $?
}

while check_heavy; do
  echo "[run_v3_when_idle] detected heavy process running at $(date -u), sleeping 30s" >> "$LOGDIR/run_v3_when_idle.log"
  sleep 30
done

echo "[run_v3_when_idle] system idle at $(date -u). Starting V3 runner." >> "$LOGDIR/run_v3_when_idle.log"

if [ -x /data/scripts/run_v3_after_batch.sh ]; then
  echo "[run_v3_when_idle] calling /data/scripts/run_v3_after_batch.sh" >> "$LOGDIR/run_v3_when_idle.log"
  /data/scripts/run_v3_after_batch.sh >> "$LOGDIR/run_v3_when_idle.log" 2>&1
  echo "[run_v3_when_idle] /data/scripts/run_v3_after_batch.sh finished at $(date -u)" >> "$LOGDIR/run_v3_when_idle.log"
else
  echo "[run_v3_when_idle] /data/scripts/run_v3_after_batch.sh not found or not executable; exiting" >> "$LOGDIR/run_v3_when_idle.log"
fi

echo "[run_v3_when_idle] done at $(date -u)" >> "$LOGDIR/run_v3_when_idle.log"
exit 0
