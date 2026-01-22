# 📡 Dashboard Smart Signals - Guide Utilisateur

## Vue d'Ensemble

Le **Dashboard Smart Signals** est un outil d'analyse technique intelligente conçu pour répondre à des questions comme:
- **"Pourquoi le prix d'Amazon drop aujourd'hui?"**
- **"Est-ce un bon point d'entrée?"**
- **"L'action est-elle en survente?"**

Il combine des indicateurs techniques classiques, des métriques de valorisation et des signaux "smart money" pour fournir une analyse complète et actio nnable.

## 🚀 Lancement

### Méthode 1: Via VS Code Tasks (Recommandé)
1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. Sélectionner: `📡 Smart Signals (Local - Port 8504)`

### Méthode 2: Ligne de commande
```powershell
# Local (dev)
cd c:\n8n-local-stack
$env:PYTHONUTF8='1'
python -m streamlit run prod/dashboards/generators/dashboard_smart_signals.py --server.port=8504

# Docker (production)
docker exec -d n8n_data_architect sh -c "nohup python3 -m streamlit run /data/scripts/dashboards/generators/dashboard_smart_signals.py --server.port=8504 --server.address=0.0.0.0 > /tmp/dashboard_smart_signals.log 2>&1 &"
```

### Accès
- **URL**: http://localhost:8504
- **Port**: 8504 (évite les conflits avec autres dashboards)

## 📊 Fonctionnalités Principales

### 1. Signaux Intelligents 🚦
Détection automatique des opportunités:
- **🟢 OVERSOLD (Survente)**: RSI < 30 → Potentiel rebond technique
- **🔴 OVERBOUGHT (Surachat)**: RSI > 70 → Prudence, zone de surachat
- **⚠️ CAPITULATION**: Volume spike + baisse > 2% → Possible fin de correction
- **🟢 ACCUMULATION**: Volume spike + hausse > 2% → Institutionnels entrent
- **🟡 NEAR 52W LOW/HIGH**: Position dans le range annuel

### 2. Graphique Technique Multi-Indicateurs 📈

#### Panneau 1: Prix & Tendances
- **Candlesticks** (Open/High/Low/Close)
- **MA20 / MA50 / MA200** (Moyennes mobiles)
- **Bollinger Bands** (Volatilité)
- **Support & Resistance** (Niveaux clés automatiques)

#### Panneau 2: RSI (Relative Strength Index)
- **RSI < 30**: Zone de survente (vert) → Buy signal
- **RSI > 70**: Zone de surachat (rouge) → Sell signal
- **RSI 30-70**: Zone neutre

#### Panneau 3: MACD (Momentum)
- **Histogramme**: Vert = momentum haussier, Rouge = baissier
- **Lignes MACD & Signal**: Croisements = signaux d'entrée/sortie

#### Panneau 4: Volume
- **Barres vertes/rouges**: Selon prix haussier/baissier
- **Ligne jaune**: Moyenne mobile 20 jours
- **Détection automatique des spikes** (>2x la moyenne)

### 3. Métriques de Valorisation 💰

#### Métriques Principales
- **P/E Trailing**: Prix / Bénéfices (12 derniers mois)
  - ✅ <15 = Attractif
  - ⚠️ >30 = Élevé
  
- **P/E Forward**: P/E basé sur bénéfices projetés
  - Delta "Compression" = Bon signe (croissance attendue)
  - Delta "Expansion" = Mauvais signe (ralentissement attendu)
  
- **PEG Ratio**: P/E / Taux de Croissance
  - ✅ <1.0 = GARP (Growth At Reasonable Price) → **OPPORTUNITÉ**
  - ⚠️ 1.0-2.0 = Fair Value
  - 🔴 >2.0 = Surévalué
  - **Note**: Si N/A dans Yahoo Finance, calcul automatique basé sur Earnings Growth

- **Beta**: Volatilité relative au marché
  - <0.7 = Moins volatil que le marché
  - ~1.0 = Similaire au marché
  - >1.3 = Haute volatilité

- **Short Interest**: % d'actions en position short
  - <3% = Normal
  - 10-20% = Élevé
  - >20% = **Risque de Short Squeeze** 🔥

#### Métriques Avancées (Expander)
**Croissance & Qualité**:
- Earnings Growth, Revenue Growth (QoQ & YoY)
- Profit Margin, Operating Margin
- ROE, ROA

**Santé Financière**:
- Debt/Equity, Current Ratio, Quick Ratio
- Dividend Yield, Payout Ratio

**Trading & Sentiment**:
- Target Price (consensus analystes)
- Recommendation (Buy/Hold/Sell)
- Number of Analysts

### 4. Diagnostic Automatique 🔍

Analyse textuelle générée automatiquement incluant:
1. **Mouvement du Jour**: % de variation
2. **Facteurs Clés**:
   - RSI: Survente/Surachat/Neutre
   - MA200: Au-dessus/En-dessous (tendance)
   - Volume: Anomalies (capitulation/accumulation)
   - Valorisation: P/E, PEG dans le contexte
3. **Synthèse**: Biais CONSTRUCTIF / PRUDENT / NEUTRE

### 5. Profil de Volume 📊
- **Timeline de Prix + Volume** (60 derniers jours)
- **Volume at Price** (90 jours): Zones d'accumulation/distribution
- **Étoiles jaunes**: Marquent les spikes de volume (>2x moyenne)

## 🎯 Cas d'Usage Réels

### Cas 1: "Pourquoi Amazon a drop?"
**Workflow**:
1. Sélectionner `AMZN` dans la sidebar
2. **Regarder Signaux**: Ex: "🔴 BEARISH TREND - Prix < MA200"
3. **Vérifier Volume**: Spike + baisse = Capitulation possible
4. **Lire Diagnostic**: Explication des facteurs (géopolitique, marges, etc.)
5. **Check Valorisation**: PEG < 1 ? = Opportunité long-terme malgré court-terme faible

### Cas 2: "C'est un bon point d'entrée?"
**Checklist**:
- ✅ RSI < 35 (survente technique)
- ✅ Prix proche MA200 (support majeur)
- ✅ PEG < 1.5 (croissance pas trop chère)
- ✅ Volume spike récent avec stabilisation (capitulation passée)
- ⚠️ Tendance générale du marché (benchmark VOO/SPY)

### Cas 3: "Position déjà ouverte - Dois-je vendre?"
**Workflow**:
1. Dashboard détecte automatiquement si ticker est dans portfolio (sidebar)
2. Affiche PRU (Prix de Revient Unitaire)
3. **Signaux de sortie**:
   - 🔴 RSI > 75 + Volume spike = Surachat extrême
   - Prix > Target Price des analystes
   - Divergence baissière (prix monte mais RSI descend)

## ⚙️ Configuration

### Personnalisation des Seuils
Modifier `prod/config/smart_signals_config.py`:

```python
RSI_CONFIG = {
    "oversold": 30,  # Changer à 25 pour être plus strict
    "overbought": 70
}

VOLUME_CONFIG = {
    "spike_threshold": 2.0,  # 2x la moyenne = spike
    "capitulation_min_drop": -3.0  # -3% avec spike = capitulation
}
```

### Intégration Questrade
Le dashboard détecte automatiquement les positions du fichier:
`prod/config/portfolio_holdings.json`

Pour synchroniser avec Questrade:
```bash
python prod/pipelines/questrade/questrade_loader.py --token YOUR_TOKEN
```

## 📚 Indicateurs Techniques - Rappels

| Indicateur | Description | Interprétation |
|------------|-------------|----------------|
| **RSI** | Mesure momentum (0-100) | <30 = Survente, >70 = Surachat |
| **MACD** | Momentum + Direction | Histogramme > 0 = Haussier |
| **Bollinger Bands** | Enveloppe de volatilité | Prix touche bande inf = possible rebond |
| **MA200** | Tendance long-terme | Prix > MA200 = Marché haussier |
| **Volume Profile** | Zones de liquidité | Pics = niveaux de support/résistance |
| **OBV** | On-Balance Volume | Divergence = signal précoce |

## 🔄 Workflow Complet (Exemple Amazon - Janvier 2026)

```
1. OBSERVATION: Amazon -2.5% aujourd'hui
2. DASHBOARD CHECK:
   - Signal: ⚠️ CAPITULATION? (Volume 2.8x moyenne)
   - RSI: 28 (Survente technique)
   - Prix: 5% sous MA200
   - PEG: 1.2 (Fair value, calculé manuellement)
   
3. DIAGNOSTIC:
   "Pression baissière due à tensions géopolitiques (droits de douane).
    Volume climatique suggère capitulation. Historiquement, Amazon rebondit
    depuis la MA200. PEG 1.2 indique valorisation raisonnable pour la croissance."
   
4. DÉCISION:
   - Court-terme: Attendre confirmation (RSI remonte > 35)
   - Moyen-terme: Bon point d'entrée si croyance dans fondamentaux
   - Stop-loss: 5% sous MA200
```

## 🛠️ Dépannage

### Erreur: "Aucune donnée disponible"
- Vérifier que le ticker existe sur Yahoo Finance
- Essayer un autre ticker pour tester
- Vérifier connexion internet

### PEG Ratio = N/A malgré corrections
- Certains tickers n'ont pas de données de croissance
- Le dashboard essaie de calculer avec Earnings Growth
- Si toujours N/A: Utiliser P/E Forward comme proxy

### Dashboard lent
- Réduire période d'analyse (sidebar: 3M au lieu de 5Y)
- Désactiver Support/Resistance (calcul intensif)
- Fermer autres dashboards Streamlit

## 📝 Notes Techniques

### Calcul PEG Manuel
Si Yahoo Finance ne fournit pas le PEG:
```python
PEG = (P/E Forward) / (Earnings Growth * 100)
```
Sources essayées dans l'ordre:
1. `earningsGrowth`
2. `earningsQuarterlyGrowth`
3. `revenueGrowth`

### Détection Volume Spike
```python
spike = Volume_actuel > (2.0 * Moyenne_20j)
```

### Support/Resistance
Algorithme de pivots locaux avec fenêtre de 20 jours.
Affiche les 3 niveaux les plus récents.

## 🔗 Dashboards Complémentaires

| Dashboard | Port | Usage |
|-----------|------|-------|
| Smart Signals | 8504 | Analyse technique individuelle |
| Benchmark Beta | 8503 | Comparaison vs VOO/SPY |
| Sentiment Multi-D | 8502 | Analyse LLM + News |
| Timeline | 8501 | Historique événements |

## ⚠️ Avertissement

Ce dashboard est un outil d'aide à la décision, **PAS un conseil financier**.
- Les signaux peuvent être faux (faux positifs/négatifs)
- Toujours faire ses propres recherches (DYOR)
- Considérer le contexte macroéconomique
- Ne jamais investir plus que ce qu'on peut se permettre de perdre

---

**Version**: 1.0  
**Auteur**: AI Data Pipeline Team  
**Dernière MAJ**: 2026-01-21  
**Port**: 8504
