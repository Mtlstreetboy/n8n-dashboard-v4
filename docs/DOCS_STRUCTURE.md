# 📁 Documentation Structure - n8n Dashboard v4

Dernière mise à jour: 2026-01-02

## 🗂️ Organisation des dossiers

```
docs/
├── README_DOCUMENTATION.md          ← Index principal ⭐
├── WELCOME.md                        ← Onboarding
│
├── 🚀 Quick Start/
│   ├── QUICK_START_TOMORROW.md      ← Démarrage rapide (5 min)
│   ├── QUICK_REFERENCE.md           ← Commandes clés
│   └── SMART_MONEY_QUICKSTART.md    ← Guide Smart Money
│
├── 📊 Status & Planning/
│   ├── STATUS_FINAL.md              ← État actuel (70% complete)
│   ├── CHECKLIST_TOMORROW.md        ← Tasks quotidiennes
│   └── SMART_MONEY_PROPOSAL.md      ← Proposition initiale
│
├── 🔧 Technical Guides/
│   ├── GUIDE_EXECUTION.md           ← Guide d'exécution
│   ├── IMPLEMENTATION_GUIDE.md      ← Implémentation
│   ├── PROJECT_STRUCTURE.md         ← Structure du projet
│   └── RUN_OPTIONS_LOCALLY.md       ← Lancer options localement
│
├── 🎯 QuiverQuant (Political Trading)/
│   └── QQ/                           ← Dossier dédié QuiverQuant ⭐
│       ├── README.md                 ← Index QQ complet
│       ├── POLITICAL_TRADING_PIPELINE.md
│       ├── QUIVERQUANT_API_REFERENCE.md
│       ├── INTEGRATION_POLITICAL_TRADES.md
│       ├── POLITICAL_TRADES_PLAN.md
│       └── political_trades_flow.md  ← Diagrammes Mermaid
│
├── 🏗️ Architecture/
│   ├── finbert-architecture.md       ← Architecture FinBERT
│   └── diagrams/                     ← Autres diagrammes
│
└── 📚 Guides détaillés/
    └── guides/
        ├── GUIDE_UTILISATION.md
        ├── INTEGRATION_OPTIONS_SENTIMENT.md
        ├── n8n-setup-and-workflows.md
        ├── PROD_README.md
        └── README_OPTIONS_DASHBOARD.md
```

## 📖 Guide de lecture selon profil

### 👨‍💻 Développeur - Première fois

1. **[WELCOME.md](WELCOME.md)** (5 min) - Vue d'ensemble
2. **[QUICK_START_TOMORROW.md](QUICK_START_TOMORROW.md)** (5 min) - Démarrage rapide
3. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** (10 min) - Architecture
4. **[GUIDE_EXECUTION.md](GUIDE_EXECUTION.md)** (15 min) - Exécution

**Temps total:** ~35 minutes

### 📊 Analyste Data - QuiverQuant Focus

1. **[QQ/README.md](QQ/README.md)** (10 min) - Index QuiverQuant
2. **[QQ/POLITICAL_TRADING_PIPELINE.md](QQ/POLITICAL_TRADING_PIPELINE.md)** (20 min) - Pipeline complet
3. **[QQ/political_trades_flow.md](QQ/political_trades_flow.md)** (10 min) - Diagrammes
4. Lancer `python quick_start_political.py`

**Temps total:** ~40 minutes

### 🎯 Product Manager - Status & Roadmap

1. **[STATUS_FINAL.md](STATUS_FINAL.md)** (10 min) - État actuel
2. **[SMART_MONEY_PROPOSAL.md](SMART_MONEY_PROPOSAL.md)** (15 min) - Vision
3. **[CHECKLIST_TOMORROW.md](CHECKLIST_TOMORROW.md)** (5 min) - Next steps

**Temps total:** ~30 minutes

### 🔧 DevOps - Déploiement

1. **[RUN_OPTIONS_LOCALLY.md](RUN_OPTIONS_LOCALLY.md)** (10 min)
2. **[guides/PROD_README.md](guides/PROD_README.md)** (15 min)
3. **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** (20 min)

**Temps total:** ~45 minutes

## 🎯 Documents par cas d'usage

### Je veux comprendre le système complet
→ **[README_DOCUMENTATION.md](README_DOCUMENTATION.md)** (Index principal)

### Je veux lancer le dashboard options
→ **[RUN_OPTIONS_LOCALLY.md](RUN_OPTIONS_LOCALLY.md)**

### Je veux implémenter political trading
→ **[QQ/POLITICAL_TRADING_PIPELINE.md](QQ/POLITICAL_TRADING_PIPELINE.md)**

### Je veux voir l'état du projet
→ **[STATUS_FINAL.md](STATUS_FINAL.md)**

### Je veux les diagrammes d'architecture
→ **[QQ/political_trades_flow.md](QQ/political_trades_flow.md)**  
→ **[finbert-architecture.md](finbert-architecture.md)**

### Je veux démarrer rapidement
→ **[QUICK_START_TOMORROW.md](QUICK_START_TOMORROW.md)**

### Je veux la référence API QuiverQuant
→ **[QQ/QUIVERQUANT_API_REFERENCE.md](QQ/QUIVERQUANT_API_REFERENCE.md)**

## 🆕 Nouveautés (2026-01-02)

### ✅ Réorganisation docs/QQ

Tous les fichiers relatifs à QuiverQuant ont été déplacés dans `docs/QQ/`:
- Documentation centralisée
- Navigation simplifiée
- Séparation claire QuiverQuant vs reste du système

### ✅ Fichiers déplacés

- `QUIVERQUANT_API_REFERENCE.md` → `QQ/`
- `POLITICAL_TRADING_PIPELINE.md` → `QQ/`
- `POLITICAL_TRADES_PLAN.md` → `QQ/`
- `INTEGRATION_POLITICAL_TRADES.md` → `QQ/`
- `diagrams/political_trades_flow.md` → `QQ/`

### ✅ Nouveau README QQ

Un fichier `QQ/README.md` complet a été créé avec:
- Index de tous les fichiers QQ
- Quick start guide
- Cas d'usage
- Troubleshooting
- Configuration

## 📊 Statistiques Documentation

```
Total fichiers markdown: ~25
Dossier QQ: 6 fichiers
Guides détaillés: 5 fichiers
Quick starts: 3 fichiers
Status/Planning: 3 fichiers
Architecture: 2 fichiers
```

## 🔗 Liens externes importants

- **QuiverQuant API:** https://api.quiverquant.com/docs
- **n8n Documentation:** https://docs.n8n.io/
- **FinBERT Model:** https://huggingface.co/ProsusAI/finbert
- **Streamlit Docs:** https://docs.streamlit.io/

## 🛠️ Maintenance de la documentation

### Règles d'organisation

1. **Tout ce qui concerne QuiverQuant** → `docs/QQ/`
2. **Guides généraux** → `docs/guides/`
3. **Diagrammes généraux** → `docs/diagrams/`
4. **Quick starts** → Racine de `docs/`
5. **Status/Planning** → Racine de `docs/`

### Quand ajouter un nouveau fichier

- **QuiverQuant/Political?** → `docs/QQ/`
- **Guide technique?** → `docs/guides/`
- **Diagramme?** → Vérifier si QQ → `docs/QQ/`, sinon → `docs/diagrams/`
- **Quick reference?** → Racine `docs/`

### Mise à jour de cet index

Ce fichier (`DOCS_STRUCTURE.md`) doit être mis à jour chaque fois que:
- Un nouveau dossier est créé
- Des fichiers sont déplacés
- Une réorganisation majeure est effectuée

## 💡 Tips pour naviguer

1. **Commencer par:** `README_DOCUMENTATION.md`
2. **Chercher QuiverQuant?** → Aller dans `QQ/`
3. **Besoin d'un guide?** → Chercher dans `guides/`
4. **Quick start?** → Fichiers commençant par `QUICK_`
5. **Architecture?** → Fichiers finissant par `-architecture.md`

## 🔍 Recherche rapide

### Par mot-clé

- **Political/Trading** → `docs/QQ/`
- **Options** → `RUN_OPTIONS_LOCALLY.md`, `guides/README_OPTIONS_DASHBOARD.md`
- **Sentiment** → `finbert-architecture.md`, `guides/INTEGRATION_OPTIONS_SENTIMENT.md`
- **Automation** → `GUIDE_EXECUTION.md`, `guides/PROD_README.md`
- **n8n** → `guides/n8n-setup-and-workflows.md`

### Par niveau d'urgence

- **🔴 Urgent/Blocker** → `STATUS_FINAL.md`, `CHECKLIST_TOMORROW.md`
- **🟡 Important** → `QQ/POLITICAL_TRADING_PIPELINE.md`, `IMPLEMENTATION_GUIDE.md`
- **🟢 Référence** → `QQ/QUIVERQUANT_API_REFERENCE.md`, `QUICK_REFERENCE.md`

---

**Dernière révision:** 2026-01-02  
**Responsable:** Équipe n8n Dashboard v4  
**Version:** 2.0 (Réorganisation QQ)
