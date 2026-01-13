#!/usr/bin/env python3
"""
🚀 FULL PIPELINE - De zéro au graphique
--------------------------------------------------------------------
Flux complet:
1. Collecte des news (Yahoo Finance)
2. Analyse sentiment (FinBERT)
3. Génération rapport consolidé
4. Génération dashboard HTML interactif

Usage:
    python full_pipeline.py              # Pipeline complet
    python full_pipeline.py 7            # Derniers 7 jours
    python full_pipeline.py --no-collect # Skip collecte, analyse seulement
"""
import sys
import os
import subprocess
import time
from datetime import datetime

# Environment Detection
if os.path.exists('/data/scripts'):
    COLLECTION_DIR = '/data/scripts/collection'
    DASHBOARD_DIR = '/data/scripts/dashboard'
    PYTHON = 'python3'
else:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    COLLECTION_DIR = os.path.join(PROJECT_ROOT, 'prod', 'collection')
    DASHBOARD_DIR = os.path.join(PROJECT_ROOT, 'prod', 'dashboard')
    PYTHON = sys.executable

# Rich pour affichage
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    class Console:
        def print(self, *args, **kwargs):
            text = str(args[0]) if args else ''
            import re
            text = re.sub(r'\[.*?\]', '', text)
            print(text)

console = Console()


def run_step(step_num: int, script_name: str, args: list = None, description: str = "") -> bool:
    """Exécute une étape du pipeline"""
    script_path = os.path.join(COLLECTION_DIR if 'news' in script_name else DASHBOARD_DIR, script_name)
    
    if not os.path.exists(script_path):
        console.print(f"\n❌ [bold red]ÉTAPE {step_num}: {description}[/bold red]")
        console.print(f"   Script not found: {script_path}", style="red")
        return False
    
    cmd = [PYTHON, script_path] + (args or [])
    
    console.print(f"\n{'='*70}", style="bold yellow")
    console.print(f"[bold yellow]ÉTAPE {step_num}: {description}[/bold yellow]", justify="center")
    console.print(f"{'='*70}", style="bold yellow")
    console.print(f"   📝 Commande: {' '.join(cmd)}", style="dim")
    console.print()
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            timeout=900  # 15 minutes max
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            console.print(f"\n✅ [green]ÉTAPE {step_num} OK ({elapsed:.1f}s)[/green]")
            return True
        else:
            console.print(f"\n❌ [red]ÉTAPE {step_num} FAILED (code {result.returncode})[/red]")
            return False
            
    except subprocess.TimeoutExpired:
        console.print(f"\n❌ [red]ÉTAPE {step_num} TIMEOUT (>900s)[/red]")
        return False
    except Exception as e:
        console.print(f"\n❌ [red]ÉTAPE {step_num} ERREUR: {e}[/red]")
        return False


def generate_sentiment_reports():
    """Génère les rapports de sentiment pour tous les tickers"""
    console.print(f"\n{'='*70}", style="bold cyan")
    console.print("[bold cyan]ÉTAPE 3: Génération Rapports Sentiment (Advanced Engine)[/bold cyan]", justify="center")
    console.print(f"{'='*70}", style="bold cyan")
    
    # Script qui génère les rapports de sentiment pour chaque ticker
    script_path = os.path.join(os.path.dirname(DASHBOARD_DIR), 'analysis', 'analyze_all_sentiment.py')
    
    if not os.path.exists(script_path):
        console.print(f"   ⚠️ Script not found: {script_path}", style="yellow")
        console.print("   ⏭️ Skipping sentiment analysis (utilisez les fichiers existants)", style="yellow")
        return True
    
    cmd = [PYTHON, script_path]
    
    console.print(f"   📝 Commande: {' '.join(cmd)}", style="dim")
    console.print()
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            timeout=600
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            console.print(f"\n✅ [green]Rapports générés OK ({elapsed:.1f}s)[/green]")
            return True
        else:
            console.print(f"\n⚠️ [yellow]Rapports avec avertissements (code {result.returncode})[/yellow]")
            return True  # Continue quand même
            
    except subprocess.TimeoutExpired:
        console.print(f"\n⚠️ [yellow]Timeout - continuer avec les données existantes[/yellow]")
        return True
    except Exception as e:
        console.print(f"\n⚠️ [yellow]Erreur: {e} - continuer avec les données existantes[/yellow]")
        return True


def main():
    """Pipeline principal"""
    # Parser les arguments
    days = "7"  # Défaut: 7 jours
    skip_collect = '--no-collect' in sys.argv
    
    for arg in sys.argv[1:]:
        if arg.isdigit():
            days = arg
            break
    
    console.print("\n" + "="*70, style="bold magenta")
    console.print("[bold magenta]🚀 FULL PIPELINE - De Zéro au Graphique[/bold magenta]", justify="center")
    console.print("="*70, style="bold magenta")
    
    console.print(f"\n📋 Configuration:")
    console.print(f"   📅 Période: {days} jours")
    console.print(f"   📁 Collection: {COLLECTION_DIR}")
    console.print(f"   📊 Dashboard: {DASHBOARD_DIR}")
    console.print(f"   ⏰ Démarré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    pipeline_steps = [
        (1, 'news_collector.py', [days], "Collecte d'articles (Yahoo Finance)"),
        (2, 'news_analyzer.py', [], "Analyse sentiment (FinBERT)"),
        (3, None, None, "Génération rapports sentiment (Advanced Engine)"),
        (4, 'generate_consolidated_data.py', [], "Consolidation données pour dashboard"),
    ]
    
    total_start = time.time()
    results = {}
    step_num = 1
    
    for step in pipeline_steps:
        if step[1] is None:
            # Étape spéciale: génération sentiment
            success = generate_sentiment_reports()
        else:
            # Étape normale
            if skip_collect and step_num == 1:
                console.print(f"\n⏭️ [yellow]ÉTAPE {step_num}: SKIPPED[/yellow]")
                success = True
            else:
                success = run_step(step_num, step[1], step[2], step[3])
        
        results[step_num] = success
        step_num += 1
        
        if not success and step_num <= 2:
            console.print("\n❌ [bold red]Pipeline arrêté - erreur critique[/bold red]")
            return 1
    
    # Rapport final
    total_elapsed = time.time() - total_start
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    console.print("\n" + "="*70, style="bold green")
    console.print("[bold green]📊 RÉSUMÉ FINAL[/bold green]", justify="center")
    console.print("="*70, style="bold green")
    
    results_table = Table(show_header=True, header_style="bold cyan")
    results_table.add_column("Étape", style="cyan")
    results_table.add_column("Résultat", style="green")
    
    step_names = {
        1: "Collecte",
        2: "Analyse sentiment",
        3: "Rapport sentiment",
        4: "Consolidation dashboard"
    }
    
    for step_num, success in results.items():
        status = "✅ OK" if success else "❌ FAILED"
        style = "green" if success else "red"
        results_table.add_row(step_names[step_num], f"[{style}]{status}[/{style}]")
    
    console.print(Panel(results_table, title="Résultats", border_style="green"))
    
    console.print(f"\n   🎯 Total: {success_count}/{total_count} étapes réussies")
    console.print(f"   ⏱️  Durée totale: {total_elapsed:.1f}s ({total_elapsed/60:.1f}min)")
    console.print(f"   🕐 Terminé: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Fichier résultat
    if success_count >= 3:  # Au minimum collecte + analyse + consolidation
        output_dir = os.path.join(
            os.path.dirname(DASHBOARD_DIR) if 'prod' not in DASHBOARD_DIR else os.path.dirname(os.path.dirname(DASHBOARD_DIR)),
            'prod' if 'prod' not in DASHBOARD_DIR else '',
            'dashboard'
        )
        
        # Trouver le dashboard
        dashboard_file = os.path.join(DASHBOARD_DIR, 'dashboard_v4_dynamic.html')
        if os.path.exists(dashboard_file):
            console.print(f"\n📊 [bold green]Dashboard généré![/bold green]")
            console.print(f"   📂 Localisation: {dashboard_file}")
            console.print(f"   🌐 Ouvrir dans le navigateur pour voir les graphiques")
        else:
            console.print(f"\n💾 [yellow]Données consolidées générées[/yellow]")
            console.print(f"   📂 Dashboard: {DASHBOARD_DIR}/dashboard_v4_dynamic.html")
    
    if success_count == total_count:
        console.print("\n🎉 [bold green]Pipeline complet avec succès![/bold green]")
        return 0
    else:
        console.print("\n⚠️ [bold yellow]Pipeline complété avec des avertissements[/bold yellow]")
        return 0


if __name__ == "__main__":
    sys.exit(main())
