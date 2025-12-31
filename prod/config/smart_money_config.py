"""
Configuration Smart Money Tracker
===================================

Paramètres centralisés pour l'analyse des flux Smart Money
"""

SMART_MONEY_CONFIG = {
    # ==================== SEC EDGAR ====================
    'sec_user_agent': 'n8n-local-stack research@example.com',  # OBLIGATOIRE pour SEC
    
    # ==================== RATE LIMITS ====================
    'rate_limits': {
        'sec_edgar': 9,        # Requêtes/seconde (limite SEC: 10, marge de sécurité: 9)
        'github': 60,          # Requêtes/minute pour APIs GitHub
        'retry_max': 3,        # Nombre max de tentatives en cas d'échec
        'backoff_base': 2.0    # Multiplicateur pour backoff exponentiel (2^attempt secondes)
    },
    
    # ==================== RÉTENTION DES DONNÉES ====================
    'data_retention_days': 365,  # Nombre de jours à conserver dans les fichiers JSON
    
    # ==================== FENÊTRES D'ANALYSE ====================
    'analysis_windows': {
        'political_cluster': 14,   # Jours pour détecter clusters politiques
        'insider_cluster': 7,      # Jours pour détecter clusters d'initiés
        'min_cluster_size': 2,     # Nombre minimum d'acteurs pour définir un cluster
        'hedge_fund_quarters': 2   # Nombre de trimestres 13F à comparer
    },
    
    # ==================== SEUILS DE SIGNAUX ====================
    'thresholds': {
        # Valeur minimale pour considérer un achat d'initié comme "haute conviction"
        'high_conviction_min_value': 100000,  # $100,000
        
        # Valeur considérée comme "très élevée"
        'very_high_value': 1000000,  # $1,000,000
        
        # Seuils pour clusters politiques
        'cluster_signal_strength': {
            'weak': 2,      # 2+ politiciens
            'medium': 3,    # 3+ politiciens
            'strong': 5     # 5+ politiciens
        },
        
        # Seuils pour changements significatifs dans 13F
        '13f_significant_change_pct': 15,  # Changement > 15% considéré significatif
        
        # Scoring combiné
        'combined_score_thresholds': {
            'very_bullish': 70,    # Score >= 70: 🚀 TRÈS BULLISH
            'bullish': 50,          # Score >= 50: 📈 BULLISH
            'interesting': 30,      # Score >= 30: 💡 INTÉRESSANT
            'neutral': 0            # Score < 30: 😐 NEUTRE
        }
    },
    
    # ==================== POIDS POUR SCORING ====================
    'scoring_weights': {
        # Poids pour le score combiné
        'sentiment_weight': 0.4,      # 40% sentiment 6D
        'smart_money_weight': 0.4,    # 40% Smart Money
        'options_flow_weight': 0.2,   # 20% Options flow
        
        # Poids pour conviction d'initiés
        'insider_value_weight': 0.4,   # 40% basé sur valeur transaction
        'insider_role_weight': 0.3,    # 30% basé sur rôle (CEO > CFO > Director)
        'insider_cluster_weight': 0.3, # 30% si cluster détecté
        
        # Poids pour clusters politiques
        'political_count_weight': 0.5,   # 50% nombre d'acheteurs
        'political_value_weight': 0.3,   # 30% valeur totale
        'political_timing_weight': 0.2   # 20% rapidité du cluster
    },
    
    # ==================== RÔLES D'INITIÉS (IMPORTANCE) ====================
    'insider_roles': {
        'CEO': 30,
        'CHIEF EXECUTIVE OFFICER': 30,
        'CFO': 25,
        'CHIEF FINANCIAL OFFICER': 25,
        'COO': 20,
        'CHIEF OPERATING OFFICER': 20,
        'DIRECTOR': 20,
        'BOARD MEMBER': 20,
        'PRESIDENT': 25,
        'VICE PRESIDENT': 15,
        'VP': 15,
        'OFFICER': 10,
        'SECRETARY': 5,
        'TREASURER': 5,
        'OTHER': 5
    },
    
    # ==================== HEDGE FUNDS À SUIVRE (13F) ====================
    'tracked_hedge_funds': {
        'Berkshire Hathaway': '0001067983',
        'Bridgewater Associates': '0001350694',
        'Renaissance Technologies': '0001037389',
        'ARK Invest': '0001579982',
        'Tiger Global Management': '0001167483',
        'Pershing Square': '0001336528',
        'Soros Fund Management': '0001029160',
        'Icahn Associates': '0000921669',
        'Third Point': '0001040273',
        'Appaloosa Management': '0001135731'
    },
    
    # ==================== CODES DE TRANSACTION FORM 4 ====================
    'form4_transaction_codes': {
        # Codes à INCLURE (signaux valides)
        'include': ['P', 'S'],  # P = Purchase, S = Sale
        
        # Codes à EXCLURE (bruit)
        'exclude': [
            'M',  # Exercise of derivative (options)
            'G',  # Gift / donation
            'F',  # Payment of tax via shares
            'J',  # Other acquisition/disposition
            'D',  # Disposition to issuer (return)
            'I',  # Discretionary transaction
            'C',  # Conversion of derivative
            'A',  # Grant/Award (attribution gratuite)
            'W'   # Acquisition or disposition by will
        ],
        
        # Descriptions
        'descriptions': {
            'P': 'Open Market Purchase (Signal FORT)',
            'S': 'Open Market Sale',
            'M': 'Exercise of options (Ignorer)',
            'G': 'Gift (Ignorer)',
            'F': 'Payment of taxes (Ignorer)',
            'A': 'Grant/Award (Ignorer)'
        }
    },
    
    # ==================== PARAMÈTRES TECHNIQUES ====================
    'technical': {
        'max_parallel_requests': 5,     # Nombre max de requêtes parallèles
        'request_timeout': 15,          # Timeout en secondes pour requêtes HTTP
        'cache_expiry_hours': 24,       # Expiration du cache CIK (heures)
        'circuit_breaker_threshold': 5, # Nb échecs consécutifs avant ouverture circuit
        'circuit_breaker_timeout': 60,  # Secondes avant tentative de récupération
        'log_level': 'INFO',            # DEBUG, INFO, WARNING, ERROR
        'log_file': 'prod/logs/smart_money.log'
    },
    
    # ==================== CHEMINS DE FICHIERS ====================
    'paths': {
        'base_dir': 'local_files/smart_money',
        'political_trades': 'local_files/smart_money/political_trades',
        'insider_trades': 'local_files/smart_money/insider_trades',
        'hedge_funds': 'local_files/smart_money/hedge_funds',
        'clusters': 'local_files/smart_money/clusters',
        'combined_signals': 'local_files/combined_signals',
        'cik_cache': 'local_files/smart_money/cik_cache.json'
    },
    
    # ==================== INTÉGRATION AVEC PIPELINE EXISTANT ====================
    'integration': {
        'enable_smart_money': True,              # Active/désactive le module
        'run_in_daily_automation': True,         # Exécuter dans daily_automation.py
        'fail_silently': True,                   # Ne pas bloquer le pipeline en cas d'erreur
        'sentiment_correlation_enabled': True,   # Activer corrélation avec sentiment 6D
        'options_flow_correlation_enabled': True # Activer corrélation avec options flow
    },
    
    # ==================== ALERTES ====================
    'alerts': {
        'enable_alerts': False,  # À activer quand webhooks configurés
        'alert_thresholds': {
            'cluster_min_buyers': 3,           # Alerter si cluster >= 3 acheteurs
            'insider_min_value': 500000,       # Alerter si achat initié >= $500k
            'combined_score_min': 70           # Alerter si score combiné >= 70
        },
        'webhook_url': None  # URL n8n webhook (à configurer)
    }
}


# ==================== HELPER FUNCTIONS ====================

def get_config(key: str, default=None):
    """
    Récupère une valeur de configuration avec support de chemin pointé
    
    Exemple:
        get_config('thresholds.high_conviction_min_value')
        get_config('rate_limits.sec_edgar', default=9)
    """
    keys = key.split('.')
    value = SMART_MONEY_CONFIG
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def get_insider_role_score(role: str) -> int:
    """
    Retourne le score d'importance pour un rôle d'initié
    
    Args:
        role: Titre de l'initié (ex: "CEO", "Chief Financial Officer")
    
    Returns:
        Score 0-30
    """
    role_upper = role.upper()
    
    for key, score in SMART_MONEY_CONFIG['insider_roles'].items():
        if key in role_upper:
            return score
    
    return 5  # Default pour rôle inconnu


def is_valid_transaction_code(code: str) -> bool:
    """
    Vérifie si un code de transaction Form 4 est valide (non-bruit)
    
    Args:
        code: Code transaction (P, S, M, G, etc.)
    
    Returns:
        True si code valide, False sinon
    """
    include = SMART_MONEY_CONFIG['form4_transaction_codes']['include']
    exclude = SMART_MONEY_CONFIG['form4_transaction_codes']['exclude']
    
    return code in include and code not in exclude


# ==================== VALIDATION ====================

def validate_config():
    """Valide la cohérence de la configuration"""
    errors = []
    
    # Vérifier User-Agent SEC
    if not SMART_MONEY_CONFIG['sec_user_agent'] or '@' not in SMART_MONEY_CONFIG['sec_user_agent']:
        errors.append("sec_user_agent invalide (doit contenir un email)")
    
    # Vérifier rate limit SEC
    if SMART_MONEY_CONFIG['rate_limits']['sec_edgar'] > 10:
        errors.append("rate_limits.sec_edgar ne doit pas dépasser 10 (limite SEC)")
    
    # Vérifier que les poids de scoring somment à 1.0
    weights = SMART_MONEY_CONFIG['scoring_weights']
    total = weights['sentiment_weight'] + weights['smart_money_weight'] + weights['options_flow_weight']
    if abs(total - 1.0) > 0.01:
        errors.append(f"scoring_weights ne somment pas à 1.0 (total: {total})")
    
    if errors:
        raise ValueError("Erreurs de configuration:\n" + "\n".join(f"  - {e}" for e in errors))
    
    print("✅ Configuration validée")


if __name__ == "__main__":
    # Tester la configuration
    validate_config()
    
    print("\n📋 Configuration Smart Money:")
    print(f"  - User-Agent SEC: {SMART_MONEY_CONFIG['sec_user_agent']}")
    print(f"  - Rate limit SEC: {SMART_MONEY_CONFIG['rate_limits']['sec_edgar']} req/sec")
    print(f"  - Seuil haute conviction: ${SMART_MONEY_CONFIG['thresholds']['high_conviction_min_value']:,}")
    print(f"  - Fenêtre cluster politique: {SMART_MONEY_CONFIG['analysis_windows']['political_cluster']} jours")
    print(f"  - Hedge funds suivis: {len(SMART_MONEY_CONFIG['tracked_hedge_funds'])}")
    print(f"  - Intégration pipeline: {'✓' if SMART_MONEY_CONFIG['integration']['enable_smart_money'] else '✗'}")
    
    print("\n🔍 Test fonctions helper:")
    print(f"  - Score CEO: {get_insider_role_score('Chief Executive Officer')}")
    print(f"  - Score CFO: {get_insider_role_score('CFO')}")
    print(f"  - Code P valide: {is_valid_transaction_code('P')}")
    print(f"  - Code M valide: {is_valid_transaction_code('M')}")
    print(f"  - Seuil min value: {get_config('thresholds.high_conviction_min_value')}")
