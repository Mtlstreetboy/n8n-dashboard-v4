"""
QuiverQuant API Configuration
=============================

Credentials pour accès API QuiverQuant
Créé: 2025-12-31
"""

# QuiverQuant API Credentials
QUIVERQUANT_USERNAME = "bibep"
QUIVERQUANT_TOKEN = "5f04adc7e07958d777b52aef00674d3451a365ff"

# API Base URLs
API_BASE_URL = "https://api.quiverquant.com/beta"
API_LIVE_URL = f"{API_BASE_URL}/live"
API_HISTORICAL_URL = f"{API_BASE_URL}/historical"
API_BULK_URL = f"{API_BASE_URL}/bulk"

# Headers template
def get_headers():
    """Retourne les headers nécessaires pour les requêtes API"""
    return {
        'accept': 'application/json',
        'X-CSRFToken': 'TyTJwjuEC7VV7mOqZ622haRaaUr0x0Ng4nrwSRFKQs7vdoBcJlK9qjAS69ghzhFu',
        'Authorization': f"Token {QUIVERQUANT_TOKEN}"
    }
