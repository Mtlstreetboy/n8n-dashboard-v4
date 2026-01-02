# 💰 Political Trades Collector - Guide d'Utilisation

## 🎯 Objectif

Outil **standalone** qui collecte les trades politiques (Congress, Senate, House) et génère une liste des stocks les plus tradés pour alimenter votre processus d'analyse sentiment.

---

## 🚀 Utilisation

### Dans le Container Docker

```bash
docker exec n8n_data_architect python3 /data/scripts/collect_political_trades.py
```

### Localement (Windows)

```powershell
cd c:\n8n-local-stack
python prod\collection\collect_political_trades.py
```

---

## 📊 Processus Complet

L'outil exécute automatiquement les étapes suivantes:

### 1️⃣ Collecte des Trades
- Congressional Trading (tous les politiciens)
- Senate Trading (Sénat uniquement)
- House Trading (Chambre uniquement)

### 2️⃣ Sauvegarde Données Brutes
- CSV par source avec timestamp
- CSV "latest" (écrase le précédent)

### 3️⃣ Cache avec Historique
- Accumulation progressive (résout le problème des 1000 résultats)
- Déduplication automatique
- Cache en format Parquet pour performance

### 4️⃣ Analyse des Stocks
- Compte les occurrences par ticker
- Identifie les stocks les plus tradés
- Affiche le TOP 20

### 5️⃣ Analyse Sentiment (60 jours)
- Calcule ratio achats/ventes par ticker
- Score de sentiment: -1 (bearish) à +1 (bullish)
- Classification: BULLISH / NEUTRAL / BEARISH

### 6️⃣ Génération Liste pour Analyse
- Filtre les stocks avec minimum de trades (par défaut: 5)
- Combine fréquence + sentiment
- Export CSV + JSON

### 7️⃣ Rapport de Synthèse
- Stats globales par source
- Top stocks identifiés
- Résumé du sentiment

---

## 📁 Fichiers Générés

### Dans `/data/political_trades/` (container) ou `local_files/political_trades/` (local)

```
political_trades/
├── stocks_for_analysis.csv         # 🎯 FICHIER PRINCIPAL
├── stocks_for_analysis.json        # Format JSON
├── collection_summary.json         # Rapport détaillé
├── congressional_trades_latest.csv
├── senate_trades_latest.csv
├── house_trades_latest.csv
├── congressional_trades_20260102_143022.csv  # Avec timestamp
├── senate_trades_20260102_143022.csv
├── house_trades_20260102_143022.csv
└── cache/
    ├── congressional_cache.parquet  # Cache historique
    ├── senate_cache.parquet
    └── house_cache.parquet
```

---

## 🎯 Fichier Principal: `stocks_for_analysis.csv`

Ce fichier contient la liste des stocks à analyser:

| ticker | trade_count | sentiment_score | signal   |
|--------|-------------|-----------------|----------|
| NVDA   | 45          | 0.67            | BULLISH  |
| AAPL   | 38          | -0.15           | NEUTRAL  |
| TSLA   | 32          | -0.55           | BEARISH  |
| ...    | ...         | ...             | ...      |

### Colonnes:
- **ticker**: Symbol du stock
- **trade_count**: Nombre total de trades (60 derniers jours)
- **sentiment_score**: Score -1 (bearish) à +1 (bullish)
- **signal**: BULLISH / NEUTRAL / BEARISH

---

## 🔄 Utilisation dans le Pipeline d'Analyse

### Méthode 1: Analyse Manuelle

```bash
# 1. Collecter les trades politiques
docker exec n8n_data_architect python3 /data/scripts/collect_political_trades.py

# 2. Visualiser la liste générée
docker exec n8n_data_architect cat /data/political_trades/stocks_for_analysis.csv

# 3. Lancer l'analyse sentiment sur ces stocks
# (À implémenter: modifier companies_config.py pour lire ce fichier)
```

### Méthode 2: Intégration dans `daily_automation.py`

```python
# Ajouter dans prod/automation/daily_automation.py

def collect_political_trades():
    """Collecte trades politiques et génère liste stocks"""
    log("💰 Collecte Political Trades...")
    
    success = run_command(
        ['python3', '/data/scripts/collect_political_trades.py'],
        "Collecte Political Trades",
        timeout=600
    )
    
    return success

# Dans la fonction main():
# 1. collect_political_trades()  # NOUVEAU
# 2. collect_news()              # Existant
# 3. collect_options()           # Existant
# 4. analyze_sentiment()         # Existant
```

---

## 📊 Exemples de Sortie

### Console Output

```
[2026-01-02 14:30:22] ======================================================================
[2026-01-02 14:30:22] 💰 DÉBUT COLLECTE TRADES POLITIQUES
[2026-01-02 14:30:22] ======================================================================

[2026-01-02 14:30:22] 1️⃣ Collecte Congressional Trading...
[2026-01-02 14:30:25]    ✅ 1000 trades collectés

[2026-01-02 14:30:25] 2️⃣ Collecte Senate Trading...
[2026-01-02 14:30:28]    ✅ 523 trades collectés

[2026-01-02 14:30:28] 3️⃣ Collecte House Trading...
[2026-01-02 14:30:31]    ✅ 477 trades collectés

[2026-01-02 14:30:31] ======================================================================
[2026-01-02 14:30:31] 📊 ANALYSE DES STOCKS LES PLUS TRADÉS
[2026-01-02 14:30:31] ======================================================================

[2026-01-02 14:30:31] ✅ 234 tickers uniques identifiés

[2026-01-02 14:30:31] 📈 TOP 20 STOCKS LES PLUS TRADÉS:
[2026-01-02 14:30:31] ----------------------------------------------------------------------
[2026-01-02 14:30:31]     1. NVDA   -   45 trades
[2026-01-02 14:30:31]     2. AAPL   -   38 trades
[2026-01-02 14:30:31]     3. TSLA   -   32 trades
[2026-01-02 14:30:31]     4. MSFT   -   28 trades
[2026-01-02 14:30:31]     5. GOOGL  -   24 trades
...

[2026-01-02 14:30:32] ======================================================================
[2026-01-02 14:30:32] 📅 ANALYSE SENTIMENT - 60 DERNIERS JOURS
[2026-01-02 14:30:32] ======================================================================

[2026-01-02 14:30:32] 📊 TOP 10 BULLISH STOCKS:
[2026-01-02 14:30:32] ----------------------------------------------------------------------
[2026-01-02 14:30:32]    NVDA   | Score: +0.67 | Achats:  30 | Ventes:  15
[2026-01-02 14:30:32]    META   | Score: +0.55 | Achats:  18 | Ventes:   8
...

[2026-01-02 14:30:32] ✅ COLLECTE TERMINÉE
[2026-01-02 14:30:32] 🎯 PROCHAINE ÉTAPE:
[2026-01-02 14:30:32]    Utiliser stocks_for_analysis.csv pour lancer l'analyse sentiment
```

---

## 🔧 Configuration

### Seuil Minimum de Trades

Par défaut, seuls les stocks avec **minimum 5 trades** sont inclus dans la liste d'analyse.

Pour modifier:

```python
# Dans collect_political_trades.py, ligne ~380
df_stocks = self.generate_stock_list_for_analysis(
    df_tickers, 
    df_sentiment_agg,
    min_trades=5  # Modifier ici (ex: 10 pour plus sélectif)
)
```

### Période d'Analyse

Par défaut, l'analyse sentiment porte sur les **60 derniers jours**.

Pour modifier:

```python
# Dans collect_political_trades.py, ligne ~186
cutoff_date = datetime.now() - timedelta(days=60)  # Modifier ici
```

---

## 🧠 Smart Features

### 1. Cache Historique
- Résout le problème des 1000 résultats max de l'API
- Accumule les données à chaque exécution
- Après 1 an: jusqu'à 365K trades historiques

### 2. Déduplication Intelligente
- Évite les doublons lors du merge avec le cache
- Basé sur: Politicien + Date + Ticker

### 3. Sentiment Score
- Formule: `(Achats - Ventes) / (Achats + Ventes)`
- Score: -1 (100% ventes) à +1 (100% achats)
- Classifications:
  - **BULLISH**: score > 0.3
  - **NEUTRAL**: -0.3 ≤ score ≤ 0.3
  - **BEARISH**: score < -0.3

---

## 🐛 Dépannage

### Erreur: Token QuiverQuant invalide

```bash
# Vérifier le token
cat services/quiverquant/config.py

# Le token doit être défini:
QUIVERQUANT_TOKEN = "votre_token_ici"
```

### Erreur: Module not found

```bash
# Vérifier que le path est correct
docker exec n8n_data_architect python3 -c "import sys; print(sys.path)"

# Ou installer le package si nécessaire
docker exec n8n_data_architect pip3 install pandas
```

### Aucun fichier généré

```bash
# Vérifier les permissions
docker exec n8n_data_architect ls -la /data/political_trades/

# Créer le dossier manuellement si besoin
docker exec n8n_data_architect mkdir -p /data/political_trades/cache
```

---

## 📈 Prochaines Étapes

1. ✅ **Collecter les trades** avec cet outil
2. 🔄 **Visualiser les résultats** dans `stocks_for_analysis.csv`
3. 🎯 **Sélectionner les stocks** à analyser
4. 🚀 **Lancer l'analyse sentiment** sur ces stocks
5. 📊 **Intégrer** dans le dashboard V4

---

## 📝 Notes Importantes

### Limitations API QuiverQuant
- Maximum 1000 résultats par requête
- Solution: cache avec accumulation progressive
- Exécuter quotidiennement pour historique complet

### Délai de Reporting
- Trades reportés avec 5-45 jours de retard (légal)
- Date de transaction ≠ date de report
- Sentiment = indicateur **anticipé**, pas immédiat

### Fréquence de Collecte Recommandée
- **Daily**: Pour accumulation historique
- **Weekly**: Si peu de nouveaux trades
- **On-demand**: Pour analyse ponctuelle

---

**Créé:** 2 Janvier 2026  
**Version:** 1.0  
**Auteur:** GitHub Copilot
