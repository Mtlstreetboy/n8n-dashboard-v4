import subprocess
import time
import sys
import os
import signal
import webbrowser

# Configuration des services
# Format: (Nom, Commande, Port)
SERVICES = [
    {
        "name": "MAIN_DASHBOARD_V5",
        "command": ["python", "-m", "http.server", "8505", "--directory", "prod/dashboards/generators"],
        "port": 8505,
        "url": "http://127.0.0.1:8505/dashboard_v5_dynamic.html"
    },
    {
        "name": "OPTIONS_DASHBOARD",
        "command": ["streamlit", "run", "prod/dashboards/generators/dashboard_options.py", "--server.port", "8500", "--server.headless", "true"],
        "port": 8500
    },
    {
        "name": "NEWS_DASHBOARD",
        "command": ["streamlit", "run", "prod/dashboards/generators/dashboard_news_v2.py", "--server.port", "8502", "--server.headless", "true"],
        "port": 8502
    },
    {
        "name": "BENCHMARK_DASHBOARD",
        "command": ["streamlit", "run", "prod/dashboards/generators/dashboard_benchmark_v2.py", "--server.port", "8503", "--server.headless", "true"],
        "port": 8503
    },
    {
        "name": "SMART_SIGNALS_DASHBOARD",
        "command": ["streamlit", "run", "prod/dashboards/generators/dashboard_smart_signals.py", "--server.port", "8504", "--server.headless", "true"],
        "port": 8504
    }
]

processes = []

def signal_handler(sig, frame):
    print("\n🛑 Arrêt de tous les services...")
    for p in processes:
        print(f"   Terminating {p['name']}...")
        p['process'].terminate()
    print("✅ Tout est arrêté.")
    sys.exit(0)

def main():
    print("🚀 LANCEMENT DU HUB UNIVERSEL DE DASHBOARDS")
    print("===========================================")
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Working directory should be the root of the project (c:\n8n-local-stack)
    # We assume the script is run from there or we adjust if needed.
    # Current CWD is usually passed as c:\n8n-local-stack by the agent tool.
    
    for service in SERVICES:
        print(f"⏳ Démarrage de {service['name']} sur le port {service['port']}...")
        try:
            # We use Popen to start without blocking
            # On Windows, we might need shell=True to find commands properly, especially 'streamlit' if not directly in path
            # But usually full path python -m streamlit is safer. Let's try direct first.
            cmd = service['command']
            
            # Use 'python -m streamlit' if command starts with streamlit to be safer on Windows paths
            if cmd[0] == 'streamlit':
                cmd = ['python', '-m', 'streamlit'] + cmd[1:]
                
            p = subprocess.Popen(cmd, cwd=os.getcwd())
            processes.append({"name": service['name'], "process": p})
            print(f"   ✅ {service['name']} lancé (PID: {p.pid})")
            
        except Exception as e:
            print(f"   ❌ Erreur lancement {service['name']}: {e}")

    print("\n✨ TOUS LES SYSTÈMES SONT OPÉRATIONNELS ✨")
    print("-------------------------------------------")
    print(f"👉 ACCÈS PRINCIPAL: http://127.0.0.1:8505/dashboard_v5_dynamic.html")
    print("-------------------------------------------")
    print("Appuyez sur Ctrl+C pour tout arrêter.")
    
    # Open the main dashboard automatically
    time.sleep(2) # Wait a bit for server to start
    webbrowser.open("http://127.0.0.1:8505/dashboard_v5_dynamic.html")

    # Keep script running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
