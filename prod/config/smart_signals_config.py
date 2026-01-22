# -*- coding: utf-8 -*-
"""
Configuration: Seuils des Indicateurs Techniques pour Smart Signals Dashboard
=============================================================================

Personnalisez ces valeurs selon votre style de trading.
"""

# ============================================================================
# RSI (Relative Strength Index)
# ============================================================================
RSI_CONFIG = {
    "period": 14,           # Période standard
    "oversold": 30,         # Seuil de survente (signal d'achat potentiel)
    "overbought": 70,       # Seuil de surachat (signal de vente potentiel)
    "extreme_oversold": 20, # Survente extrême (signal fort)
    "extreme_overbought": 80  # Surachat extrême (signal fort)
}

# ============================================================================
# MOVING AVERAGES
# ============================================================================
MA_CONFIG = {
    "short_term": 20,       # Court terme (swing trading)
    "medium_term": 50,      # Moyen terme (position trading)
    "long_term": 200,       # Long terme (tendance majeure)
    "golden_cross_signal": True,  # MA50 croise MA200 vers le haut
    "death_cross_signal": True    # MA50 croise MA200 vers le bas
}

# ============================================================================
# BOLLINGER BANDS
# ============================================================================
BOLLINGER_CONFIG = {
    "window": 20,           # Période de la SMA
    "num_std": 2.0,         # Nombre d'écarts-types
    "squeeze_threshold": 0.05  # Seuil de squeeze (faible volatilité)
}

# ============================================================================
# MACD
# ============================================================================
MACD_CONFIG = {
    "fast_period": 12,      # EMA rapide
    "slow_period": 26,      # EMA lente
    "signal_period": 9      # Ligne de signal
}

# ============================================================================
# VOLUME ANALYSIS
# ============================================================================
VOLUME_CONFIG = {
    "spike_threshold": 2.0,     # Ratio pour détecter un spike (2x la moyenne)
    "climax_threshold": 3.0,    # Ratio pour un volume climatique
    "ma_period": 20,            # Période pour la moyenne du volume
    "capitulation_min_drop": -3.0  # % de baisse minimum avec volume spike = capitulation
}

# ============================================================================
# VALUATION THRESHOLDS
# ============================================================================
VALUATION_CONFIG = {
    "pe_cheap": 15,         # P/E considéré bon marché
    "pe_fair": 25,          # P/E considéré fair value
    "pe_expensive": 35,     # P/E considéré cher
    
    "peg_undervalued": 1.0, # PEG < 1 = sous-évalué
    "peg_fair": 1.5,        # PEG ~1.5 = fair
    "peg_overvalued": 2.0,  # PEG > 2 = surévalué
    
    "short_interest_low": 0.03,    # < 3% = normal
    "short_interest_high": 0.10,   # > 10% = élevé (squeeze potentiel)
    "short_interest_danger": 0.20  # > 20% = très élevé
}

# ============================================================================
# SUPPORT/RESISTANCE DETECTION
# ============================================================================
SR_CONFIG = {
    "lookback_window": 20,  # Fenêtre pour détecter les pivots
    "max_levels": 3,        # Nombre max de niveaux à afficher
    "tolerance": 0.02       # Tolérance pour regrouper les niveaux (2%)
}

# ============================================================================
# SIGNAL STRENGTH
# ============================================================================
SIGNAL_STRENGTH = {
    "HIGH": {
        "rsi_distance": 10,     # Distance du seuil RSI pour signal fort
        "volume_ratio": 2.5,    # Ratio volume pour signal fort
        "ma_distance": 0.05     # Distance de MA200 pour signal fort (5%)
    },
    "MEDIUM": {
        "rsi_distance": 5,
        "volume_ratio": 2.0,
        "ma_distance": 0.02
    }
}

# ============================================================================
# QUESTRADE INTEGRATION
# ============================================================================
QUESTRADE_CONFIG = {
    "auto_refresh": False,      # Rafraîchir auto le portfolio au démarrage
    "token_file": "prod/pipelines/questrade/token_store.json",
    "holdings_file": "prod/config/portfolio_holdings.json"
}

# ============================================================================
# ALERT THRESHOLDS (Future Feature)
# ============================================================================
ALERTS_CONFIG = {
    "rsi_alert": True,          # Alerter sur RSI extrêmes
    "volume_alert": True,       # Alerter sur spikes de volume
    "ma200_cross_alert": True,  # Alerter sur croisement MA200
    "price_target_alert": True  # Alerter sur atteinte d'objectif de prix
}

# ============================================================================
# DISPLAY PREFERENCES
# ============================================================================
DISPLAY_CONFIG = {
    "default_period": "1Y",     # Période par défaut
    "show_bollinger": True,
    "show_ma": True,
    "show_sr_levels": True,
    "show_volume_profile": True,
    "theme": "dark",
    "chart_height": 900,
    "volume_chart_height": 400
}
