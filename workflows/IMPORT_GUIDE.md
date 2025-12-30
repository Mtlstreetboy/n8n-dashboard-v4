# 🚀 Guide d'Import des Workflows n8n

## 📦 Workflows Créés

Deux workflows ont été générés pour votre système d'analyse de sentiment :

### 1. **Workflow 1 : Collection Quotidienne** (`workflow-1-daily-collection.json`)
- **Déclencheur** : Schedule (8h00 chaque jour)
- **Fonction** : Collecte 30 articles IA, analyse sentiment via Ollama, stocke en CSV et JSON
- **Durée estimée** : 5-10 minutes (selon vitesse Ollama)

### 2. **Workflow 2 : Agrégation & Alertes** (`workflow-2-aggregation-alerts.json`)
- **Déclencheur** : Schedule (20h00 chaque jour)
- **Fonction** : Agrège données historiques, calcule moyennes mobiles, détecte bulles, envoie alertes
- **Durée estimée** : < 1 minute

---

## 📥 Instructions d'Import dans n8n

### Étape 1 : Accéder à n8n
```
http://localhost:5678
Login: admin
Password: supersecurepassword
```

### Étape 2 : Importer Workflow 1 (Collection)

1. Dans n8n, cliquez sur **"Workflows"** (menu gauche)
2. Cliquez sur **"Add Workflow"** → **"Import from File"**
3. Sélectionnez `workflows/workflow-1-daily-collection.json`
4. Le workflow s'ouvre automatiquement dans l'éditeur

### Étape 3 : Configurer les Credentials (API Keys)

#### NewsAPI Configuration
1. Dans le workflow, cliquez sur le nœud **"NewsAPI Request"**
2. Sous "Credentials", cliquez sur **"Create New"**
3. Sélectionnez **"HTTP Query Auth"**
4. Nom du paramètre : `apiKey`
5. Valeur : Votre clé API NewsAPI (obtenez-la sur https://newsapi.org)
6. Cliquez **"Save"**

**Note :** Si vous n'avez pas de clé NewsAPI, vous pouvez :
- Désactiver ce nœud temporairement
- Utiliser uniquement Google News RSS (gratuit)
- Créer un compte gratuit sur NewsAPI (100 requêtes/jour)

### Étape 4 : Tester le Workflow 1

1. Cliquez sur **"Execute Workflow"** (bouton en bas à droite)
2. Observez chaque nœud s'exécuter (ils deviennent verts)
3. **ATTENTION** : L'exécution prendra plusieurs minutes car Ollama analyse chaque article
4. Vérifiez que le fichier `local_files/sentiment/YYYY-MM-DD_articles.csv` a été créé

### Étape 5 : Activer le Schedule

1. Cliquez sur le nœud **"Schedule Trigger - 8h00"**
2. Ajustez l'heure si nécessaire (par défaut : toutes les 24h à 8h00)
3. Cliquez sur **"Save"** en haut à droite
4. Activez le workflow avec le bouton **"Active"** (switch en haut à droite)

### Étape 6 : Importer Workflow 2 (Agrégation)

1. Répétez les étapes 2-3 pour `workflow-2-aggregation-alerts.json`
2. **Configurer l'email** :
   - Cliquez sur le nœud **"Send Alert Email"**
   - Créez des credentials SMTP (Gmail, Outlook, ou SMTP custom)
   - Modifiez `toEmail` avec votre adresse
3. Sauvegardez et activez le workflow

---

## ⚙️ Configuration Avancée

### Modifier la Fréquence de Collection

Par défaut, le système collecte 30 articles/jour. Pour augmenter :

1. **Dans Workflow 1**, nœud **"NewsAPI Request"** :
   - Changez `pageSize: 30` → `pageSize: 100`
2. **Ajustez le schedule** :
   - Pour 2x/jour : Changez `hoursInterval: 24` → `hoursInterval: 12`

### Personnaliser les Mots-Clés de Recherche

Dans le nœud **"NewsAPI Request"** :
```javascript
// Modifiez cette ligne :
"q": "artificial intelligence OR machine learning OR GPT OR LLM"

// Exemples de personnalisation :
"q": "(AI OR artificial intelligence) AND (investment OR funding OR valuation)"
"q": "OpenAI OR Anthropic OR Google AI OR Meta AI"
```

### Ajuster les Seuils de Détection de Bulle

Éditez `local_scripts/aggregate_sentiment.py` (lignes 30-50) :

```python
# Signal 1: Score très élevé
if latest['daily_avg_score'] > 7:  # Changez 7 → 8 pour moins sensible

# Signal 2: Divergence
if divergence > 3:  # Changez 3 → 4 pour moins sensible
```

---

## 🐛 Dépannage

### Erreur "Command not found: python3"
Le conteneur n8n n'a pas accès à Python. Vérifiez que le volume est bien mappé :
```powershell
docker exec -it n8n_data_architect ls /data/scripts
# Vous devez voir : sentiment_analyzer.py
```

### Erreur "Cannot connect to Ollama"
Ollama n'est pas démarré ou le modèle n'est pas téléchargé :
```powershell
docker ps  # Vérifiez que ollama_local_ai tourne
docker exec -it ollama_local_ai ollama list  # Vérifiez que llama3 est installé
```

### Workflow trop lent
Ollama analyse prend 3-5 secondes/article. Pour 30 articles = 2-3 minutes.

**Solutions :**
- Réduire le nombre d'articles à 10-15
- Utiliser un modèle plus petit : `ollama pull mistral` (7B vs 8B)
- Activer le GPU si disponible (déjà configuré dans docker-compose.yml)

### Articles dupliqués
Le nœud "Normalize & Deduplicate" filtre par URL. Si vous voyez des doublons :
- Vérifiez que différentes sources ne renvoient pas des URLs légèrement différentes
- Ajoutez un filtre sur les titres similaires (Levenshtein distance)

### Email non envoyé
Configurez correctement les credentials SMTP :
- **Gmail** : Activez "Autoriser les applications moins sécurisées" ou créez un "Mot de passe d'application"
- **Outlook** : Utilisez le SMTP `smtp-mail.outlook.com:587`

---

## 📊 Visualisation des Résultats

Les données sont stockées dans :
```
local_files/
├── sentiment/
│   └── YYYY-MM-DD_articles.csv      # Articles du jour avec scores
├── sentiment_historical.json         # Historique complet (100 jours)
├── reports/
│   └── daily_report_YYYY-MM-DD.json # Rapport quotidien avec stats
└── charts/
    └── chart_data_YYYY-MM-DD.json   # Données prêtes pour graphiques
```

### Créer un Dashboard Excel

1. Ouvrez `sentiment_historical.json` dans Excel (Power Query)
2. Créez un graphique avec :
   - Axe X : Date
   - Axe Y : `sentiment_score`
   - Ligne de tendance : Moyenne mobile 7 jours

### Script Python pour Graphique (À venir)

Voulez-vous que je crée un script Python avec `matplotlib` pour générer automatiquement un graphique PNG quotidien ?

---

## 🎯 Prochaines Étapes

Après avoir importé et testé les workflows :

1. **Laisser tourner 7 jours** pour accumuler des données
2. **Analyser les premiers résultats** dans les CSV quotidiens
3. **Ajuster les seuils** de détection de bulle selon votre tolérance au risque
4. **Optionnel** : Créer un dashboard avec visualisation graphique

---

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs : `docker logs -f n8n_data_architect`
2. Testez manuellement les scripts Python (voir SENTIMENT_ANALYSIS_GUIDE.md)
3. Validez qu'Ollama répond : `docker exec -it ollama_local_ai ollama list`

**Système opérationnel = Collection quotidienne automatique + Alertes bulle + Historique 100 jours**
