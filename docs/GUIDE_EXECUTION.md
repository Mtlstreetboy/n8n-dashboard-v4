# 🚀 Guide d'Exécution - Pipeline de Sentiment Financier

**Date:** 23 décembre 2025  
**Version:** 2.0 (FinBERT + VADER)

---

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Mode VADER (Baseline)](#mode-vader-baseline)
3. [Mode FinBERT CPU](#mode-finbert-cpu)
4. [Mode FinBERT GPU](#mode-finbert-gpu)
5. [Pipeline Complet de A à Z](#pipeline-complet-de-a-à-z)
6. [Vérification et Diagnostic](#vérification-et-diagnostic)

---

## Prérequis

### Installation de base
```powershell
# Vérifier que Docker est installé et en cours d'exécution
docker --version
docker-compose --version

# Vérifier que le repo est cloné
cd c:\n8n-local-stack
```

### Pour FinBERT GPU (optionnel, nécessite RTX 2070 Ti)
```powershell
# Vérifier NVIDIA runtime dans WSL2
wsl -e nvidia-smi

# Tester l'accès GPU depuis Docker
docker run --gpus all --rm nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

## Mode VADER (Baseline)

### ✅ Avantages
- Léger, rapide (~0.5ms par texte)
- Fonctionne sur Alpine (musl libc)
- Aucune dépendance lourde
- Précision: ~65% sur textes financiers

### 🚀 Étape 1: Démarrer le container principal

```powershell
# Démarrer le stack principal (n8n, Ollama, data_architect)
docker-compose up -d

# Vérifier que le container est démarré
docker ps | Select-String "n8n_data_architect"
```

### 🚀 Étape 2: Installer VADER

```powershell
# Installer VADER dans le container
docker exec -u root n8n_data_architect sh -c "pip install -q vaderSentiment"

# Vérifier l'installation
docker exec n8n_data_architect python3 -c "from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer; print('✅ VADER OK')"
```

### 🚀 Étape 3: Collecter les nouvelles (Batch Loader)

```powershell
# Pour un seul ticker (ex: AAPL)
docker exec n8n_data_architect python3 /data/scripts/batch_loader_v2.py AAPL

# Pour plusieurs tickers (boucle)
$tickers = @("AAPL", "MSFT", "GOOGL", "TSLA", "NVDA")
foreach ($ticker in $tickers) {
    Write-Host "📰 Collecte des nouvelles pour $ticker..." -ForegroundColor Cyan
    docker exec n8n_data_architect python3 /data/scripts/batch_loader_v2.py $ticker
}
```

### 🚀 Étape 4: Collecter les données d'options

```powershell
# Collecter les options pour tous les tickers configurés
docker exec n8n_data_architect python3 /data/scripts/collect_options.py

# Ou pour un ticker spécifique
docker exec n8n_data_architect python3 -c "
from collect_options import collect_single_ticker
collect_single_ticker('AAPL')
"
```

### 🚀 Étape 5: Analyser le sentiment (V3 Engine)

```powershell
# Analyse sentiment multi-dimensionnelle pour un ticker
docker exec n8n_data_architect python3 /data/scripts/advanced_sentiment_engine_v3.py AAPL

# Pour tous les tickers
$tickers = @("AAPL", "MSFT", "GOOGL", "TSLA", "NVDA")
foreach ($ticker in $tickers) {
    Write-Host "📊 Analyse sentiment pour $ticker..." -ForegroundColor Green
    docker exec n8n_data_architect python3 /data/scripts/advanced_sentiment_engine_v3.py $ticker
}
```

### 🚀 Étape 6: Récupérer les résultats

```powershell
# Copier les résultats sur le host
docker cp n8n_data_architect:/data/sentiment_analysis .\data\sentiment_analysis

# Lister les rapports générés
Get-ChildItem .\data\sentiment_analysis\*_latest_v3.json | Select-Object Name, LastWriteTime
```

---

## Mode FinBERT CPU

### ✅ Avantages
- Précision supérieure (~88% sur textes financiers)
- Modèle pré-entraîné sur corpus financier
- Fonctionne sans GPU
- Container séparé, n'affecte pas le stack principal

### 🚀 Étape 1: Build et démarrage du service FinBERT API

```powershell
# Build l'image FinBERT CPU
docker compose -f "c:\n8n-local-stack\docker-compose.finbert.yml" build

# Démarrer le service en arrière-plan
docker compose -f "c:\n8n-local-stack\docker-compose.finbert.yml" up -d

# Vérifier que le service est opérationnel
Start-Sleep -Seconds 10
Invoke-WebRequest -UseBasicParsing http://localhost:8088/health | Select-Object -ExpandProperty Content
```

### 🚀 Étape 2: Tester l'API FinBERT

```powershell
# Test simple d'analyse de sentiment
$body = @{
    text = "Apple stock surged after great earnings report"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8088/analyze -ContentType 'application/json' -Body $body

# Test batch (multiple textes)
$bodyBatch = @{
    texts = @(
        "NVIDIA rallies on strong AI demand",
        "Tesla recalls vehicles due to safety concerns"
    )
    batch_size = 16
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8088/analyze_batch -ContentType 'application/json' -Body $bodyBatch
```

### 🚀 Étape 3: Utiliser FinBERT dans le pipeline

```powershell
# Définir l'URL de l'API FinBERT comme variable d'environnement
$env:FINBERT_API_URL = "http://finbert_api:8080"

# Collecter les nouvelles avec analyse FinBERT
docker exec -e FINBERT_API_URL=http://finbert_api:8080 n8n_data_architect python3 /data/scripts/batch_loader_v2.py AAPL

# Analyser le sentiment avec FinBERT
docker exec -e FINBERT_API_URL=http://finbert_api:8080 n8n_data_architect python3 /data/scripts/advanced_sentiment_engine_v3.py AAPL

# Pipeline complet pour plusieurs tickers
$tickers = @("AAPL", "MSFT", "GOOGL")
foreach ($ticker in $tickers) {
    Write-Host "📰 FinBERT: Collecte et analyse pour $ticker..." -ForegroundColor Magenta
    docker exec -e FINBERT_API_URL=http://finbert_api:8080 n8n_data_architect python3 /data/scripts/batch_loader_v2.py $ticker
    docker exec -e FINBERT_API_URL=http://finbert_api:8080 n8n_data_architect python3 /data/scripts/advanced_sentiment_engine_v3.py $ticker
}
```

### 🚀 Étape 4: Arrêter le service FinBERT CPU

```powershell
# Arrêter le service
docker compose -f "c:\n8n-local-stack\docker-compose.finbert.yml" down

# Vérifier qu'il est arrêté
docker ps -a | Select-String "finbert_api"
```

---

## Mode FinBERT GPU

### ✅ Avantages
- Utilise votre RTX 2070 Ti pour accélération GPU
- ~10-20x plus rapide que CPU pour batch processing
- Précision identique au mode CPU (~88%)
- Optimisé pour throughput élevé

### ⚠️ Prérequis GPU
- NVIDIA drivers installés (version 525+)
- Docker Desktop avec WSL2 backend
- NVIDIA Container Toolkit configuré

### 🚀 Étape 1: Vérifier l'accès GPU

```powershell
# Vérifier que NVIDIA-SMI fonctionne dans WSL2
wsl -e nvidia-smi

# Tester l'accès GPU depuis Docker
docker run --gpus all --rm nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 🚀 Étape 2: Build et démarrage du service FinBERT GPU

```powershell
# Build l'image FinBERT GPU (peut prendre 5-10 minutes)
docker compose -f "c:\n8n-local-stack\docker-compose.finbert.gpu.yml" build

# Démarrer le service avec accès GPU
docker compose -f "c:\n8n-local-stack\docker-compose.finbert.gpu.yml" up -d

# Attendre que le modèle se charge (30-60 secondes)
Start-Sleep -Seconds 30

# Vérifier le health check
Invoke-WebRequest -UseBasicParsing http://localhost:8089/health | Select-Object -ExpandProperty Content
```

### 🚀 Étape 3: Vérifier l'utilisation GPU

```powershell
# Monitorer l'utilisation GPU en temps réel
docker exec finbert_api_gpu nvidia-smi

# Logs du container pour voir le device utilisé
docker logs finbert_api_gpu 2>&1 | Select-String "device|cuda|GPU"
```

### 🚀 Étape 4: Utiliser FinBERT GPU dans le pipeline

```powershell
# Pipeline avec FinBERT GPU (port 8089)
$env:FINBERT_API_URL = "http://finbert_api_gpu:8080"

# Collecter et analyser avec GPU
docker exec -e FINBERT_API_URL=http://finbert_api_gpu:8080 n8n_data_architect python3 /data/scripts/batch_loader_v2.py AAPL
docker exec -e FINBERT_API_URL=http://finbert_api_gpu:8080 n8n_data_architect python3 /data/scripts/advanced_sentiment_engine_v3.py AAPL

# Batch processing pour maximiser GPU throughput
$tickers = @("AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN")
foreach ($ticker in $tickers) {
    Write-Host "🚀 GPU FinBERT: $ticker..." -ForegroundColor Yellow
    docker exec -e FINBERT_API_URL=http://finbert_api_gpu:8080 n8n_data_architect python3 /data/scripts/batch_loader_v2.py $ticker
    docker exec -e FINBERT_API_URL=http://finbert_api_gpu:8080 n8n_data_architect python3 /data/scripts/advanced_sentiment_engine_v3.py $ticker
}
```

### 🚀 Étape 5: Monitorer les performances GPU

```powershell
# Ouvrir un terminal séparé pour monitoring continu
docker exec finbert_api_gpu sh -c "watch -n 1 nvidia-smi"

# Ou en PowerShell avec boucle
while ($true) {
    Clear-Host
    docker exec finbert_api_gpu nvidia-smi
    Start-Sleep -Seconds 2
}
```

---

## Pipeline Complet de A à Z

### 🎯 Scénario: Analyse complète avec FinBERT GPU

```powershell
# ============================================
# PHASE 1: DÉMARRAGE DES SERVICES
# ============================================

Write-Host "🚀 Phase 1: Démarrage des services..." -ForegroundColor Cyan

# Stack principal (n8n, Ollama, data_architect)
docker-compose up -d

# Service FinBERT GPU
docker compose -f "c:\n8n-local-stack\docker-compose.finbert.gpu.yml" up -d

# Attendre le chargement du modèle
Write-Host "⏳ Attente du chargement du modèle FinBERT GPU (30s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Vérifier les services
$healthCPU = Invoke-WebRequest -UseBasicParsing http://localhost:8088/health -ErrorAction SilentlyContinue
$healthGPU = Invoke-WebRequest -UseBasicParsing http://localhost:8089/health -ErrorAction SilentlyContinue

if ($healthGPU) {
    Write-Host "✅ FinBERT GPU opérationnel" -ForegroundColor Green
} elseif ($healthCPU) {
    Write-Host "✅ FinBERT CPU opérationnel (fallback)" -ForegroundColor Yellow
} else {
    Write-Host "⚠️ Aucun service FinBERT détecté, utilisation de VADER" -ForegroundColor Yellow
}

# ============================================
# PHASE 2: COLLECTE DES DONNÉES
# ============================================

Write-Host "`n🚀 Phase 2: Collecte des données..." -ForegroundColor Cyan

# Liste des tickers à analyser
$tickers = @("AAPL", "MSFT", "GOOGL", "TSLA", "NVDA")

# Collecte des nouvelles avec FinBERT
foreach ($ticker in $tickers) {
    Write-Host "📰 Collecte nouvelles: $ticker" -ForegroundColor White
    docker exec -e FINBERT_API_URL=http://finbert_api_gpu:8080 n8n_data_architect python3 /data/scripts/batch_loader_v2.py $ticker
}

# Collecte des options
Write-Host "📊 Collecte des données d'options..." -ForegroundColor White
docker exec n8n_data_architect python3 /data/scripts/collect_options.py

# ============================================
# PHASE 3: ANALYSE DE SENTIMENT
# ============================================

Write-Host "`n🚀 Phase 3: Analyse de sentiment multi-dimensionnelle..." -ForegroundColor Cyan

foreach ($ticker in $tickers) {
    Write-Host "🧠 Analyse V3: $ticker" -ForegroundColor White
    docker exec -e FINBERT_API_URL=http://finbert_api_gpu:8080 n8n_data_architect python3 /data/scripts/advanced_sentiment_engine_v3.py $ticker
}

# ============================================
# PHASE 4: RÉCUPÉRATION DES RÉSULTATS
# ============================================

Write-Host "`n🚀 Phase 4: Récupération des résultats..." -ForegroundColor Cyan

# Copier les résultats sur le host
docker cp n8n_data_architect:/data/sentiment_analysis .\data\sentiment_analysis

# Afficher un résumé
Write-Host "`n📊 RÉSUMÉ DES ANALYSES:" -ForegroundColor Green
Get-ChildItem .\data\sentiment_analysis\*_latest_v3.json | ForEach-Object {
    $content = Get-Content $_.FullName -Raw | ConvertFrom-Json
    $ticker = $content.ticker
    $score = $content.final_sentiment_score
    $classification = $content.classification
    
    $color = if ($score -gt 0.2) { "Green" } elseif ($score -lt -0.2) { "Red" } else { "Yellow" }
    Write-Host "  $ticker : Score $score | $classification" -ForegroundColor $color
}

Write-Host "`n✅ Pipeline complet terminé!" -ForegroundColor Green
Write-Host "📁 Résultats disponibles dans: .\data\sentiment_analysis\" -ForegroundColor Cyan
```

---

## Vérification et Diagnostic

### 🔍 Vérifier l'état des containers

```powershell
# Lister tous les containers
docker ps -a

# Vérifier les containers du projet
docker ps --filter "name=n8n_data_architect"
docker ps --filter "name=finbert_api"
docker ps --filter "name=finbert_api_gpu"
```

### 🔍 Consulter les logs

```powershell
# Logs du container principal
docker logs n8n_data_architect --tail 50

# Logs FinBERT CPU
docker logs finbert_api --tail 50

# Logs FinBERT GPU
docker logs finbert_api_gpu --tail 50

# Suivre les logs en temps réel
docker logs -f n8n_data_architect
```

### 🔍 Tester la connectivité entre containers

```powershell
# Depuis le container principal vers FinBERT CPU
docker exec n8n_data_architect sh -c "wget -qO- http://finbert_api:8080/health"

# Depuis le container principal vers FinBERT GPU
docker exec n8n_data_architect sh -c "wget -qO- http://finbert_api_gpu:8080/health"

# Test Python de l'API
docker exec n8n_data_architect python3 -c "
import requests
try:
    r = requests.get('http://finbert_api:8080/health', timeout=5)
    print('✅ FinBERT CPU accessible:', r.json())
except Exception as e:
    print('❌ Erreur:', e)
"
```

### 🔍 Vérifier les fichiers de données

```powershell
# Lister les fichiers de nouvelles collectées
docker exec n8n_data_architect sh -c "ls -lh /data/files/companies/*.json"

# Lister les fichiers d'options
docker exec n8n_data_architect sh -c "ls -lh /data/options_data/*.json"

# Lister les rapports de sentiment
docker exec n8n_data_architect sh -c "ls -lh /data/sentiment_analysis/*_latest_v3.json"

# Compter les articles pour un ticker
docker exec n8n_data_architect python3 -c "
import json
with open('/data/files/companies/AAPL_news.json') as f:
    data = json.load(f)
    articles = data.get('articles', [])
    print(f'📰 AAPL: {len(articles)} articles')
"
```

### 🔍 Benchmark de performance

```powershell
# Test de vitesse VADER
Measure-Command {
    docker exec n8n_data_architect python3 -c "
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
vader = SentimentIntensityAnalyzer()
for i in range(100):
    vader.polarity_scores('Apple stock surged after earnings')
"
}

# Test de vitesse FinBERT CPU (API)
Measure-Command {
    $body = @{ text = "Apple stock surged after earnings" } | ConvertTo-Json
    for ($i=0; $i -lt 10; $i++) {
        Invoke-RestMethod -Method Post -Uri http://localhost:8088/analyze -ContentType 'application/json' -Body $body | Out-Null
    }
}

# Test de vitesse FinBERT GPU (API)
Measure-Command {
    $body = @{ text = "Apple stock surged after earnings" } | ConvertTo-Json
    for ($i=0; $i -lt 10; $i++) {
        Invoke-RestMethod -Method Post -Uri http://localhost:8089/analyze -ContentType 'application/json' -Body $body | Out-Null
    }
}
```

### 🔍 Résoudre les problèmes courants

#### Problème: Container n'démarre pas
```powershell
# Vérifier les erreurs
docker logs n8n_data_architect

# Redémarrer le container
docker restart n8n_data_architect

# Reconstruire si nécessaire
docker-compose down
docker-compose up -d --build
```

#### Problème: FinBERT API ne répond pas
```powershell
# Vérifier que le container est démarré
docker ps | Select-String "finbert"

# Vérifier les logs pour erreurs
docker logs finbert_api

# Redémarrer le service
docker compose -f "c:\n8n-local-stack\docker-compose.finbert.yml" restart

# Test de connexion depuis l'hôte
Test-NetConnection -ComputerName localhost -Port 8088
```

#### Problème: GPU non détecté
```powershell
# Vérifier que NVIDIA driver fonctionne dans WSL
wsl -e nvidia-smi

# Vérifier que Docker voit le GPU
docker run --gpus all --rm nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Vérifier les logs du container GPU
docker logs finbert_api_gpu 2>&1 | Select-String "cuda|gpu|device"

# Si "device: cpu" au lieu de "cuda", vérifier la config Docker Desktop:
# Settings > Resources > WSL Integration > Enable integration with additional distros
```

#### Problème: Modèle FinBERT ne se charge pas
```powershell
# Vérifier l'espace disque
docker exec finbert_api df -h /root/.cache/huggingface

# Nettoyer le cache HuggingFace si nécessaire
docker exec finbert_api rm -rf /root/.cache/huggingface/hub

# Redémarrer pour re-télécharger le modèle
docker compose -f "c:\n8n-local-stack\docker-compose.finbert.yml" restart
```

---

## 📊 Comparaison des Modes

| Critère | VADER | FinBERT CPU | FinBERT GPU |
|---------|-------|-------------|-------------|
| **Précision** | ~65% | ~88% | ~88% |
| **Vitesse (texte simple)** | ~0.5ms | ~50ms | ~5-10ms |
| **Vitesse (batch 32)** | ~16ms | ~1.5s | ~150ms |
| **Mémoire** | 50MB | 500MB | 1GB (VRAM) |
| **Setup** | Très simple | Simple | Moyen |
| **Prérequis** | Aucun | Container additionnel | GPU + drivers |
| **Recommandation** | Prototypage rapide | Production CPU | Production GPU |

---

## 🎯 Recommandations

### Pour le développement et tests
- Utiliser **VADER** pour itération rapide
- Valider la logique avant de passer à FinBERT

### Pour la production (volume modéré)
- Utiliser **FinBERT CPU** via API
- Balance entre précision et coût infrastructure

### Pour la production (volume élevé)
- Utiliser **FinBERT GPU** pour maximiser throughput
- ROI positif si > 10K analyses/jour

### Pipeline hybride (recommandé)
```powershell
# Analyse LLM pour titres importants (coût OK, précision max)
# FinBERT pour le bulk (précision élevée, coût raisonnable)
# VADER en fallback si services indisponibles (résilience)
```

---

## 📚 Ressources additionnelles

- **Documentation FinBERT**: https://huggingface.co/ProsusAI/finbert
- **API Reference**: Voir `/health`, `/analyze`, `/analyze_batch` endpoints
- **Logs**: `docker logs <container_name>`
- **Support**: Voir `/docs` dans le repo

---

**Dernière mise à jour:** 23 décembre 2025  
**Auteur:** Pipeline de Sentiment Financier v3
