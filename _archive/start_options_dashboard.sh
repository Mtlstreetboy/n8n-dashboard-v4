#!/bin/bash
# -*- coding: utf-8 -*-
"""
🚀 QUICK START - Dashboard Options
--------------------------------------------------------------------
Script pour lancer rapidement le dashboard d'options
"""

echo "================================================================"
echo "📊 DASHBOARD OPTIONS - Quick Start"
echo "================================================================"

# 1. Vérifier Docker
echo ""
echo "🔍 Vérification de Docker..."
if ! docker ps | grep -q n8n_data_architect; then
    echo "❌ Container n8n_data_architect non démarré"
    echo "   Lancement du container..."
    docker start n8n_data_architect
    sleep 3
fi
echo "✅ Container actif"

# 2. Collecter les données d'options
echo ""
echo "📥 Collection des données d'options..."
echo "   (Cela peut prendre 5-10 minutes pour tous les tickers)"
docker exec n8n_data_architect python3 /data/scripts/collect_options.py

# 3. Lancer le dashboard
echo ""
echo "🚀 Lancement du dashboard..."
docker exec n8n_data_architect sh -c "pkill -f 'streamlit.*dashboard_options' || true"
sleep 2
docker exec -d n8n_data_architect streamlit run /data/scripts/dashboard_options.py --server.port 8501 --server.address 0.0.0.0
sleep 3

# 4. Vérifier que ça tourne
echo ""
echo "🔍 Vérification..."
if docker exec n8n_data_architect sh -c "ps aux | grep -q '[s]treamlit.*dashboard_options'"; then
    echo "✅ Dashboard lancé avec succès!"
    echo ""
    echo "================================================================"
    echo "🎉 DASHBOARD ACCESSIBLE À:"
    echo "   http://localhost:8501"
    echo "================================================================"
    echo ""
    echo "📊 Exemples de tickers disponibles:"
    docker exec n8n_data_architect sh -c "ls /data/options_data/*_calls_*.csv 2>/dev/null | head -5 | xargs -n1 basename | cut -d'_' -f1 | sort -u"
    echo ""
    echo "💡 Pour tester:"
    echo "   1. Ouvrir http://localhost:8501"
    echo "   2. Entrer un ticker (ex: AAPL, NVDA, TSLA)"
    echo "   3. Cliquer 'Analyser'"
    echo "   4. Explorer les 5 onglets de visualisation"
    echo ""
else
    echo "❌ Erreur lors du lancement du dashboard"
    echo "   Vérifier les logs:"
    echo "   docker exec n8n_data_architect sh -c 'tail -50 /data/logs/dashboard_options.log'"
    exit 1
fi
