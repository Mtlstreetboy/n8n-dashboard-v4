# 📊 Dashboard d'Options - 5 Visualisations Innovantes

## 🎯 Vue d'ensemble

Ce dashboard offre **5 vues complémentaires** pour analyser les options et détecter le sentiment du marché:

1. **📈 Volatility Smile** - Détecte la nervosité du marché via l'IV
2. **🔥 Volume Heatmap** - Identifie les zones de support/résistance
3. **📊 Open Interest Ladder** - Calcule le Max Pain et les stakes
4. **💰 Money Flow** - Suit les flux d'argent (smart money)
5. **🎯 3D Surface** - Pattern recognition visuel

---

## 🚀 Lancement Rapide

### 1. Collecter les données d'options
```bash
docker exec n8n_data_architect python3 /data/scripts/collect_options.py
```

### 2. Lancer le dashboard
```bash
docker exec -d n8n_data_architect streamlit run /data/scripts/dashboard_options.py --server.port 8501 --server.address 0.0.0.0
```

### 3. Accéder au dashboard
```
http://localhost:8501
```

---

## 📊 Les 5 Visualisations

### 📈 **VUE 1: Volatility Smile**
**Ce qu'on voit:**
- **Taille des points** = Volume (plus gros = plus tradé)
- **Couleur** = Intensité du volume
- **Courbe IV** = Nervosité du marché
- **Barres volume** = Mirror effect calls/puts

**Signaux:**
- Smile prononcé = marché nerveux
- IV puts > calls = peur cachée
- Volume OTM élevé = spéculation

---

### 🔥 **VUE 2: Volume Heatmap**
**Ce qu'on voit:**
- **Couleur verte** = Concentration calls
- **Couleur rouge** = Concentration puts
- **Zones chaudes** = Support/résistance magnétique

**Signaux:**
- Mur de calls à X$ = résistance
- Mur de puts à Y$ = support
- Concentration temporelle = événement attendu (earnings?)

---

### 📊 **VUE 3: Open Interest Ladder**
**Ce qu'on voit:**
- **Barres** = OI par strike (pyramid effect)
- **Courbes** = Argent réel en jeu ($)
- **Max Pain** = Strike où MM perdent le moins

**Signaux:**
- Max pain = aimant de prix
- Notional élevé = stakes importants
- Asymétrie = direction du marché

---

### 💰 **VUE 4: Money Flow Analysis**
**Ce qu'on voit:**
- **5 zones**: Deep OTM, OTM, ATM, ITM, Deep ITM
- **Flow** = Prix × Volume × 100
- **Ratio** = Calls vs Puts money

**Signaux:**
- Flow OTM calls = spéculation bullish
- Flow ITM puts = protection bearish
- Flow ATM = trading actif, momentum

---

### 🎯 **VUE 5: 3D Surface**
**Ce qu'on voit:**
- **Axe X** = Strike
- **Axe Y** = Expiration
- **Axe Z** = Volume (hauteur)
- **Couleur** = Intensité

**Signaux:**
- Pics = Zones d'intérêt massif
- Vallées = Strikes ignorés
- Patterns = Formations répétitives

---

## 🎯 Score Composite

Le dashboard calcule un **Score Composite** qui combine les 5 vues:

```python
Options_Score = (
    Volatility_Skew × 0.25 +      # Peur/Euphorie
    Max_Pain_Distance × 0.20 +    # Attraction magnétique
    Money_Flow_Ratio × 0.30 +     # Où va l'argent
    Volume_Concentration × 0.25   # Conviction
)
```

**Interprétation:**
- **Score > 0.15** = 🚀 Configuration Bullish
- **Score -0.15 à 0.15** = ⏸️ Neutre/Indécis
- **Score < -0.15** = 📉 Configuration Bearish

---

## 🔍 Scénarios Automatiquement Détectés

### **Scénario 1: 🚀 Bullish Setup**
```
✅ Volatility Smile: IV calls > IV puts
✅ Heatmap: Concentration OTM calls
✅ OI Ladder: Max pain en dessous du prix
✅ Money Flow: Flow massif vers OTM calls
✅ 3D Surface: Pic sur calls courts termes
→ Signal: FORTE CONVICTION BULLISH
```

### **Scénario 2: 📉 Bearish Hedge**
```
⚠️ Volatility Smile: Skew élevé vers puts
⚠️ Heatmap: Mur de puts ITM
⚠️ OI Ladder: Notional puts >> calls
⚠️ Money Flow: Flow vers puts ITM
⚠️ 3D Surface: Escalier descendant
→ Signal: PROTECTION MASSIVE ou BEARISH
```

### **Scénario 3: 🔥 Squeeze Setup**
```
🔥 Volatility Smile: IV bas partout
🔥 Heatmap: Concentration extrême ATM
🔥 OI Ladder: Max pain = prix actuel
🔥 Money Flow: Flow équilibré
🔥 3D Surface: Plateau
→ Signal: COMPRESSION, breakout imminent
```

---

## 📊 Intégration avec le Sentiment Global

Pour créer un **Score Final** qui combine News + Options + Momentum:

```python
Final_Sentiment = (
    News_Sentiment × 0.30 +
    Options_Score × 0.50 +        # Poids fort!
    Momentum × 0.20
)
```

**Pourquoi donner plus de poids aux Options?**
- Les options révèlent les **vraies convictions** (argent réel en jeu)
- Les news peuvent être du bruit
- Les options montrent ce que les **institutions** font réellement

---

## 🛠️ Architecture Technique

### Fichiers
```
prod/
├── collect_options.py          # Collecteur de données options (Yahoo Finance)
├── dashboard_options.py        # Dashboard avec 5 visualisations
└── dashboard_sentiment.py      # Dashboard sentiment (News + Options)
```

### Données Stockées
```
/data/options_data/
├── AAPL_calls_20251210_010238.csv      # Données calls
├── AAPL_puts_20251210_010238.csv       # Données puts
├── AAPL_sentiment_20251210_010238.json # Métriques calculées
└── AAPL_latest_sentiment.json          # Dernière version (accès rapide)
```

### Métriques Calculées
```json
{
  "ticker": "AAPL",
  "call_volume": 125000,
  "put_volume": 95000,
  "put_call_ratio_volume": 0.76,
  "call_implied_volatility": 0.245,
  "put_implied_volatility": 0.268,
  "sentiment_label": "bullish",
  "sentiment_score": 0.24,
  "near_term_call_volume": 85000,
  "far_term_call_volume": 40000
}
```

---

## 🔄 Automatisation

### Collecter les options toutes les heures
```bash
# Cron job
0 * * * * docker exec n8n_data_architect python3 /data/scripts/collect_options.py
```

### Script de collection
```python
# collect_options.py utilise companies_config.py
from companies_config import get_all_companies

companies = get_all_companies()
collector = OptionsCollector()
collector.collect_all_companies(companies, days_forward=90)
```

---

## 📈 Exemples d'Utilisation

### Analyser AAPL
1. Ouvrir http://localhost:8502
2. Entrer "AAPL" dans le champ ticker
3. Cliquer "🔍 Analyser"
4. Explorer les 5 onglets

### Interpréter les Résultats

**Exemple 1: Signal Bullish**
```
Options Score: 0.28 (🚀 Bullish)
Put/Call Ratio: 0.65

Tab 1: IV Smile plat, calls actifs
Tab 2: Heatmap concentrée sur calls OTM
Tab 3: Max Pain à $180, prix actuel $185
Tab 4: Flow massif vers OTM calls ($50M)
Tab 5: Pics 3D sur calls court terme

→ Interprétation: Spéculation haussière, momentum fort
```

**Exemple 2: Signal Bearish**
```
Options Score: -0.32 (📉 Bearish)
Put/Call Ratio: 1.45

Tab 1: IV Skew prononcé (puts chers)
Tab 2: Mur de puts ITM
Tab 3: Max Pain au-dessus du prix
Tab 4: Flow vers puts ITM ($75M)
Tab 5: Escalier descendant

→ Interprétation: Protection institutionnelle ou bearish bet
```

---

## 🎓 Concepts Clés

### Max Pain
**Définition:** Strike où l'Open Interest total est maximum

**Utilité:** Le prix tend à graviter vers Max Pain à l'expiration (market makers hedging)

**Calcul:**
```python
total_oi_by_strike = calls_oi + puts_oi
max_pain = strike_with_highest_total_oi
```

### Volatility Skew
**Définition:** Différence d'IV entre puts et calls

**Interprétation:**
- IV_put > IV_call = Marché nerveux (protection demandée)
- IV_call > IV_put = Euphorie (spéculation)

### Money Flow
**Définition:** Volume × Prix × 100 (notional value)

**Utilité:** Montre où va l'argent RÉEL (pas juste le volume)

### Moneyness Zones
- **Deep OTM**: Strike < Prix - 10%
- **OTM**: Strike < Prix - 2%
- **ATM**: Strike ≈ Prix (±2%)
- **ITM**: Strike > Prix + 2%
- **Deep ITM**: Strike > Prix + 10%

---

## 🚨 Limitations

1. **Données retardées**: Yahoo Finance a ~15min de délai
2. **Options illiquides**: Certains strikes ont peu de volume
3. **Market makers**: Peuvent manipuler les prix près de Max Pain
4. **Événements**: Earnings/annonces créent des anomalies temporaires

---

## 🔮 Améliorations Futures

### Détection Automatique de Patterns
- [ ] Squeeze detector (IV crush imminent)
- [ ] Unusual activity alerts (volume >> OI)
- [ ] Divergence detection (options vs stock)
- [ ] Greeks analysis (Delta, Gamma hedging)

### Backtesting
- [ ] Historical accuracy du Score Composite
- [ ] Win rate par scénario (Bullish/Bearish/Squeeze)
- [ ] Optimal thresholds pour les alertes

### Intégration
- [ ] Fusionner avec dashboard_sentiment.py
- [ ] Ajouter Options Score aux métriques globales
- [ ] Créer un "Super Score" (News + Options + Momentum + Fear/Greed)

---

## 📚 Ressources

- **Volatility Smile**: https://www.investopedia.com/terms/v/volatilitysmile.asp
- **Max Pain Theory**: https://www.investopedia.com/terms/m/maxpain.asp
- **Put/Call Ratio**: https://www.investopedia.com/terms/p/putcallratio.asp
- **Greeks**: https://www.investopedia.com/terms/g/greeks.asp

---

## 💡 Tips d'Utilisation

1. **Combiner les vues**: Aucune vue seule ne suffit, il faut le contexte complet
2. **Vérifier le volume**: Ignorer les strikes avec volume < 100
3. **Expirations proches**: Court terme (< 30j) = momentum, Long terme = conviction
4. **Max Pain est un guide**: Pas une garantie, surtout loin de l'expiration
5. **IV vs Historical Vol**: Comparer IV actuelle avec moyenne historique

---

## 🐛 Dépannage

### Dashboard ne charge pas
```bash
# Vérifier que Streamlit tourne
docker exec n8n_data_architect ps aux | grep streamlit

# Relancer si nécessaire
docker exec -d n8n_data_architect streamlit run /data/scripts/dashboard_options.py --server.port 8502 --server.address 0.0.0.0
```

### Pas de données pour un ticker
```bash
# Collecter manuellement
docker exec n8n_data_architect python3 /data/scripts/collect_options.py

# Vérifier les données
docker exec n8n_data_architect ls -lh /data/options_data/ | grep AAPL
```

### Graphiques vides
- Vérifier que les CSV contiennent des données (pas vides)
- Certains tickers n'ont pas d'options (small caps)
- Vérifier les colonnes: `strike`, `volume`, `impliedVolatility`, `openInterest`

---

**Créé le:** 2025-12-09  
**Version:** 1.0  
**Auteur:** n8n-local-stack
