
```mermaid
flowchart TB
    subgraph "🐳 Container n8n_data_architect (Alpine Linux)"
        A[batch_loader_v2.py<br/>Collecte Articles] --> B{FINBERT_API_URL<br/>défini?}
        B -->|Non| C[Mode VADER<br/>~65% précision<br/>⚠️ Baseline]
        B -->|Oui| D[finbert_analyzer.py<br/>Mode API HTTP]
        
        D --> E[Requête HTTP POST]
        E --> F{/analyze ou<br/>/analyze_batch}
        
        G[advanced_sentiment_engine_v3.py<br/>Analyse Multi-dim] --> D
        
        style A fill:#e1f5ff
        style D fill:#fff4e6
        style C fill:#ffe0e0
    end
    
    subgraph "🐳 Container finbert_api_gpu (NVIDIA CUDA)"
        F --> H[FastAPI Service<br/>Port 8080]
        H --> I[FinBERTAnalyzer Local<br/>ProsusAI/finbert]
        I --> J[PyTorch CUDA 11.8<br/>GPU: RTX 2070 Ti]
        J --> K[Transformers Pipeline<br/>Batch Size: 32]
        K --> L{Type?}
        L -->|Single| M[/analyze endpoint<br/>1 texte]
        L -->|Batch| N[/analyze_batch endpoint<br/>N textes en parallèle]
        
        M --> O[Scores FinBERT<br/>positive/negative/neutral/compound]
        N --> O
        
        style H fill:#d4edda
        style J fill:#fff3cd
        style K fill:#cce5ff
        style O fill:#d1ecf1
    end
    
    subgraph "🐳 Container finbert_api (CPU)"
        P[FastAPI Service<br/>Port 8080]
        P --> Q[FinBERTAnalyzer Local<br/>ProsusAI/finbert]
        Q --> R[PyTorch CPU Only<br/>Batch Size: 16]
        R --> S[Scores FinBERT<br/>~88% précision]
        
        style P fill:#d4edda
        style R fill:#f8d7da
    end
    
    subgraph "💾 Stockage"
        T[/data/files/companies/<br/>TICKER_news.json]
        U[articles: [...]]
        V[fetched_dates: [...]]
        W[sentiment:<br/>positive/negative/neutral/compound<br/>model: 'finbert']
        
        U --> W
        T --> U
        T --> V
        
        style T fill:#e7f3ff
        style W fill:#d1f2eb
    end
    
    A --> T
    O --> T
    S --> T
    
    subgraph "🌐 Accès Externe"
        X[Host Windows<br/>localhost:8088] -.->|CPU API| P
        Y[Host Windows<br/>localhost:8089] -.->|GPU API| H
        
        style X fill:#f0f0f0
        style Y fill:#f0f0f0
    end
    
    subgraph "📊 Modes d'Exécution"
        Z1[Mode 1: VADER Only<br/>Sans FINBERT_API_URL<br/>⚡ Rapide mais ~65%]
        Z2[Mode 2: FinBERT CPU<br/>FINBERT_API_URL=finbert_api:8080<br/>🖥️ ~88% précision]
        Z3[Mode 3: FinBERT GPU<br/>FINBERT_API_URL=finbert_api_gpu:8080<br/>🚀 ~88% + 10-20x plus rapide]
        
        style Z1 fill:#ffe0e0
        style Z2 fill:#fff4e6
        style Z3 fill:#d4edda
    end
    
    classDef container fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef api fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef storage fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    
    class A,D,G container
    class H,P api
    class T storage
```

## 🔄 Flux de Données

### 1. Collecte avec Sentiment (batch_loader_v2.py)
```
Article Google News
    ↓
Extraction métadonnées
    ↓
Analyse sentiment (FinBERT GPU/CPU ou VADER)
    ↓
Sauvegarde JSON avec scores
```

### 2. Modes d'Analyse

#### **Mode API (Recommandé)**
- Container Alpine → HTTP POST → Container FinBERT
- Évite incompatibilité musl/glibc
- Scalable et découplé

#### **Mode Local (Impossible sur Alpine)**
- PyTorch ne fonctionne pas sur Alpine Linux (musl libc)
- Uniquement possible sur Debian/Ubuntu (glibc)

### 3. Format de Sortie

```json
{
  "ticker": "NVDA",
  "articles": [
    {
      "title": "NVIDIA announces new AI chip",
      "published_at": "2025-12-23T10:00:00Z",
      "sentiment": {
        "positive": 0.9312,
        "negative": 0.0262,
        "neutral": 0.0425,
        "compound": 0.9050,
        "model": "finbert"
      }
    }
  ],
  "fetched_dates": ["2025-12-23", "2025-12-22", ...]
}
```

## 📈 Performance

| Mode | Précision | Vitesse (100 articles) | GPU Requis |
|------|-----------|------------------------|------------|
| **VADER** | ~65% | 2s | Non |
| **FinBERT CPU** | ~88% | 60s | Non |
| **FinBERT GPU** | ~88% | 3-5s | Oui (RTX 2070 Ti) |

## 🔧 Configuration

### Activer FinBERT GPU
```bash
docker exec -e FINBERT_API_URL=http://finbert_api_gpu:8080 \
  n8n_data_architect python3 /data/scripts/batch_loader_v2.py GOOGL
```

### Activer FinBERT CPU
```bash
docker exec -e FINBERT_API_URL=http://finbert_api_cpu:8080 \
  n8n_data_architect python3 /data/scripts/batch_loader_v2.py GOOGL
```

### Mode VADER (Baseline)
```bash
docker exec n8n_data_architect \
  python3 /data/scripts/batch_loader_v2.py GOOGL
```

## 🎯 État Actuel

✅ **Infrastructure déployée**
✅ **6,326 articles collectés** 
⚠️ **Sentiment historique = VADER** (collecté avant FinBERT)
🔄 **Prochaine étape**: Ré-analyser tous les articles avec FinBERT GPU
