# n8n - Setup et Workflows pour AI Sentiment Pipeline

Ce guide explique comment importer et configurer les workflows n8n fournis, comment utiliser n8n pour orchestrer la collecte, l'analyse et l'agrégation.

## Prérequis
- Docker + Docker Compose
- Accès au dépôt `n8n-local-stack`
- Variables d'environnement `N8N_USER` et `N8N_PASSWORD` dans `.env`

## Démarrer la stack
1. `docker compose up -d`
2. Accéder à `http://localhost:5678` (n8n)

## Importer les workflows pré-générés
- Fichiers: `workflows/workflow-1-daily-collection.json`, `workflows/workflow-2-aggregation-alerts.json`
- Dans n8n: Workflows → Add → Import from File

## Workflows recommandés
1. **Daily Pipeline**
   - Déclencheur: Schedule (6:00)
   - Étapes:
     - Execute Command: `python3 /data/scripts/batch_loader_v2.py` (par batch)
     - Execute Command: `python3 /data/scripts/collect_options.py {TICKER}`
     - Execute Command: `python3 /data/scripts/advanced_sentiment_engine_v3.py {TICKER}`
     - Merge results & call `python3 /data/scripts/analyze_all_sentiment.py`
   - Notifications: Slack/Email à la fin

2. **Error Handler**
   - Trigger: Error Trigger
   - Actions: Envoi d'un message Slack + enregistrement du log dans `/data/logs`

3. **Ad-hoc Ticker Runner**
   - Trigger: Webhook
   - Permet d'exécuter pipeline pour un ticker donné (reprise manuelle)

## Remarques
- Les commandes `Execute Command` s'exécutent dans le conteneur `n8n` avec les mêmes mounts: `/data/scripts` et `/data/files`.
- Ajuster les timeouts des nœuds `Execute Command` pour tenir compte des appels LLM (Ollama).
- Configurer des credentials pour les API (NewsAPI) dans n8n.

---

Si tu veux, je peux générer automatiquement le JSON d'un workflow n8n prêt à importer (Daily Pipeline). Veux-tu que je le crée maintenant ?