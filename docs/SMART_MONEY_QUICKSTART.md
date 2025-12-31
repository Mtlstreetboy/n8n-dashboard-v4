# 🎯 Smart Money Tracker - Guide de Démarrage Rapide

## Vue d'ensemble

Le Smart Money Tracker est un système **standalone** pour suivre les flux de capitaux des "smart money":
- **Politiciens** (Congrès & Sénat)
- **Initiés d'entreprises** (Form 4)
- **Hedge Funds** (13F - optionnel)

## 📁 Structure des Fichiers

```
n8n-local-stack/
├── smart_money_testing.ipynb           [NOUVEAU] Notebook Jupyter pour tests
├── prod/
│   ├── analysis/
│   │   └── smart_money_analyzer.py     [NOUVEAU] Classe principale
│   └── config/
│       └── smart_money_config.py       [NOUVEAU] Configuration
└── local_files/
    └── smart_money/                    [NOUVEAU] Données collectées
        ├── political_trades/
        ├── insider_trades/
        └── cik_cache.json
```

## 🚀 Démarrage Rapide

### Option 1: Jupyter Notebook (Recommandé pour tests)

1. **Ouvrir le notebook**
   ```powershell
   # Dans VS Code
   # Ouvrir: smart_money_testing.ipynb
   ```

2. **Sélectionner le kernel Python**
   - Utiliser le kernel de votre environnement virtuel `.venv`
   - Ou utiliser le kernel Python système

3. **Exécuter les cellules dans l'ordre**
   - Cellule 1-3: Setup
   - Cellule 4-7: Tests politiques
   - Cellule 8-10: Tests clusters
   - Cellule 11-14: Tests initiés
   - Cellule 15-17: Signaux combinés

### Option 2: Script Python direct

```powershell
# Activer l'environnement virtuel
.\.venv\Scripts\Activate.ps1

# Exécuter le script
python prod/analysis/smart_money_analyzer.py
```

### Option 3: Dans Docker (si vous préférez)

```powershell
# Copier les fichiers dans le container
docker cp prod/analysis/smart_money_analyzer.py n8n_data_architect:/data/scripts/
docker cp prod/config/smart_money_config.py n8n_data_architect:/data/scripts/

# Exécuter
docker exec -it n8n_data_architect python3 /data/scripts/smart_money_analyzer.py
```

## 🔧 Configuration

Modifiez `prod/config/smart_money_config.py` pour ajuster:

### User-Agent SEC (OBLIGATOIRE)
```python
'sec_user_agent': 'VotreNom votre@email.com'  # Requis par SEC
```

### Seuils de détection
```python
'thresholds': {
    'high_conviction_min_value': 100000,  # $100k minimum pour initiés
    'cluster_signal_strength': {
        'weak': 2,    # 2+ politiciens = faible
        'medium': 3,  # 3+ politiciens = moyen
        'strong': 5   # 5+ politiciens = fort
    }
}
```

### Fenêtres temporelles
```python
'analysis_windows': {
    'political_cluster': 14,  # Détection clusters sur 14 jours
    'insider_cluster': 7,     # Détection clusters sur 7 jours
}
```

## 📊 Utilisation du Notebook

### Test 1: Transactions Politiques
```python
# Collecter les transactions (90 jours)
political_df = analyzer.collect_political_trades(
    days_back=90,
    tickers_filter=['NVDA', 'AAPL', 'TSLA']
)

# Détecter les clusters d'achats
clusters_df = analyzer.detect_political_clusters(political_df)
```

**Résultat attendu:**
- DataFrame avec colonnes: `transaction_date`, `politician`, `ticker`, `type`, `value`, `chamber`
- Clusters avec score de confiance 0-100

### Test 2: Transactions d'Initiés
```python
# Collecter Form 4 pour un ticker
insider_df = analyzer.collect_insider_trades('NVDA', days_back=90)

# Filtrer les achats haute conviction
high_conviction_df = analyzer.filter_high_conviction_buys(insider_df)
```

**Résultat attendu:**
- Transactions avec rôle de l'initié (CEO, CFO, Director)
- Score de conviction basé sur: valeur, rôle, cluster
- Flag `is_cluster` si 2+ initiés achètent

### Test 3: Signaux Combinés
```python
# Générer signaux pour plusieurs tickers
combined_df = analyzer.generate_combined_signals(
    tickers=['NVDA', 'AAPL', 'TSLA'],
    days_political=60,
    days_insider=30
)
```

**Résultat attendu:**
- Score politique (0-50)
- Score initié (0-50)
- Score combiné (0-100)
- Recommandation: 🚀 TRÈS BULLISH / 📈 BULLISH / 💡 INTÉRESSANT / 😐 NEUTRE

## 🎨 Visualisations

Le notebook inclut:
- **Graphiques de répartition** (types de transactions, tickers)
- **Histogrammes** (scores de confiance, nombre d'acheteurs)
- **Comparaisons** (political vs insider scores)

## 💾 Export des Données

Tous les résultats sont automatiquement exportés dans:
```
local_files/smart_money_exports/
├── political_trades_20251230_143022.csv
├── political_clusters_20251230_143022.csv
├── insider_trades_NVDA_20251230_143022.csv
├── high_conviction_buys_NVDA_20251230_143022.csv
└── combined_signals_20251230_143022.csv
```

Format: CSV avec horodatage pour analyse ultérieure

## ⚠️ Limitations & Précautions

### Rate Limiting SEC
- **Limite stricte**: 10 requêtes/seconde
- **Implémenté**: 9 req/sec pour marge de sécurité
- **Circuit breaker**: S'ouvre après 5 échecs consécutifs
- **Si bloqué**: Attendre 60 secondes

### Qualité des Données
- **Latence**: Jusqu'à 45 jours pour transactions politiques (STOCK Act)
- **Form 4 manuscrits**: Non parsables (environ 5% des cas)
- **Amendements**: Les Form 4/A corrigent les Form 4 originaux (géré automatiquement)

### Performance
- **Political trades**: ~10 secondes (GitHub + S3)
- **1 ticker insider**: ~30-60 secondes (SEC EDGAR)
- **5 tickers combined**: ~5-10 minutes (rate limit)

## 🐛 Dépannage

### Erreur: `ModuleNotFoundError: No module named 'prod'`
**Cause**: Notebook pas dans le bon répertoire

**Solution**:
```python
# Dans la première cellule du notebook
import sys
sys.path.insert(0, 'C:/n8n-local-stack')  # Chemin absolu
```

### Erreur: `403 Forbidden` (SEC)
**Cause**: User-Agent invalide ou rate limit dépassé

**Solution**:
1. Vérifier `sec_user_agent` dans config (doit contenir un email)
2. Attendre 60 secondes (circuit breaker)
3. Relancer

### Erreur: `CIK not found for ticker`
**Cause**: Ticker invalide ou non référencé SEC

**Solution**:
- Vérifier l'orthographe du ticker
- Utiliser uniquement des tickers US
- Certains ETFs n'ont pas de Form 4

### Warning: `No Form 4 found`
**Ce n'est pas une erreur!**

Signifie simplement qu'aucun initié n'a fait de transaction dans la période demandée.

## 📈 Interprétation des Signaux

### Cluster Politique Très Fort (🔥🔥🔥)
- **5+ politiciens** achètent le même ticker
- **Fenêtre**: 14 jours
- **Interprétation**: Forte conviction bipartisane, souvent avant événement majeur

### Achat Initié Haute Conviction
- **Valeur**: >$100k
- **Rôle**: CEO, CFO, ou Director
- **Code**: P (Open Market Purchase)
- **Interprétation**: Capital personnel à risque = bullish

### Divergence (Alerte ⚠️)
- **Sentiment public positif** MAIS **initiés vendent**
- **Interprétation**: Prudence, insiders savent quelque chose

### Convergence (Signal fort 🚀)
- **Cluster politique** + **Cluster initiés** + **Sentiment positif**
- **Interprétation**: Alignement maximal, opportunité

## 🔄 Workflow Recommandé

1. **Quotidien** (matin):
   ```python
   # Collecter nouveaux trades politiques
   political_df = analyzer.collect_political_trades(days_back=7)
   clusters_df = analyzer.detect_political_clusters(political_df)
   ```

2. **Hebdomadaire** (weekend):
   ```python
   # Analyser tous vos tickers
   combined_df = analyzer.generate_combined_signals(
       tickers=YOUR_WATCHLIST,
       days_political=30,
       days_insider=30
   )
   ```

3. **Mensuel**:
   - Nettoyer les anciens fichiers JSON (>1 an)
   - Vérifier la qualité des données (anomalies)
   - Recalibrer les seuils de scoring

## 🎯 Prochaines Étapes

### Phase 1: Tests (Actuelle)
- ✅ Tester le notebook avec vos tickers
- ✅ Valider la qualité des données collectées
- ✅ Ajuster les seuils dans la config

### Phase 2: Automatisation (Future)
- Intégrer dans `daily_automation.py`
- Ajouter alertes (webhooks n8n)
- Créer dashboard dédié

### Phase 3: Corrélation (Future)
- Croiser avec sentiment 6D existant
- Intégrer dans `dashboard_v4_split.html`
- Backtesting des signaux

## 📚 Ressources

### Documentation SEC
- Form 4: https://www.sec.gov/files/form4data.pdf
- EDGAR API: https://www.sec.gov/edgar/sec-api-documentation
- Rate Limits: https://www.sec.gov/os/webmaster-faq#developers

### Sources de Données
- Senate Stock Watcher: https://github.com/dwyl/senate-stock-watcher-data
- House Stock Watcher: https://housestockwatcher.com

### Bibliothèques Python
- `pandas`: Manipulation de données
- `requests`: Requêtes HTTP
- `lxml`: Parsing XML (Form 4)
- `matplotlib`: Visualisation

## 💬 Support

En cas de problème:
1. Vérifier les logs: `prod/logs/smart_money.log`
2. Consulter la section Dépannage ci-dessus
3. Vérifier la configuration SEC User-Agent
4. Tester avec un seul ticker d'abord (NVDA)

---

**Date de création**: 2025-12-30  
**Version**: 1.0 (Standalone)  
**Status**: ✅ Prêt pour tests
