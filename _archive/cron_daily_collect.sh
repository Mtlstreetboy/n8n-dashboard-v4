#!/bin/bash
# Collecte quotidienne automatique ?? 1h du matin (UTC)
# Installation: docker exec n8n_data_architect sh -c "crontab /data/scripts/cron_daily_collect.sh"

# Chaque jour ?? 1h00 UTC
0 1 * * * cd /data/scripts && python3 collect_news.py 100 >> /data/files/collect_daily.log 2>&1

# Alternative: Toutes les 6 heures (pour tester rapidement)
# 0 */6 * * * cd /data/scripts && python3 collect_news.py 100 >> /data/files/collect_daily.log 2>&1
