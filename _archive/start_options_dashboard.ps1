# 🚀 QUICK START - Dashboard Options (PowerShell)
# --------------------------------------------------------------------
# Script pour lancer rapidement le dashboard d'options sous Windows

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "📊 DASHBOARD OPTIONS - Quick Start" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 1. Vérifier Docker
Write-Host ""
Write-Host "🔍 Vérification de Docker..." -ForegroundColor Yellow
$containerRunning = docker ps --format "{{.Names}}" | Select-String "n8n_data_architect"
if (-not $containerRunning) {
    Write-Host "❌ Container n8n_data_architect non démarré" -ForegroundColor Red
    Write-Host "   Lancement du container..." -ForegroundColor Yellow
    docker start n8n_data_architect
    Start-Sleep -Seconds 3
}
Write-Host "✅ Container actif" -ForegroundColor Green

# 2. Vérifier si des données existent déjà
Write-Host ""
Write-Host "🔍 Vérification des données d'options..." -ForegroundColor Yellow
$optionsFiles = docker exec n8n_data_architect sh -c "ls /data/options_data/*.csv 2>/dev/null | wc -l"
if ($optionsFiles -eq "0") {
    Write-Host "📥 Aucune donnée trouvée. Collection des options..." -ForegroundColor Yellow
    Write-Host "   (Cela peut prendre 5-10 minutes pour tous les tickers)" -ForegroundColor Gray
    docker exec n8n_data_architect python3 /data/scripts/collect_options.py
} else {
    Write-Host "✅ Données d'options trouvées ($optionsFiles fichiers)" -ForegroundColor Green
    $response = Read-Host "Recollect les données? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "📥 Collection des données d'options..." -ForegroundColor Yellow
        docker exec n8n_data_architect python3 /data/scripts/collect_options.py
    }
}

# 3. Lancer le dashboard
Write-Host ""
Write-Host "🚀 Lancement du dashboard..." -ForegroundColor Yellow

# Arrêter l'instance précédente
docker exec n8n_data_architect sh -c "pkill -f 'streamlit.*dashboard_options' 2>/dev/null || true"
Start-Sleep -Seconds 2

# Lancer nouvelle instance
docker exec -d n8n_data_architect streamlit run /data/scripts/dashboard_options.py --server.port 8501 --server.address 0.0.0.0
Start-Sleep -Seconds 3

# 4. Vérifier que ça tourne
Write-Host ""
Write-Host "🔍 Vérification..." -ForegroundColor Yellow
$processCheck = docker exec n8n_data_architect sh -c "ps aux | grep '[s]treamlit.*dashboard_options'"
if ($processCheck) {
    Write-Host "✅ Dashboard lancé avec succès!" -ForegroundColor Green
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "🎉 DASHBOARD ACCESSIBLE À:" -ForegroundColor Green
    Write-Host "   http://localhost:8501" -ForegroundColor White
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 Exemples de tickers disponibles:" -ForegroundColor Yellow
    $tickers = docker exec n8n_data_architect sh -c "ls /data/options_data/*_calls_*.csv 2>/dev/null | head -10 | xargs -n1 basename | cut -d'_' -f1 | sort -u"
    Write-Host $tickers -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Pour tester:" -ForegroundColor Cyan
    Write-Host "   1. Ouvrir http://localhost:8501" -ForegroundColor White
    Write-Host "   2. Entrer un ticker (ex: AAPL, NVDA, TSLA)" -ForegroundColor White
    Write-Host "   3. Cliquer 'Analyser'" -ForegroundColor White
    Write-Host "   4. Explorer les 5 onglets de visualisation" -ForegroundColor White
    Write-Host ""
    Write-Host "📚 Documentation complète:" -ForegroundColor Cyan
    Write-Host "   prod/README_OPTIONS_DASHBOARD.md" -ForegroundColor White
    Write-Host ""
    
    # Ouvrir le navigateur automatiquement
    $openBrowser = Read-Host "Ouvrir dans le navigateur? (Y/n)"
    if ($openBrowser -ne 'n' -and $openBrowser -ne 'N') {
        Start-Process "http://localhost:8501"
    }
} else {
    Write-Host "❌ Erreur lors du lancement du dashboard" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔍 Vérifier les logs:" -ForegroundColor Yellow
    Write-Host "   docker exec n8n_data_architect sh -c 'tail -50 /data/logs/dashboard_options.log 2>/dev/null || echo No logs'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔍 Vérifier les processus:" -ForegroundColor Yellow
    Write-Host "   docker exec n8n_data_architect ps aux | grep streamlit" -ForegroundColor Gray
    exit 1
}
