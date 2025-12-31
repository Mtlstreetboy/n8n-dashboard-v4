# Plan de Développement: Smart Money Tracker
## Intégration dans l'Architecture n8n-local-stack

**Date:** 2025-12-30  
**Objectif:** Ajouter le suivi des flux "Smart Money" (Politiciens, Initiés, Hedge Funds) à l'infrastructure existante d'analyse de sentiment et d'options.

---

## 📋 Vue d'Ensemble

### Synergies avec l'Infrastructure Existante

Votre architecture actuelle suit ce pipeline:
```
collect_options.py → batch_loader_v2.py → advanced_sentiment_engine_v4.py → dashboard_v4_split.html
```

Le système Smart Money va s'intégrer en **parallèle** et **enrichir** vos analyses:

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE EXISTANT                         │
│  Options + News → Sentiment (6D) → Dashboard                │
└─────────────────────────────────────────────────────────────┘
                            ↓ Enrichissement
┌─────────────────────────────────────────────────────────────┐
│                   NOUVEAU: SMART MONEY                       │
│  Politicians + Insiders + 13F → Signals → Dashboard Unified │
└─────────────────────────────────────────────────────────────┘
```

**Avantages de l'intégration:**
1. **Signal de Confirmation:** Les achats d'initiés/politiciens confirment vos signaux de sentiment positif
2. **Early Warning:** Détection d'achats massifs avant que le sentiment public ne change
3. **Corrélation:** Croiser les clusters Smart Money avec vos 6 dimensions de sentiment
4. **Dashboard Unifié:** Vue unique combinant sentiment + flux de capitaux intelligents

---

## 🏗️ Architecture Proposée

### Structure de Fichiers (Alignée avec `prod/`)

```
prod/
├── collection/
│   ├── collect_options.py          [EXISTANT]
│   ├── batch_loader_v2.py          [EXISTANT]
│   ├── collect_political_trades.py [NOUVEAU]
│   ├── collect_insider_trades.py   [NOUVEAU]
│   └── collect_13f_filings.py      [NOUVEAU]
│
├── analysis/
│   ├── advanced_sentiment_engine_v4.py [EXISTANT]
│   ├── smart_money_analyzer.py         [NOUVEAU - Core]
│   ├── cluster_detector.py             [NOUVEAU]
│   └── signal_correlator.py            [NOUVEAU]
│
├── config/
│   ├── companies_config.py         [EXISTANT - 15 tickers]
│   └── smart_money_config.py       [NOUVEAU]
│
├── automation/
│   ├── daily_automation.py         [MODIFIER - Ajouter Smart Money]
│   └── weekly_13f_automation.py    [NOUVEAU - 13F = Trimestriel]
│
├── dashboard/
│   ├── dashboard_v4_split.html     [EXISTANT]
│   └── dashboard_smart_money.html  [NOUVEAU - Ou intégrer à v4]
│
└── utils/
    ├── sec_edgar_client.py         [NOUVEAU]
    ├── rate_limiter.py             [NOUVEAU]
    └── data_validator.py           [NOUVEAU]

local_files/
├── smart_money/                    [NOUVEAU]
│   ├── political_trades/
│   │   ├── senate_YYYYMMDD.json
│   │   └── house_YYYYMMDD.json
│   ├── insider_trades/
│   │   └── {TICKER}_insiders_YYYYMMDD.json
│   ├── hedge_funds/
│   │   └── {CIK}_13f_YYYYMMDD.json
│   └── clusters/
│       └── clusters_YYYYMMDD.json
│
└── combined_signals/               [NOUVEAU]
    └── {TICKER}_combined_YYYYMMDD.json
```

---

## 📅 Plan de Développement (8 Phases)

### **PHASE 1: Fondations (Semaine 1)**
**Objectif:** Poser les bases techniques sans casser l'existant

#### Tâches:
1. **Créer `prod/utils/sec_edgar_client.py`**
   - Classe `SECEdgarClient` avec gestion User-Agent
   - Rate limiting (10 req/sec max SEC)
   - Retry logic + circuit breaker
   - Logging intégré

2. **Créer `prod/config/smart_money_config.py`**
   ```python
   # Exemple de structure
   SMART_MONEY_CONFIG = {
       'sec_user_agent': 'n8n-local-stack research@example.com',
       'rate_limits': {
           'sec_edgar': 10,  # req/sec
           'github': 60      # req/minute
       },
       'data_retention_days': 365,
       'analysis_windows': {
           'political_cluster': 14,  # jours
           'insider_cluster': 7,
           'min_cluster_size': 2
       },
       'thresholds': {
           'high_conviction_min_value': 100000,  # $100k
           'cluster_signal_strength': {
               'weak': 2,
               'medium': 3,
               'strong': 5
           }
       }
   }
   ```

3. **Créer `prod/utils/rate_limiter.py`**
   - Implémentation Token Bucket Algorithm
   - Thread-safe pour éviter ban SEC

4. **Tests unitaires**
   - Tester le client SEC avec des requêtes basiques
   - Vérifier que le rate limiter fonctionne

**Livrable:** Infrastructure technique solide et testée

---

### **PHASE 2: Collection - Transactions Politiques (Semaine 2)**
**Objectif:** Implémenter le suivi Congrès/Sénat

#### Tâches:
1. **Créer `prod/collection/collect_political_trades.py`**
   ```python
   class PoliticalTradesCollector:
       """
       Collecte depuis:
       - Senate Stock Watcher (GitHub JSON)
       - House Stock Watcher (S3 bucket)
       
       Fonctionnalités:
       - Téléchargement incrémental (nouveaux trades uniquement)
       - Normalisation des données (colonnes unifiées)
       - Filtrage par vos 15 tickers (companies_config.py)
       - Export JSON horodaté
       """
   ```

2. **Filtrage intelligent**
   - Ne collecter que les trades concernant vos 15 tickers actuels
   - Éviter de stocker des millions de trades inutiles

3. **Validation des données**
   - Vérifier les champs obligatoires (date, ticker, type)
   - Logger les anomalies

4. **Tests manuels**
   ```bash
   docker exec n8n_data_architect python3 /data/scripts/collect_political_trades.py --days-back 90 --tickers NVDA,AAPL,TSLA
   ```

**Livrable:** JSON quotidien avec trades politiques filtrés

---

### **PHASE 3: Collection - Transactions d'Initiés (Semaine 3)**
**Objectif:** Parser les Form 4 depuis SEC EDGAR

#### Tâches:
1. **Créer `prod/collection/collect_insider_trades.py`**
   ```python
   class InsiderTradesCollector:
       """
       Pour chaque ticker dans companies_config:
       1. Convertir ticker → CIK
       2. Chercher Form 4 (90 derniers jours)
       3. Parser XML → extraire transactions
       4. Filtrer: garder uniquement Code P (Purchase)
       5. Stocker: {TICKER}_insiders_YYYYMMDD.json
       """
   ```

2. **Parser XML robuste**
   - Gérer les Form 4 corrompus (certains sont manuscrits scannés)
   - Fallback vers Form 4/A (amendements)

3. **Détection de signaux**
   - Identifier les achats > $100k (haute conviction)
   - Détecter si CEO/CFO/Director
   - Calculer la valeur totale des transactions

4. **Optimisation performance**
   - Paralléliser les requêtes (mais respecter rate limit)
   - Cacher les CIK → ticker mappings

**Livrable:** Transactions d'initiés par ticker, JSON structuré

---

### **PHASE 4: Analyse - Détection de Clusters (Semaine 4)**
**Objectif:** Identifier les signaux forts (achats groupés)

#### Tâches:
1. **Créer `prod/analysis/cluster_detector.py`**
   ```python
   class ClusterDetector:
       """
       Algorithme de détection:
       
       POLITICAL CLUSTERS:
       - Fenêtre: 14 jours
       - Signal: 2+ politiciens achètent même ticker
       - Force: 5+ politiciens = 🔥🔥🔥 TRÈS FORT
       
       INSIDER CLUSTERS:
       - Fenêtre: 7 jours
       - Signal: 2+ executives (CEO/CFO) achètent
       - Bonus: Si member du board inclus
       
       OUTPUT:
       {
         'ticker': 'NVDA',
         'cluster_date': '2025-12-25',
         'type': 'political',
         'num_buyers': 6,
         'buyers': ['Pelosi', 'McConnell', ...],
         'total_value': 2500000,
         'strength': 'very_strong',
         'confidence_score': 95
       }
       """
   ```

2. **Scoring de confiance**
   - Pondérer par: nombre d'acteurs, valeur totale, rôles, timing
   - Score 0-100

3. **Tests avec données historiques**
   - Vérifier si clusters passés ont prédit des hausses
   - Calibrer les seuils

**Livrable:** Algorithme de détection validé

---

### **PHASE 5: Analyse - Corrélation avec Sentiment (Semaine 5)**
**Objectif:** Croiser Smart Money avec vos 6 dimensions de sentiment

#### Tâches:
1. **Créer `prod/analysis/signal_correlator.py`**
   ```python
   class SignalCorrelator:
       """
       Combine 3 sources:
       1. Votre sentiment 6D (depuis *_latest_v4.json)
       2. Smart Money clusters
       3. Options flow (depuis collect_options.py)
       
       Stratégies de corrélation:
       
       CONVERGENCE HAUSSIÈRE:
       - Sentiment positif (>60/100)
       + Cluster d'achats politiques
       + Initiés achètent
       + Options Call volume élevé
       → Signal: 🚀 TRÈS BULLISH
       
       DIVERGENCE (Alerte):
       - Sentiment positif
       - Mais initiés vendent massivement
       → Signal: ⚠️ MÉFIANCE
       
       EARLY WARNING:
       - Sentiment neutre/négatif
       - Mais cluster d'achats insiders
       → Signal: 💎 OPPORTUNITÉ (Value play)
       """
   ```

2. **Calcul de scores combinés**
   ```python
   combined_score = (
       sentiment_score * 0.4 +
       smart_money_score * 0.4 +
       options_flow_score * 0.2
   )
   ```

3. **Exports pour dashboard**
   - Générer `{TICKER}_combined_YYYYMMDD.json`
   - Structure compatible avec dashboard_v4_split.html

**Livrable:** Signaux combinés avec scoring unifié

---

### **PHASE 6: Collection - Hedge Funds 13F (Semaine 6)**
**Objectif:** Suivre les grands fonds (optionnel, données trimestrielles)

#### Tâches:
1. **Créer `prod/collection/collect_13f_filings.py`**
   ```python
   class HedgeFund13FCollector:
       """
       CIK des Top Funds à suivre:
       - Berkshire Hathaway: 0001067983
       - Bridgewater: 0001350694
       - Renaissance Tech: 0001037389
       - ARK Invest: 0001579982
       
       Fonctionnalités:
       - Parser 13F XML (Information Table)
       - Comparer Q actuel vs Q précédent
       - Identifier: nouvelles positions, sorties, augmentations
       - Filtrer par vos 15 tickers
       """
   ```

2. **Analyse comparative**
   - Détecter les changements significatifs (>15%)
   - Identifier les nouveaux "bets"

3. **Automation trimestrielle**
   - Créer `prod/automation/weekly_13f_automation.py`
   - Vérifier chaque semaine si nouveaux dépôts (45 jours après fin trimestre)

**Livrable:** Suivi des positions institutionnelles (optionnel, valeur ajoutée limitée pour trading court terme)

---

### **PHASE 7: Automation & Orchestration (Semaine 7)**
**Objectif:** Intégrer Smart Money dans le pipeline quotidien

#### Tâches:
1. **Modifier `prod/automation/daily_automation.py`**
   ```python
   # PIPELINE EXISTANT
   # Étape 1: collect_options.py
   # Étape 2: batch_loader_v2.py (news)
   # Étape 3: analyze_all_sentiment.py
   
   # AJOUT: SMART MONEY (entre étape 2 et 3)
   # Étape 2.5a: collect_political_trades.py
   # Étape 2.5b: collect_insider_trades.py (parallèle)
   # Étape 2.5c: detect_clusters.py
   
   # Étape 3: analyze_all_sentiment.py
   # Étape 4 [NOUVEAU]: signal_correlator.py
   
   # Étape 5: Mise à jour dashboard (intégrer Smart Money)
   ```

2. **Gestion d'erreurs**
   - Si Smart Money échoue, ne pas bloquer le pipeline existant
   - Logger les erreurs mais continuer

3. **Performance**
   - Paralléliser Political + Insider collection (2 threads)
   - Timeout: 5 min max pour Smart Money (rate limit SEC)

4. **Tester le pipeline complet**
   ```bash
   docker exec n8n_data_architect python3 /data/scripts/daily_automation.py
   ```

**Livrable:** Pipeline quotidien enrichi avec Smart Money

---

### **PHASE 8: Dashboard & Visualisation (Semaine 8)**
**Objectif:** Interface utilisateur pour exploiter les données

#### Option A: Dashboard Séparé (Recommandé Phase 1)
**Créer `prod/dashboard/dashboard_smart_money.html`**

Sections:
1. **Vue d'ensemble**
   - Nombre de clusters détectés (7 derniers jours)
   - Top 5 tickers avec signaux les plus forts
   - Heatmap: Political vs Insider signals

2. **Transactions Politiques**
   - Tableau: Date, Politicien, Ticker, Type, Valeur
   - Filtre: Chambre (Senate/House), Derniers 30/60/90 jours
   - Graphique: Volume d'achats par ticker

3. **Transactions d'Initiés**
   - Tableau: Ticker, Initié, Rôle, Transaction Value
   - Badge: 🔥 Cluster si 2+ initiés
   - Graphique: Timeline des achats par ticker

4. **Clusters Actifs**
   - Cards avec: Ticker, Nombre d'acteurs, Force du signal
   - Lien vers graphique de prix (TradingView embed)

5. **Signaux Combinés**
   - Tableau: Ticker, Sentiment 6D, Smart Money Score, Combined Score
   - Tri: Par confiance décroissante

**Technologies:**
- React 18 (comme dashboard_v4_split.html)
- Recharts pour graphiques
- Tailwind CSS pour styling
- JSON embedded (même approche que v4)

#### Option B: Intégrer dans dashboard_v4_split.html (Phase 2)
- Ajouter un onglet "Smart Money"
- Afficher les signaux combinés dans la vue principale
- Indicateur visuel: 💰 si Smart Money confirme sentiment positif

**Livrable:** Dashboard fonctionnel et intuitif

---

## 🔧 Améliorations du Script Claude

### Problèmes Identifiés dans le Script Original

1. **Rate Limiting Insuffisant**
   - Risque de ban SEC (10 req/sec limite stricte)
   - Pas de backoff exponentiel

2. **Gestion d'Erreurs Faible**
   - Crashes si XML corrompu
   - Pas de retry sur timeout

3. **Parsing XML Fragile**
   - Assume structure uniforme (certains Form 4 varient)
   - Pas de gestion des Form 4/A (amendements)

4. **Performance**
   - Boucle séquentielle (lent pour 15 tickers)
   - Pas de cache CIK

5. **Validation des Données**
   - Accepte des dates futures
   - Pas de détection d'anomalies (prix négatif, etc.)

### Script Amélioré: `prod/analysis/smart_money_analyzer.py`

Je vais créer une version production-ready avec:
- ✅ Rate limiting robuste
- ✅ Retry logic + circuit breaker
- ✅ Validation des données
- ✅ Parallélisation intelligente
- ✅ Cache CIK → ticker
- ✅ Logging détaillé
- ✅ Tests unitaires intégrés

---

## 📊 Cas d'Usage Concrets

### Cas 1: Confirmation de Signal Haussier
**Scénario:** Votre sentiment 6D détecte NVDA en zone positive (75/100)

**Enrichissement Smart Money:**
- ✅ Cluster politique: 4 sénateurs ont acheté NVDA (14 derniers jours)
- ✅ Initiés: Le CFO a acheté $500k d'actions (marché ouvert)
- ✅ Options: Call volume élevé

**Recommandation:** 🚀 **TRÈS BULLISH** - Convergence totale des signaux

---

### Cas 2: Alerte Divergence
**Scénario:** TSLA sentiment positif (68/100) mais...

**Enrichissement Smart Money:**
- ⚠️ Initiés: CEO et 2 directeurs ont vendu $10M
- ⚠️ 13F: Bridgewater a réduit sa position de 30%

**Recommandation:** ⚠️ **PRUDENCE** - Divergence entre sentiment public et Smart Money

---

### Cas 3: Opportunité Contrarian
**Scénario:** AAPL sentiment négatif (42/100)

**Enrichissement Smart Money:**
- 💎 Cluster d'initiés: 5 executives ont acheté (haute conviction)
- 💎 Berkshire n'a pas vendu (13F stable)

**Recommandation:** 💎 **OPPORTUNITÉ VALUE** - Smart Money achète la baisse

---

## 🛡️ Considérations Techniques & Risques

### Rate Limiting SEC
**Règle stricte:** 10 requêtes/seconde maximum

**Solution:**
```python
from prod.utils.rate_limiter import SECRateLimiter

limiter = SECRateLimiter(max_rate=10, period=1.0)

for ticker in tickers:
    with limiter:
        data = fetch_form4(ticker)
```

### Qualité des Données
**Problèmes connus:**
- Form 4 manuscrits (OCR requis, hors scope)
- Retards de publication (jusqu'à 45 jours)
- Amendements qui annulent/corrigent

**Mitigation:**
- Logger les Form 4 non parsables
- Afficher le délai de publication dans le dashboard
- Gérer les Form 4/A (priorité sur version originale)

### Stockage
**Volume estimé:**
- Political: ~50 trades/jour × 365 = 18k trades/an → ~5 MB/an
- Insiders: ~100 trades/jour × 365 = 36k trades/an → ~10 MB/an
- 13F: ~200 positions × 4 trimestres × 10 fonds = 8k positions/an → ~2 MB/an

**Total: ~20 MB/an** → Négligeable

**Rétention:** Conserver 2 ans de données (40 MB)

### Légalité & Éthique
**Utilisation des données:**
- ✅ Données publiques (SEC, Congrès)
- ✅ Utilisation autorisée (analyse financière)
- ⚠️ Respecter les ToS des APIs tierces
- ⚠️ Ne pas revendre les données brutes

---

## ✅ Checklist de Lancement

### Avant Production
- [ ] Tests unitaires passent (>80% coverage)
- [ ] Rate limiter validé (pas de ban SEC)
- [ ] Pipeline complet exécuté 3× sans erreur
- [ ] Dashboard affiche données réelles
- [ ] Logs configurés (rotation, niveau INFO)
- [ ] Documentation utilisateur rédigée

### Monitoring Post-Lancement
- [ ] Vérifier logs quotidiens (erreurs SEC?)
- [ ] Valider les clusters détectés (faux positifs?)
- [ ] Mesurer corrélation sentiment/Smart Money (sur 30 jours)
- [ ] Ajuster les seuils de scoring si nécessaire

---

## 📚 Ressources & Documentation

### APIs & Sources
- **SEC EDGAR API:** https://www.sec.gov/edgar/sec-api-documentation
- **Senate Stock Watcher:** https://github.com/dwyl/senate-stock-watcher-data
- **House Stock Watcher:** https://housestockwatcher.com/api

### Bibliothèques Python
```bash
# À ajouter dans requirements.txt
requests>=2.31.0
pandas>=2.0.0
lxml>=4.9.0
beautifulsoup4>=4.12.0
python-dateutil>=2.8.2
```

### Guides Techniques
- Form 4 XML Schema: https://www.sec.gov/info/edgar/form4
- 13F-HR Structure: https://www.sec.gov/divisions/investment/13ffaq.htm

---

## 🚀 Roadmap Future (Post-MVP)

### Phase 9: Machine Learning (Optionnel)
- Entraîner un modèle: Smart Money signals → Prédiction de prix (horizon 30j)
- Features: Cluster size, insider roles, sentiment 6D, options flow
- Target: % de variation prix

### Phase 10: Alertes Temps Réel
- Webhook n8n: Notification immédiate si cluster détecté
- Telegram/Discord bot: Alertes sur mobile

### Phase 11: Backtesting
- Tester historiquement: "Si j'avais suivi tous les clusters, quel ROI?"
- Optimiser les seuils de scoring

---

## 🎯 Résumé Exécutif

**Effort Total:** 8 semaines (1 développeur à temps partiel)

**ROI Estimé:**
- ✅ Signaux supplémentaires pour confirmer vos analyses
- ✅ Réduction des faux positifs (divergences détectées)
- ✅ Avantage informationnel vs investisseurs retail

**Risques:**
- ⚠️ Qualité variable des données (Form 4 manuscrits)
- ⚠️ Rate limiting SEC (requiert discipline)
- ⚠️ Latence des données (45 jours max pour STOCK Act)

**Prochaine Étape:**
1. Valider ce plan avec vous
2. Commencer Phase 1 (Fondations)
3. Itérer rapidement avec feedback

---

**Auteur:** GitHub Copilot  
**Date:** 2025-12-30  
**Version:** 1.0
