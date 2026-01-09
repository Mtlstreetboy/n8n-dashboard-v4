#!/usr/bin/env python3
"""
🚀 NEWS PIPELINE V3 - Collecte + Analyse en deux étapes
--------------------------------------------------------------------
Wrapper qui exécute:
1. news_collector.py (Yahoo Finance - collecte d'articles)
2. news_analyzer.py (FinBERT - analyse sentiment)

Usage:
    python news_pipeline.py              # Pipeline complet
    python news_pipeline.py 7            # Derniers 7 jours
    python news_pipeline.py --collect    # Collecte uniquement
    python news_pipeline.py --analyze    # Analyse uniquement
"""
import sys
import os
import subprocess
import time
from datetime import datetime

# Environment Detection
if os.path.exists('/data/scripts'):
    SCRIPT_DIR = '/data/scripts/collection'
    PYTHON = 'python3'
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PYTHON = sys.executable

# Rich pour affichage
try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    class Console:
        def print(self, *args, **kwargs):
            text = str(args[0]) if args else ''
            # Remove rich markup
            import re
            text = re.sub(r'\[.*?\]', '', text)
            print(text)

console = Console()


def run_script(script_name: str, args: list = None, description: str = "") -> dict:
    """Exécute un script Python et capture le résultat"""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    
    if not os.path.exists(script_path):
        return {
            'success': False,
            'error': f'Script not found: {script_path}'
        }
    
    cmd = [PYTHON, script_path] + (args or [])
    
    console.print(f"\n🚀 [bold cyan]{description}[/bold cyan]")
    console.print(f"   Commande: {' '.join(cmd)}", style="dim")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Afficher output en temps réel
            text=True,
            timeout=600  # 10 minutes max
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            console.print(f"   ✅ Terminé en {elapsed:.1f}s", style="green")
            return {'success': True, 'duration': elapsed}
        else:
            console.print(f"   ❌ Échec (code {result.returncode})", style="red")
            return {'success': False, 'code': result.returncode, 'duration': elapsed}
            
    except subprocess.TimeoutExpired:
        console.print(f"   ⏱️ Timeout après 600s", style="yellow")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        console.print(f"   ❌ Erreur: {e}", style="red")
        return {'success': False, 'error': str(e)}


def main():
    """Pipeline principal"""
    # Parser les arguments
    days = "40"  # Défaut
    collect_only = '--collect' in sys.argv
    analyze_only = '--analyze' in sys.argv
    
    for arg in sys.argv[1:]:
        if arg.isdigit():
            days = arg
            break
    
    console.print("\n" + "="*70, style="bold yellow")
    console.print("🚀 NEWS PIPELINE V3", style="bold yellow", justify="center")
    console.print("="*70, style="bold yellow")
    
    console.print(f"\n📅 Période: {days} jours")
    console.print(f"⏰ Démarré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    total_start = time.time()
    
    # ÉTAPE 1: Collecte (Yahoo Finance)
    if not analyze_only:
        results['collect'] = run_script(
            'news_collector.py',
            [days],
            "ÉTAPE 1: Collecte d'articles (Yahoo Finance)"
        )
    
    # ÉTAPE 2: Analyse (FinBERT)
    if not collect_only:
        results['analyze'] = run_script(
            'news_analyzer.py',
            [],
            "ÉTAPE 2: Analyse sentiment (FinBERT)"
        )
    
    # Rapport final
    total_elapsed = time.time() - total_start
    
    console.print("\n" + "="*70, style="bold green")
    console.print("📊 RÉSUMÉ DU PIPELINE", style="bold green", justify="center")
    console.print("="*70, style="bold green")
    
    success_count = sum(1 for r in results.values() if r.get('success'))
    total_count = len(results)
    
    console.print(f"\n   ✅ Étapes réussies: {success_count}/{total_count}")
    console.print(f"   ⏱️  Durée totale: {total_elapsed:.1f}s ({total_elapsed/60:.1f}min)")
    console.print(f"   🕐 Terminé: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == total_count:
        console.print("\n🎉 Pipeline terminé avec succès!", style="bold green")
        return 0
    else:
        console.print("\n⚠️ Pipeline terminé avec des erreurs", style="bold yellow")
        return 1


if __name__ == "__main__":
    sys.exit(main())
