# -*- coding: utf-8 -*-
"""
🔄 Config Helper: Gestion des configurations de compagnies
Support pour AI_COMPANIES (défaut) et POLITICAL_COMPANIES (politique)

Permet de switcher facilement entre les 2 modes:
- Mode AI: Analyse des grandes tech AI (NVDA, MSFT, etc)
- Mode Political: Analyse basée sur le trading politique (QuiverQuant)
"""

import sys
from pathlib import Path

# Ajouter les chemins
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.companies_config import AI_COMPANIES, PRIVATE_AI_COMPANIES, get_company_by_ticker as get_ai_company

# Importer la config politique si elle existe
try:
    from config.political_companies_config import POLITICAL_COMPANIES, get_company_by_ticker as get_political_company
    POLITICAL_CONFIG_AVAILABLE = True
except ImportError:
    POLITICAL_COMPANIES = []
    POLITICAL_CONFIG_AVAILABLE = False
    def get_political_company(ticker):
        return None


class ConfigManager:
    """
    Gestionnaire de configuration pour les modes d'analyse
    Permet de switcher entre AI_COMPANIES et POLITICAL_COMPANIES
    """
    
    MODE_AI = "ai"
    MODE_POLITICAL = "political"
    MODE_HYBRID = "hybrid"  # Combine les deux
    
    def __init__(self, mode=MODE_AI):
        """
        Initialiser avec un mode spécifique
        
        Args:
            mode: 'ai', 'political', ou 'hybrid'
        """
        self.mode = mode
        self._validate_mode()
        
    def _validate_mode(self):
        """Valider le mode sélectionné"""
        if self.mode == self.MODE_POLITICAL and not POLITICAL_CONFIG_AVAILABLE:
            print("⚠️ Mode politique demandé mais config non disponible")
            print("   Utiliser political_trading_pipeline.py pour générer la config")
            self.mode = self.MODE_AI
    
    def get_companies(self):
        """Retourner les compagnies selon le mode"""
        if self.mode == self.MODE_AI:
            return AI_COMPANIES + PRIVATE_AI_COMPANIES
        elif self.mode == self.MODE_POLITICAL:
            return POLITICAL_COMPANIES
        elif self.mode == self.MODE_HYBRID:
            return list({c['ticker']: c for c in AI_COMPANIES + POLITICAL_COMPANIES}.values())
        return []
    
    def get_public_companies(self):
        """Retourner seulement les compagnies cotées"""
        companies = self.get_companies()
        return [c for c in companies if not c['ticker'].startswith('PRIVATE')]
    
    def get_company_by_ticker(self, ticker):
        """Trouver une compagnie par ticker"""
        if self.mode == self.MODE_AI:
            return get_ai_company(ticker)
        elif self.mode == self.MODE_POLITICAL:
            return get_political_company(ticker)
        elif self.mode == self.MODE_HYBRID:
            result = get_ai_company(ticker)
            if not result:
                result = get_political_company(ticker)
            return result
        return None
    
    def get_tickers(self):
        """Retourner la liste des tickers"""
        return [c['ticker'] for c in self.get_public_companies()]
    
    def switch_mode(self, new_mode):
        """Changer de mode à la volée"""
        self.mode = new_mode
        self._validate_mode()
        return self.mode
    
    def get_mode_info(self):
        """Retourner les infos du mode courant"""
        companies = self.get_public_companies()
        return {
            "mode": self.mode,
            "total_companies": len(companies),
            "tickers": self.get_tickers(),
            "sectors": list(set(c.get('sector', 'Unknown') for c in companies))
        }


# Instance globale pour utilisation simple
_config_manager = None

def get_config_manager(mode=ConfigManager.MODE_AI):
    """Obtenir l'instance du gestionnaire de config"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(mode)
    return _config_manager

def use_ai_mode():
    """Utiliser le mode AI (défaut)"""
    manager = get_config_manager()
    manager.switch_mode(ConfigManager.MODE_AI)
    return manager

def use_political_mode():
    """Utiliser le mode politique"""
    manager = get_config_manager()
    manager.switch_mode(ConfigManager.MODE_POLITICAL)
    if manager.mode != ConfigManager.MODE_POLITICAL:
        raise RuntimeError("Political mode non disponible. Exécuter political_trading_pipeline.py")
    return manager

def use_hybrid_mode():
    """Utiliser le mode hybride (AI + Political)"""
    manager = get_config_manager()
    manager.switch_mode(ConfigManager.MODE_HYBRID)
    return manager


if __name__ == "__main__":
    print("📊 CONFIG HELPER - Tests")
    print("="*80)
    
    # Test mode AI
    print("\n1️⃣ MODE AI:")
    manager_ai = use_ai_mode()
    info = manager_ai.get_mode_info()
    print(f"   Total: {info['total_companies']} companies")
    print(f"   Tickers: {', '.join(info['tickers'][:5])}...")
    print(f"   Sectors: {', '.join(info['sectors'][:3])}")
    
    # Test mode Political
    print("\n2️⃣ MODE POLITICAL:")
    try:
        manager_pol = use_political_mode()
        info = manager_pol.get_mode_info()
        print(f"   Total: {info['total_companies']} companies")
        print(f"   Tickers: {', '.join(info['tickers'][:5])}...")
    except RuntimeError as e:
        print(f"   ⚠️ {e}")
    
    # Test recherche
    print("\n3️⃣ RECHERCHE PAR TICKER:")
    for ticker in ["NVDA", "MSFT", "TSLA"]:
        company = manager_ai.get_company_by_ticker(ticker)
        if company:
            print(f"   {ticker}: {company['name']}")
    
    print("\n✅ Tests complétés")
