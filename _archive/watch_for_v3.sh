#!/bin/sh
# Watch for the first *_latest_v3.json to appear and write a flag/log
OUT_DIR=/data/sentiment_analysis
LOG_DIR=/data/scripts/logs
LOG_FILE=${LOG_DIR}/watch_v3.log
FLAG_FILE=${LOG_DIR}/v3_ready.txt

mkdir -p "$LOG_DIR"
echo "[watch_for_v3] starting at $(date -u)" >> "$LOG_FILE"

if ls ${OUT_DIR}/*_latest_v3.json >/dev/null 2>&1; then
  echo "[watch_for_v3] v3 already present at start: $(date -u)" >> "$LOG_FILE"
  ls -1 ${OUT_DIR}/*_latest_v3.json >> "$LOG_FILE" 2>&1 || true
  echo "ready:$(date -u)" > "$FLAG_FILE"
  exit 0
fi

while true; do
  if ls ${OUT_DIR}/*_latest_v3.json >/dev/null 2>&1; then
    echo "[watch_for_v3] detected v3 at $(date -u)" >> "$LOG_FILE"
    ls -1 ${OUT_DIR}/*_latest_v3.json >> "$LOG_FILE" 2>&1 || true
    echo "ready:$(date -u)" > "$FLAG_FILE"
    # dump a short sample of the first v3 file
    first=$(ls -1 ${OUT_DIR}/*_latest_v3.json | head -n1)
    echo "--- sample head of ${first} ---" >> "$LOG_FILE"
    head -n 60 "$first" >> "$LOG_FILE" 2>&1 || true
    exit 0
  fi
  echo "[watch_for_v3] not found, sleeping 30s... $(date -u)" >> "$LOG_FILE"
  sleep 30
done
