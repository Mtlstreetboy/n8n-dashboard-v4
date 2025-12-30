#!/usr/bin/env pwsh
# Script de monitoring en temps réel du batch loader
# Usage: .\scripts\watch_batch_progress.ps1

Write-Host "🔍 Monitoring du Batch Loader - AI Sentiment Pipeline" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$counter = 0
while ($true) {
    Clear-Host
    Write-Host "🔍 Monitoring du Batch Loader - Refresh #$counter" -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Vérifier si le process tourne
    Write-Host "📊 Status du Process:" -ForegroundColor Yellow
    $process = docker exec n8n_data_architect sh -c "ps aux | grep batch_loader_v2.py | grep -v grep" 2>$null
    if ($process) {
        Write-Host "✓ Batch Loader est ACTIF" -ForegroundColor Green
        Write-Host $process
    } else {
        Write-Host "✗ Batch Loader n'est PAS en cours d'exécution" -ForegroundColor Red
    }
    Write-Host ""
    
    # Afficher les dernières lignes du log dans le conteneur
    Write-Host "📝 Dernières lignes du log (conteneur):" -ForegroundColor Yellow
    docker exec n8n_data_architect sh -c "tail -n 25 /data/scripts/logs/batch_loader_v2.log 2>/dev/null || tail -n 25 /data/logs/batch_loader_v2.log 2>/dev/null || echo 'Aucun log trouvé'" 2>$null
    Write-Host ""
    
    # Compter les fichiers JSON créés
    Write-Host "📁 Fichiers collectés:" -ForegroundColor Yellow
    $jsonCount = docker exec n8n_data_architect sh -c "ls -1 /data/files/companies/*_news.json 2>/dev/null | wc -l" 2>$null
    if ($jsonCount) {
        Write-Host "  → $jsonCount fichiers *_news.json trouvés dans /data/files/companies/" -ForegroundColor Green
    }
    
    # Afficher les 5 derniers fichiers modifiés
    $recentFiles = docker exec n8n_data_architect sh -c "ls -lt /data/files/companies/*_news.json 2>/dev/null | head -n 5" 2>$null
    if ($recentFiles) {
        Write-Host ""
        Write-Host "📄 5 derniers fichiers modifiés:" -ForegroundColor Yellow
        Write-Host $recentFiles
    }
    
    Write-Host ""
    Write-Host "Appuyez sur Ctrl+C pour arrêter le monitoring" -ForegroundColor Gray
    Write-Host "Prochaine actualisation dans 5 secondes..." -ForegroundColor Gray
    
    Start-Sleep -Seconds 5
    $counter++
}
