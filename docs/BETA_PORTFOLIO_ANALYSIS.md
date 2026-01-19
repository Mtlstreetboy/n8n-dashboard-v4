# Rapport Technique : Analyse de Risque et Calcul Automatisé du Bêta Portefeuille

## 1. Introduction Exécutive et Contexte

L'évolution des marchés financiers contemporains impose aux investisseurs d'adopter des méthodologies rigoureuses pour l'évaluation et la gestion du risque. Le **Bêta** ($\beta$) constitue la pierre angulaire de la Théorie Moderne du Portefeuille (MPT) et du Modèle d'Évaluation des Actifs Financiers (CAPM).

Ce rapport détaille la construction d'un **pipeline de calcul automatisé complet** pour le portefeuille Questrade, permettant :
- ✅ Extraction automatique des positions via l'API Questrade
- ✅ Téléchargement et synchronisation des données de marché
- ✅ Calcul des bêtas individuels et du bêta pondéré
- ✅ **Calcul de la volatilité (risque total)**
- ✅ **Calcul du ratio de Sharpe (rendement ajusté du risque)**
- ✅ Analyse holistique du risque systématique et total
- ✅ Visualisation et stratégies d'optimisation

---

## 2. Fondations Mathématiques du Bêta

### 2.1 Définition Canonique : Covariance et Variance

Le bêta d'un actif $i$ relativement à un indice de marché $m$ est défini comme :

$$\beta_i = \frac{\text{Cov}(R_i, R_m)}{\text{Var}(R_m)}$$

Où :
- $R_i$ = rendements de l'actif
- $R_m$ = rendements du marché (benchmark)
- $\text{Cov}(R_i, R_m)$ = covariance conjointe
- $\text{Var}(R_m)$ = variance du marché

**Interprétation:**
- $\beta = 1.0$ : L'actif suit le marché (corrélation parfaite)
- $\beta > 1.0$ : Actif agressif (amplifie les mouvements de marché)
- $\beta < 1.0$ : Actif défensif (amortit les mouvements)
- $\beta < 0$ : Corrélation inverse (propriétés de couverture)

### 2.2 Décomposition Corrélation-Volatilité

Formulation alternative :

$$\beta_i = \rho_{i,m} \times \frac{\sigma_i}{\sigma_m}$$

Où :
- $\rho_{i,m}$ = coefficient de corrélation de Pearson
- $\sigma_i$ = volatilité de l'actif
- $\sigma_m$ = volatilité du marché

**Utilité diagnostique:** Séparer la corrélation (direction) de la volatilité (amplitude).

### 2.3 Approche Économétrique : Régression Linéaire (OLS)

Le bêta est estimé via une régression linéaire :

$$R_{i,t} = \alpha_i + \beta_i R_{m,t} + \epsilon_{i,t}$$

Où :
- $\beta_i$ (pente) = sensibilité systématique
- $\alpha_i$ (intercept) = alpha de Jensen (performance excédentaire)
- $\epsilon_{i,t}$ = risque idiosyncratique
- $R^2$ = coefficient de détermination (fiabilité du bêta)

### 2.4 Bêta Pondéré du Portefeuille

$$\beta_p = \sum_{k=1}^{N} w_k \beta_k$$

Où :
- $w_k = \frac{\text{Valeur}_k}{\text{Valeur Totale}}$ = poids de l'actif $k$
- $\sum w_k = 1.0$ (100%)

**Point critique:** Inclure le cash avec $\beta_{\text{cash}} = 0$ !

Si portefeuille = 70% actions (β=1.2) + 30% cash, alors :
$$\beta_p = 0.7 \times 1.2 + 0.3 \times 0 = 0.84$$

---

## 3. Architecture Technique : Stack Python

### 3.1 Dépendances

| Bibliothèque | Rôle | Justification |
|---|---|---|
| **Pandas** | Manipulation de séries temporelles | DataFrames, pct_change(), alignement dates |
| **NumPy** | Calcul matriciel | Opérations vectorielles, np.cov |
| **YFinance** | Acquisition données de marché | API gratuite Yahoo Finance |
| **SciPy** | Régression linéaire | stats.linregress |
| **Matplotlib** | Visualisation | Graphiques de régression |
| **Requests** | Appels HTTP | API Questrade |

### 3.2 Installation

```bash
# Créer environnement virtuel
python -m venv venv_beta
.\venv_beta\Scripts\activate

# Installer dépendances
pip install pandas numpy yfinance matplotlib scipy requests
```

### 3.3 Structure du Projet

```
prod/
├── pipelines/
│   └── questrade/
│       ├── questrade_loader.py       # Récupération positions
│       └── token_store.json           # Cache tokens OAuth
├── analytics/
│   └── beta_calculator.py             # Moteur de calcul
├── dashboards/
│   ├── generators/
│   │   └── dashboard_beta.py          # Streamlit dashboard
│   └── assets/
│       └── beta_results.json          # Cache résultats
└── config/
    └── portfolio_holdings.json        # Positions Questrade
```

---

## 4. Pipeline de Récupération des Données

### 4.1 L'API Questrade

**Endpoint clé:** `GET /v1/accounts/{id}/positions`

Réponse JSON :
```json
{
    "positions": [
        {
            "symbol": "AAPL",
            "openQuantity": 50,
            "currentMarketValue": 8500.00,
            "currentPrice": 170.00,
            "averageEntryPrice": 150.00
        }
    ]
}
```

**Champs critiques:**
- `symbol` : Correspondance Yahoo Finance
- `currentMarketValue` : Calcul des poids ($w_i$)
- `openQuantity` : Vérification croisée

### 4.2 Gestion des Comptes Multiples

Questrade permet plusieurs comptes (Margin, TFSA, RRSP). Options :

**Option 1 (Recommandée):** Analyser un compte spécifique
```python
# Cibler le compte TFSA
account_id = "53639373"
positions = get_positions(account_id)
```

**Option 2:** Agrégation multi-comptes
```python
# Boucler sur tous les comptes et consolider
all_positions = []
for account in get_accounts():
    all_positions.extend(get_positions(account['number']))
```

---

## 5. Sélection du Benchmark

### 5.1 Pour les Actifs Canadiens (TSX)

⚠️ **Attention:** L'indice `^GSPTSE` sur Yahoo Finance est souvent corrompu (données manquantes, délais).

**Solution proxy recommandée:** XIU.TO (iShares S&P/TSX 60 Index ETF)
- Corrélation ≈ 1.0 avec l'indice composite
- Données fiables et continues
- Liquidité élevée

### 5.2 Pour les Actifs Américains (NASDAQ/NYSE)

**Benchmark:** SPY (S&P 500 ETF) ou QQQ (Nasdaq-100)
- Préférable à `^GSPC` pour la qualité des données
- Inclut les dividendes ajustés
- Liquidité extrême

### 5.3 Déterminisation du Benchmark par Actif

```python
# Logique de sélection
if listing_exchange in ['TSX', 'TSXV', 'CDNX']:
    benchmark = 'XIU.TO'
elif listing_exchange in ['NASDAQ', 'NYSE']:
    benchmark = 'SPY'
else:
    benchmark = 'SPY'  # Default fallback
```

---

## 6. Synchronisation Temporelle des Données

### 6.1 Le Problème des Jours Fériés Disparates

TSX fermé : Action de Grâce (octobre), Noël (25 déc)
NYSE fermé : Thanksgiving (novembre), Independence Day (4 juillet)

**Conséquence:** Dates non alignées → calcul de covariance biaisé

### 6.2 Solution : Jointure Interne

```python
# Créer DataFrame combiné avec synchronisation automatique
data = pd.DataFrame({
    'Stock': stock_returns,
    'Market': market_returns
}).dropna()  # Supprime lignes où une donnée manque
```

Pandas gère automatiquement l'intersection des dates.

### 6.3 Renormailsation : Rendements Arithmétiques

```python
# Rendement simple (recommandé pour bêta quotidien)
returns = prices.pct_change()  # = (P_t - P_{t-1}) / P_{t-1}

# Utiliser toujours 'Adj Close' pour intégrer dividendes et splits
```

---

## 7. Implémentation : Moteur de Calcul

### 7.1 Classe BetaCalculator

```python
import yfinance as yf
import pandas as pd
from scipy import stats

class BetaCalculator:
    def __init__(self, benchmark_symbol):
        self.benchmark_symbol = benchmark_symbol
        self.market_data = None
        
    def download_market_data(self, start_date, end_date):
        """Cache le benchmark pour réutilisation"""
        df = yf.download(self.benchmark_symbol, start=start_date, end=end_date, progress=False)
        self.market_data = df['Adj Close'].pct_change().dropna()
        
    def calculate_beta(self, ticker, start_date, end_date):
        """Calcule β via régression linéaire"""
        try:
            stock_df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if stock_df.empty:
                return {'beta': 0, 'alpha': 0, 'r_squared': 0}
            
            stock_returns = stock_df['Adj Close'].pct_change().dropna()
        except Exception as e:
            print(f"Erreur {ticker}: {e}")
            return {'beta': 0, 'alpha': 0, 'r_squared': 0}
        
        # Alignement des données
        data = pd.DataFrame({
            'Stock': stock_returns,
            'Market': self.market_data
        }).dropna()
        
        if len(data) < 30:
            return {'beta': 1.0, 'alpha': 0, 'r_squared': 0, 'warning': 'Données insuffisantes'}
        
        # Régression linéaire
        slope, intercept, r_value, p_value, std_err = stats.linregress(data['Market'], data['Stock'])
        
        return {
            'beta': slope,
            'alpha': intercept,
            'r_squared': r_value ** 2,
            'correlation': r_value,
            'p_value': p_value,
            'n_obs': len(data)
        }
```

### 7.2 Processus Principal

```python
def analyze_portfolio(positions, start_date, end_date):
    """Agrège les bêtas pondérés"""
    
    # Initialiser calculateurs par devise
    beta_calc_cad = BetaCalculator('XIU.TO')
    beta_calc_usd = BetaCalculator('SPY')
    
    # Télécharger benchmarks une seule fois
    beta_calc_cad.download_market_data(start_date, end_date)
    beta_calc_usd.download_market_data(start_date, end_date)
    
    # Calcul du poids total
    total_value = sum(p['currentMarketValue'] for p in positions)
    
    results = []
    weighted_beta = 0
    
    for position in positions:
        symbol = position['symbol']
        market_value = position['currentMarketValue']
        weight = market_value / total_value
        
        # Déterminer le benchmark (TSX vs NYSE)
        # Ici on suppose une détection simple par suffixe
        if symbol.endswith('.TO') or symbol.endswith('.V'):
            yahoo_symbol = symbol
            calc = beta_calc_cad
        else:
            yahoo_symbol = symbol
            calc = beta_calc_usd
        
        # Calculer le bêta
        metrics = calc.calculate_beta(yahoo_symbol, start_date, end_date)
        beta = metrics.get('beta', 0)
        
        # Contribution au risque
        contribution = beta * weight
        weighted_beta += contribution
        
        results.append({
            'Symbol': symbol,
            'Weight (%)': round(weight * 100, 2),
            'Beta': round(beta, 2),
            'Risk Contribution': round(contribution, 3),
            'R²': round(metrics.get('r_squared', 0), 3)
        })
    
    return pd.DataFrame(results), weighted_beta
```

---

## 8. Traitement des Cas Spéciaux

### 8.1 Cash et Liquidités

```python
# Ajouter une ligne cash explicite
cash_position = {
    'symbol': 'CASH',
    'currentMarketValue': cash_balance,
    'beta': 0  # Par définition
}
```

### 8.2 Marge (Levier Financier)

Si compte sur marge (valeur nette < positions totales) :

```python
# Poids du cash devient négatif (dette)
# Poids actions > 100%
# Bêta total = Σ(w_i * β_i) amplifie mécaniquement
# Exemple: 150% actions (β=1.2) - 50% cash (β=0) = β_p = 1.8
```

### 8.3 Devises Mixtes (CAD/USD)

Convertir en devise de référence (CAD) via taux courant :

```python
# Récupérer taux USD/CAD
exchange_rate = yf.download('CAD=X', period='1d')['Close'].iloc[-1]

# Convertir positions USD
market_value_cad = market_value_usd * exchange_rate
```

---

## 9. Visualisation et Analyse Avancée

### 9.1 Graphique de Régression

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.scatter(data['Market'], data['Stock'], alpha=0.5)
ax.plot(data['Market'], slope * data['Market'] + intercept, 'r-', linewidth=2)
ax.set_xlabel(f'Rendement Benchmark')
ax.set_ylabel(f'Rendement {ticker}')
ax.set_title(f'Régression β = {slope:.2f}, R² = {r_squared:.3f}')
plt.show()
```

### 9.2 Rolling Beta (Bêta Glissant)

Détecte les changements structurels de risque :

```python
rolling_cov = data.rolling(window=60).cov()
rolling_var = data['Market'].rolling(window=60).var()
rolling_beta = rolling_cov / rolling_var

rolling_beta.plot(title='Évolution du Bêta (fenêtre 60j)')
```

---

## 10. Stratégies de Portefeuille

### 10.1 Portefeuille Zéro-Bêta

Objectif: $\beta_p = 0$ (risque systématique éliminé)

```python
# Combiner actifs long (β>0) et short (β<0)
# Ou utiliser ETFs inverses
# Génère alpha pur, indépendant du marché
```

### 10.2 Rotation Sectorielle par Bêta

```python
# Identifier les "contributeurs de risque" (Poids × Bêta élevés)
contributions = df['Weight (%)'] * df['Beta']
high_risk = df.nlargest(3, contributions)

print("Top 3 contributeurs de risque:")
print(high_risk)
```

---

## 11. Limitations et Considérations

### 11.1 Hypothèses du Modèle CAPM

- ✅ Marché efficace (prix ajustés)
- ❌ Suppose relation linéaire (non vrai en crises)
- ❌ Bêta historique ≠ bêta futur
- ❌ Ne capture pas événements systémiques rares

### 11.2 Qualité des Données

- Yahoo Finance: Données ajustées pour dividendes ✅
- ^GSPTSE: Données corrompues ❌ (utiliser XIU.TO)
- Délai d'un jour sur données de marché

### 11.3 Seuils Minimaux

- Min 30 jours de données historiques
- R² < 0.3 : Bêta peu fiable
- p-value > 0.05 : Bêta non significatif statistiquement

---

## 12. Conclusion

L'automatisation du calcul du bêta via Python + Questrade API permet :

✅ Mesure quantitative précise du risque systématique  
✅ Dépassement des limitations des interfaces web  
✅ Diagnostic de la nature du risque (corrélation vs volatilité)  
✅ Fondation pour stratégies avancées (Zero-Beta, rotation sectorielle)  

Cette infrastructure est évolutive vers :
- Optimisation Mean-Variance de Markowitz
- Calcul de Value at Risk (VaR)
- Modèles GARCH pour volatilité dynamique
- Machine Learning pour prédiction de bêta futur

---

**Date:** Janvier 2026  
**Plateforme:** Questrade + VS Code + Python 3.10+  
**Statut:** Production
