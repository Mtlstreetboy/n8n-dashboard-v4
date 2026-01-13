#!/bin/bash
tickers="NVDA MSFT GOOGL META AMZN TSLA AMD INTC AVGO CRM ORCL ADBE SNOW PLTR NOW"

for ticker in $tickers; do
    echo "=================================================="
    echo "🚀 Running Advanced Sentiment Engine V2 for $ticker"
    echo "=================================================="
    python3 /data/scripts/advanced_sentiment_engine_v2.py $ticker
    echo "✅ Done for $ticker"
    echo ""
done
