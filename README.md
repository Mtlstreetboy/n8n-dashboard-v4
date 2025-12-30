# 🤖 n8n Local Stack - Agentic AI avec Ollama

Architecture de développement pour l'automatisation intelligente avec traitement local des LLMs.

## 📊 Diagrammes d'Architecture

Ouvrez les fichiers `.mmd` avec l'extension VS Code **Markdown Preview Mermaid Support** ou collez-les dans [mermaid.live](https://mermaid.live) pour visualisation interactive.

### Diagrammes disponibles :

1. **`architecture.mmd`** : Vue d'ensemble du système (composants et flux de données)
2. **`workflow-example.mmd`** : Séquence d'exécution d'un workflow agentique typique
3. **`usage-guide.mmd`** : Guide étape par étape pour développer et maintenir

## 🚀 Démarrage Rapide

### Lancer la stack
```powershell
docker-compose up -d
```

### Accéder à n8n
- URL : http://localhost:5678
- User : `admin`
- Password : `supersecurepassword`

### Télécharger un modèle IA
```powershell
# Modèle recommandé (8B paramètres - Standard)
docker exec -it ollama_local_ai ollama run llama3

# Modèle plus puissant (70B - Nécessite 32GB+ RAM)
docker exec -it ollama_local_ai ollama run llama3:70b

# Modèle français optimisé
docker exec -it ollama_local_ai ollama run mistral
```

## 📁 Structure du Projet

```
n8n-local-stack/
├── docker-compose.yml       # Définition de la stack
├── Dockerfile               # Image n8n custom avec Python
├── .env                     # Secrets (ne pas commiter)
├── local_scripts/           # 🐍 Vos scripts Python (mappés dans n8n)
│   └── clean_data.py        # Exemple de traitement de données
├── local_files/             # 📁 Fichiers de données (CSV, JSON)
├── architecture.mmd         # 📊 Diagramme architecture globale
├── workflow-example.mmd     # 📊 Diagramme séquence workflow
└── usage-guide.mmd          # 📊 Guide d'utilisation visuel
```

## 🔗 Connexions Clés

### Depuis n8n vers Ollama
- **URL à utiliser** : `http://ollama:11434` ⚠️ (Pas `localhost`)
- **Raison** : n8n tourne dans un conteneur Docker, il doit utiliser le nom du service

### Depuis votre machine vers n8n
- **URL** : `http://localhost:5678`

### Scripts Python dans n8n
- **Chemin à utiliser** : `/data/scripts/clean_data.py`
- **Commande** : `python3 /data/scripts/clean_data.py`

## 💡 Workflow de Développement

1. **Éditer le code Python** dans VS Code (`local_scripts/`)
2. **Sauvegarder** (`Ctrl+S`)
3. **Exécuter immédiatement** depuis n8n (pas de rebuild nécessaire)
4. **Debugger** en ajoutant des `print()` dans votre script Python (visible dans les logs n8n)

## 🛠️ Commandes Utiles

### Voir les logs en temps réel
```powershell
# Logs n8n
docker logs -f n8n_data_architect

# Logs Ollama
docker logs -f ollama_local_ai
```

### Lister les modèles installés
```powershell
docker exec -it ollama_local_ai ollama list
```

### Tester Ollama manuellement
```powershell
docker exec -it ollama_local_ai ollama run llama3
```
*(Tapez votre question, puis `Ctrl+D` pour sortir)*

### Redémarrer la stack
```powershell
docker-compose restart
```

### Arrêter tout
```powershell
docker-compose down
```

## 📦 Modèles IA Recommandés

| Modèle | Taille | RAM Nécessaire | Usage |
|--------|--------|----------------|-------|
| `llama3` | 8B | 8 GB | Standard (Recommandé) |
| `mistral` | 7B | 8 GB | Français optimisé |
| `llama3:70b` | 70B | 40 GB | Très haute performance |
| `codellama` | 13B | 16 GB | Spécialisé code |
| `deepseek-coder` | 33B | 24 GB | Code avancé |

## 🔒 Sécurité

⚠️ **Cette configuration est pour le développement local uniquement.**

Pour la production :
- Changez les mots de passe dans `.env`
- Activez HTTPS
- Configurez un reverse proxy (Traefik/Nginx)
- Ne mappez pas les volumes en lecture/écriture

## 🆘 Dépannage

### "Cannot connect to Ollama"
- Vérifiez que le conteneur tourne : `docker ps`
- Utilisez `http://ollama:11434` et non `localhost`

### "Model not found"
- Téléchargez-le : `docker exec -it ollama_local_ai ollama pull llama3`

### Script Python ne se met pas à jour
- Vérifiez que vous éditez bien `local_scripts/` (pas un autre dossier)
- Redémarrez le workflow dans n8n

### Ollama est lent
- Les gros modèles (70B+) nécessitent un GPU NVIDIA avec beaucoup de VRAM
- Utilisez des modèles plus petits (7B-13B) pour CPU/RAM standard

## 📚 Ressources

- [Documentation n8n](https://docs.n8n.io)
- [Documentation Ollama](https://ollama.ai/library)
- [Mermaid Diagrams](https://mermaid.js.org)

---

**Architecture maintenue par :** Senior Data Architect
**Date :** 2025-11-30