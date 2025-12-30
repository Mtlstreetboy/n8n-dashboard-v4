#!/usr/bin/env python3
"""
🔍 Batch Loader Monitor - Temps Réel
Affiche la progression du batch_loader_v2.py en temps réel
"""
import subprocess
import time
import os
from datetime import datetime

def get_process_status():
    """Vérifie si le batch loader tourne"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'n8n_data_architect', 'sh', '-c', 
             'ps aux | grep batch_loader_v2.py | grep -v grep | wc -l'],
            capture_output=True, text=True, timeout=5
        )
        count = int(result.stdout.strip())
        return count > 0, count
    except:
        return False, 0

def get_files_count():
    """Compte les fichiers JSON créés"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'n8n_data_architect', 'sh', '-c',
             'ls -1 /data/files/companies/*_news.json 2>/dev/null | wc -l'],
            capture_output=True, text=True, timeout=5
        )
        return int(result.stdout.strip())
    except:
        return 0

def get_recent_files():
    """Récupère les 5 derniers fichiers modifiés"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'n8n_data_architect', 'sh', '-c',
             'ls -lht /data/files/companies/*_news.json 2>/dev/null | head -n 5'],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except:
        return "Aucun fichier"

def get_log_tail():
    """Récupère les dernières lignes du log"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'n8n_data_architect', 'sh', '-c',
             'tail -n 20 /data/scripts/logs/batch_loader_v2.log 2>/dev/null'],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except:
        return "Aucun log disponible"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print("🚀 Démarrage du monitoring...")
    iteration = 0
    
    try:
        while True:
            clear_screen()
            iteration += 1
            now = datetime.now().strftime("%H:%M:%S")
            
            print("=" * 80)
            print(f"🔍 BATCH LOADER MONITOR - Refresh #{iteration} - {now}")
            print("=" * 80)
            print()
            
            # Status du process
            is_running, proc_count = get_process_status()
            if is_running:
                print(f"✅ Status: ACTIF ({proc_count} processus)")
            else:
                print("❌ Status: ARRÊTÉ")
            print()
            
            # Compteur de fichiers
            files_count = get_files_count()
            print(f"📁 Fichiers collectés: {files_count}/19 tickers")
            progress = (files_count / 19) * 100 if files_count <= 19 else 100
            bar_length = 50
            filled = int(bar_length * progress / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"[{bar}] {progress:.1f}%")
            print()
            
            # Fichiers récents
            print("📄 Derniers fichiers modifiés:")
            print("-" * 80)
            recent = get_recent_files()
            for line in recent.split('\n')[:5]:
                print(line)
            print()
            
            # Log tail
            print("📝 Log (dernières lignes):")
            print("-" * 80)
            log = get_log_tail()
            for line in log.split('\n')[-15:]:
                if line.strip():
                    print(line)
            print()
            
            print("=" * 80)
            print("Appuyez sur Ctrl+C pour quitter | Refresh dans 5 secondes...")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n✋ Monitoring arrêté par l'utilisateur")
        print("Le batch loader continue de tourner en arrière-plan dans le conteneur.")

if __name__ == '__main__':
    main()
