# -*- coding: utf-8 -*-
"""
⚡ QUICK START - Political Trading Pipeline
Démarrage rapide sans configuration complexe

Usage:
    python quick_start_political.py
"""

import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'services'))
sys.path.insert(0, str(project_root / 'prod'))

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     🎯 POLITICAL TRADING ANALYSIS PIPELINE - QUICK START                    ║
║                                                                              ║
║     Cette application va:                                                   ║
║     1. Récupérer les tickers des politiciens (60 jours)                    ║
║     2. Générer une config compatible                                        ║
║     3. Lancer la collecte et l'analyse                                     ║
║     4. Créer la vue finale                                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# Check requirements
print("🔍 Vérification des dépendances...")
requirements = {
    "pandas": False,
    "numpy": False,
    "quiverquant": False,
}

for lib in requirements:
    try:
        __import__(lib)
        requirements[lib] = True
        print(f"   ✅ {lib}")
    except ImportError:
        print(f"   ❌ {lib} - NON INSTALLÉ")

if not all(requirements.values()):
    print("\n⚠️ Dépendances manquantes. Installation recommandée:")
    print("   pip install pandas numpy")
    print("\nContinuation avec modules disponibles...\n")

# Menu principal
print("""
═══════════════════════════════════════════════════════════════════════════════

📋 MENU PRINCIPAL

1️⃣  Exécuter le pipeline complet
2️⃣  Seulement extraire les tickers
3️⃣  Vérifier la config existante
4️⃣  Afficher les logs du dernier run
5️⃣  Quitter

═══════════════════════════════════════════════════════════════════════════════
""")

while True:
    try:
        choice = input("Choisir une option (1-5): ").strip()
        
        if choice == "1":
            print("\n🚀 Lancement du pipeline complet...\n")
            from automation.run_political_pipeline import run_full_pipeline
            run_full_pipeline()
            break
            
        elif choice == "2":
            print("\n📊 Extraction des tickers...\n")
            from automation.run_political_pipeline import phase_extract_political_tickers
            tickers, df_data, counts = phase_extract_political_tickers()
            print(f"\n✅ Extraction terminée!")
            print(f"   Tickers trouvés: {len(tickers)}")
            print(f"   Top 5: {', '.join(tickers[:5])}")
            break
            
        elif choice == "3":
            print("\n🔍 Vérification de la config...\n")
            try:
                from config.political_companies_config import POLITICAL_COMPANIES
                print(f"✅ Config trouvée!")
                print(f"   {len(POLITICAL_COMPANIES)} compagnies configurées")
                print(f"\n   Top 5 tickers:")
                for i, company in enumerate(POLITICAL_COMPANIES[:5], 1):
                    trades = company.get('political_trades_60d', 0)
                    print(f"      {i}. {company['ticker']}: {trades} trades")
            except ImportError:
                print("❌ Config non trouvée.")
                print("   Exécuter l'option 1 pour générer la config.")
            break
            
        elif choice == "4":
            print("\n📜 Logs du dernier run:\n")
            log_file = project_root / "political_pipeline.log"
            if log_file.exists():
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Afficher les 50 dernières lignes
                    for line in lines[-50:]:
                        print(line.rstrip())
            else:
                print("❌ Pas de logs trouvés.")
            break
            
        elif choice == "5":
            print("\n👋 Au revoir!")
            break
            
        else:
            print("❌ Option invalide. Réessayer (1-5)")
            
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Au revoir!")
        break
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        print("Essayer à nouveau ou vérifier les logs.")
        break

print("\n" + "="*80)
print("📚 Documentation complète: docs/POLITICAL_TRADING_PIPELINE.md")
print("="*80 + "\n")
