# 🔑 Configuration NewsAPI - Guide Rapide

## Étape 1: Obtenir une clé gratuite

1. Allez sur: https://newsapi.org/register
2. Inscrivez-vous (gratuit)
3. Copiez votre clé API

## Étape 2: Configurer la clé dans Docker

### Option A: Variable d'environnement (Recommandé)

```powershell
# Définir la clé (remplacez YOUR_KEY par votre vraie clé)
docker exec n8n_data_architect sh -c "export NEWSAPI_KEY='YOUR_KEY_HERE'"
```

### Option B: Modifier directement le script

```powershell
# Ouvrir le script
notepad local_scripts\collect_parallel.py

# Modifier la ligne 28:
NEWSAPI_KEY = os.environ.get('NEWSAPI_KEY', 'VOTRE_VRAIE_CLE_ICI')
```

## Étape 3: Déployer et lancer

```powershell
# Copier le script dans Docker
Get-Content local_scripts\collect_parallel.py | docker exec -i n8n_data_architect sh -c "cat > /data/scripts/collect_parallel.py"

# Lancer la collecte hybride
docker exec -it n8n_data_architect python3 /data/scripts/collect_parallel.py
```

## 📊 Limites du plan gratuit

- ✅ 100 requêtes par jour
- ✅ 30 jours d'historique
- ✅ 100 articles par requête
- ✅ Toutes les sources

## 🚀 Fonctionnement du script hybride

1. **NewsAPI** collecte les 30 derniers jours (historique fiable)
2. **GNews** collecte les nouvelles des dernières 24h (temps réel)
3. Fusion automatique + dédoublonnage par URL
4. Sauvegarde dans: `/data/files/collected_articles_100days.json`
