"""
Smart Money Tracker - Validation Setup
======================================

Script de validation pour vérifier que tout est correctement configuré
avant de commencer les tests.
"""

import sys
from pathlib import Path
import importlib.util

# Couleurs pour le terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_header(msg):
    print(f"\n{'='*70}")
    print(f"  {msg}")
    print(f"{'='*70}\n")

def check_file_exists(filepath, description):
    """Vérifie l'existence d'un fichier"""
    path = Path(filepath)
    if path.exists():
        print_success(f"{description}: {filepath}")
        return True
    else:
        print_error(f"{description} manquant: {filepath}")
        return False

def check_directory_exists(dirpath, description):
    """Vérifie l'existence d'un répertoire"""
    path = Path(dirpath)
    if path.exists() and path.is_dir():
        print_success(f"{description}: {dirpath}")
        return True
    else:
        print_warning(f"{description} manquant (sera créé): {dirpath}")
        path.mkdir(parents=True, exist_ok=True)
        return True

def check_module_import(module_name, description):
    """Vérifie l'import d'un module Python"""
    try:
        __import__(module_name)
        print_success(f"{description}")
        return True
    except ImportError as e:
        print_error(f"{description} - Erreur: {e}")
        return False

def validate_config():
    """Valide la configuration Smart Money"""
    try:
        from prod.config.smart_money_config import SMART_MONEY_CONFIG, validate_config
        
        # Tester la validation
        validate_config()
        
        # Vérifier le User-Agent
        user_agent = SMART_MONEY_CONFIG.get('sec_user_agent', '')
        if '@' in user_agent and 'example.com' not in user_agent:
            print_success(f"User-Agent SEC configuré: {user_agent}")
            return True
        else:
            print_warning(f"User-Agent SEC par défaut détecté: {user_agent}")
            print(f"           Pensez à le personnaliser dans prod/config/smart_money_config.py")
            return True
    except Exception as e:
        print_error(f"Erreur de configuration: {e}")
        return False

def main():
    print_header("🎯 VALIDATION SMART MONEY TRACKER")
    
    root_dir = Path.cwd()
    print(f"📂 Répertoire de travail: {root_dir}\n")
    
    all_checks = []
    
    # === VÉRIFICATION DES FICHIERS PRINCIPAUX ===
    print_header("📄 Fichiers Principaux")
    
    all_checks.append(check_file_exists(
        "prod/analysis/smart_money_analyzer.py",
        "Script principal"
    ))
    
    all_checks.append(check_file_exists(
        "prod/config/smart_money_config.py",
        "Fichier de configuration"
    ))
    
    all_checks.append(check_file_exists(
        "smart_money_testing.ipynb",
        "Notebook de test"
    ))
    
    all_checks.append(check_file_exists(
        "docs/SMART_MONEY_QUICKSTART.md",
        "Guide de démarrage rapide"
    ))
    
    all_checks.append(check_file_exists(
        "SMART_MONEY_PLAN.md",
        "Plan de développement"
    ))
    
    # === VÉRIFICATION DES RÉPERTOIRES ===
    print_header("📁 Répertoires de Données")
    
    all_checks.append(check_directory_exists(
        "local_files/smart_money",
        "Répertoire racine Smart Money"
    ))
    
    all_checks.append(check_directory_exists(
        "local_files/smart_money/political_trades",
        "Répertoire trades politiques"
    ))
    
    all_checks.append(check_directory_exists(
        "local_files/smart_money/insider_trades",
        "Répertoire trades initiés"
    ))
    
    all_checks.append(check_directory_exists(
        "local_files/smart_money/clusters",
        "Répertoire clusters"
    ))
    
    all_checks.append(check_directory_exists(
        "local_files/smart_money_exports",
        "Répertoire exports"
    ))
    
    all_checks.append(check_directory_exists(
        "prod/logs",
        "Répertoire logs"
    ))
    
    # === VÉRIFICATION DES MODULES PYTHON ===
    print_header("🐍 Modules Python")
    
    all_checks.append(check_module_import("pandas", "pandas"))
    all_checks.append(check_module_import("requests", "requests"))
    all_checks.append(check_module_import("numpy", "numpy"))
    all_checks.append(check_module_import("matplotlib", "matplotlib"))
    all_checks.append(check_module_import("seaborn", "seaborn (optionnel)"))
    
    # === VÉRIFICATION DE LA CONFIGURATION ===
    print_header("⚙️  Configuration")
    
    all_checks.append(validate_config())
    
    # === VÉRIFICATION DES IMPORTS ===
    print_header("📦 Imports Smart Money")
    
    try:
        sys.path.insert(0, str(root_dir))
        from prod.analysis.smart_money_analyzer import SmartMoneyAnalyzer
        print_success("SmartMoneyAnalyzer importable")
        all_checks.append(True)
        
        # Tester l'instanciation
        try:
            analyzer = SmartMoneyAnalyzer()
            print_success("SmartMoneyAnalyzer instanciable")
            all_checks.append(True)
        except Exception as e:
            print_error(f"Erreur d'instanciation: {e}")
            all_checks.append(False)
            
    except ImportError as e:
        print_error(f"Impossible d'importer SmartMoneyAnalyzer: {e}")
        all_checks.append(False)
    
    # === RÉSUMÉ ===
    print_header("📊 RÉSUMÉ")
    
    passed = sum(all_checks)
    total = len(all_checks)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Vérifications réussies: {passed}/{total} ({success_rate:.1f}%)\n")
    
    if passed == total:
        print_success("🎉 Tous les tests sont passés! Le système est prêt.")
        print("\n📖 Prochaines étapes:")
        print("   1. Ouvrir: smart_money_testing.ipynb")
        print("   2. Sélectionner le kernel Python")
        print("   3. Exécuter les cellules dans l'ordre")
        print("\n📚 Documentation: docs/SMART_MONEY_QUICKSTART.md")
        return 0
    else:
        print_error(f"⚠️  {total - passed} vérification(s) échouée(s)")
        print("\n💡 Consultez les erreurs ci-dessus et corrigez-les avant de continuer.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
