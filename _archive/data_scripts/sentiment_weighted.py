"""
Détecteur de bulle spéculative hybride
Architecture: Vectorisation (primary) + LLM (explanation)
"""
import re
import json
import requests
import numpy as np
from numpy.linalg import norm
from datetime import datetime
from typing import Dict, Optional, List

# ============================================================================
# CONFIGURATION
# ============================================================================

OLLAMA_BASE_URL = "http://ollama:11434"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3:latest"

# Seuil pour déclencher l'analyse LLM (économie de ressources)
LLM_TRIGGER_THRESHOLD = 0.25

# Textes de référence pour la triangulation sémantique
ANCHOR_HYPE = """
Revolutionary paradigm shift AI creates unlimited possibilities. 
Exponential growth, new era of humanity, superintelligence imminent. 
FOMO, trillions of dollars in value, ignore the skeptics, emotional connection.
Game-changing disruption, infinite potential, transform everything forever.
"""

ANCHOR_REALITY = """
Quarterly earnings report shows operational costs increasing due to GPU energy consumption.
ROI is currently negative. Integration challenges persist in legacy systems.
Margins are tightening, specific revenue metrics, tangible implementation details.
Infrastructure costs, deployment complexity, measured performance gains, incremental improvements.
"""

# Cache global pour les vecteurs d'ancrage (calculés une seule fois)
_ANCHOR_CACHE = {}
_ANCHOR_LOCK = None  # Sera initialisé au premier appel

def _get_lock():
    """Get or create thread lock for anchor cache"""
    global _ANCHOR_LOCK
    if _ANCHOR_LOCK is None:
        from threading import Lock
        _ANCHOR_LOCK = Lock()
    return _ANCHOR_LOCK


# ============================================================================
# VECTORISATION (CORE ENGINE)
# ============================================================================

def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> Optional[np.ndarray]:
    """
    Récupère le vecteur d'embeddings via Ollama
    Returns: numpy array ou None en cas d'erreur
    """
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=30
        )
        
        if response.status_code == 200:
            embedding = response.json().get("embedding")
            if embedding:
                return np.array(embedding, dtype=np.float32)
        else:
            print(f"Embedding API error: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("Embedding timeout - model may need to be pulled first")
    except Exception as e:
        print(f"Embedding error: {e}")
    
    return None


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Calcule la similarité cosinus entre deux vecteurs
    Returns: float entre -1 (opposé) et 1 (identique)
    """
    if vec_a is None or vec_b is None:
        return 0.0
    
    # Formule: (A · B) / (||A|| * ||B||)
    dot_product = np.dot(vec_a, vec_b)
    norm_product = norm(vec_a) * norm(vec_b)
    
    if norm_product == 0:
        return 0.0
    
    return float(dot_product / norm_product)


def get_anchor_vectors() -> Dict[str, np.ndarray]:
    """
    Récupère ou calcule les vecteurs d'ancrage (cached)
    Thread-safe pour utilisation parallèle
    """
    global _ANCHOR_CACHE
    
    if _ANCHOR_CACHE:
        return _ANCHOR_CACHE
    
    lock = _get_lock()
    with lock:
        # Double-check après acquisition du lock
        if _ANCHOR_CACHE:
            return _ANCHOR_CACHE
            
        print("🔧 Initializing anchor vectors (first run)...")
        _ANCHOR_CACHE = {
            "hype": get_embedding(ANCHOR_HYPE),
            "reality": get_embedding(ANCHOR_REALITY)
        }
        
        if _ANCHOR_CACHE["hype"] is None or _ANCHOR_CACHE["reality"] is None:
            print("⚠️  WARNING: Failed to initialize anchors - embeddings unavailable")
            _ANCHOR_CACHE = {}
            return {}
    
    return _ANCHOR_CACHE


def analyze_vectors(article_text: str) -> Dict:
    """
    Analyse vectorielle de l'article
    Returns: Dict avec scores de similarité et index de bulle
    """
    # Récupérer les vecteurs d'ancrage
    anchors = get_anchor_vectors()
    
    if not anchors:
        return {
            "status": "error",
            "error": "Anchor vectors not initialized",
            "vector_bubble_index": 0.0
        }
    
    # Vectoriser l'article
    vec_article = get_embedding(article_text[:4000])  # Limite tokens
    
    if vec_article is None:
        return {
            "status": "error",
            "error": "Failed to embed article",
            "vector_bubble_index": 0.0
        }
    
    # Calculer les similarités
    sim_hype = cosine_similarity(vec_article, anchors["hype"])
    sim_reality = cosine_similarity(vec_article, anchors["reality"])
    
    # Index de bulle: positif = hype, négatif = réalité
    bubble_index = sim_hype - sim_reality
    
    # Normaliser entre -1 et 1 (plus lisible)
    bubble_index = max(-1.0, min(1.0, bubble_index))
    
    return {
        "status": "success",
        "similarity_to_hype": round(sim_hype, 3),
        "similarity_to_reality": round(sim_reality, 3),
        "vector_bubble_index": round(bubble_index, 3),
        "confidence": round(abs(bubble_index), 3)  # 0-1, force du signal
    }


# ============================================================================
# LLM ANALYSIS (EXPLANATION LAYER)
# ============================================================================

def analyze_with_llm(
    article_text: str, 
    article_title: str,
    bubble_index: float
) -> Dict:
    """
    Utilise le LLM pour expliquer POURQUOI le score vectoriel est ce qu'il est
    Appelé uniquement si le signal vectoriel est significatif
    """
    
    # Contexte basé sur le score vectoriel
    if bubble_index > 0.3:
        context = "The vector analysis indicates STRONG HYPE signals."
    elif bubble_index < -0.3:
        context = "The vector analysis indicates STRONG REALITY/TECHNICAL focus."
    else:
        context = "The vector analysis indicates MIXED signals."
    
    prompt = f"""You are analyzing an article that has already been scored by mathematical vector analysis.

VECTOR ANALYSIS RESULT: {context}
Bubble Index: {bubble_index:.2f} (range: -1 to +1, where +1 = pure hype, -1 = pure reality)

Your job is to EXPLAIN this score by identifying specific phrases and themes.

ARTICLE:
Title: {article_title}
Content: {article_text[:2500]}

Identify:
1. Key phrases that contribute to hype (if bubble_index > 0)
2. Key phrases that show concrete reality (if bubble_index < 0)
3. Main themes present

Output ONLY valid JSON:
{{
  "flagged_hype_phrases": ["phrase1", "phrase2"],
  "flagged_reality_phrases": ["phrase1", "phrase2"],
  "key_themes": ["theme1", "theme2"],
  "explanation": "Brief explanation of why this article scores {bubble_index:.2f}"
}}

JSON only:"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "num_predict": 350
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            raw_text = result.get("response", "")
            
            # Extraire le JSON
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw_text, re.DOTALL)
            
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    return {
                        "status": "success",
                        "flagged_hype_phrases": parsed.get("flagged_hype_phrases", [])[:5],
                        "flagged_reality_phrases": parsed.get("flagged_reality_phrases", [])[:5],
                        "key_themes": parsed.get("key_themes", [])[:5],
                        "explanation": parsed.get("explanation", "")[:500]
                    }
                except json.JSONDecodeError:
                    pass
        
        # Fallback
        return {
            "status": "parsing_error",
            "flagged_hype_phrases": [],
            "flagged_reality_phrases": [],
            "key_themes": [],
            "explanation": "LLM response could not be parsed"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "flagged_hype_phrases": [],
            "flagged_reality_phrases": [],
            "key_themes": [],
            "explanation": f"LLM error: {str(e)}"
        }


# ============================================================================
# HYBRID ANALYZER (ORCHESTRATION)
# ============================================================================

def analyze_article_hybrid(
    article_text: str,
    article_title: str = "",
    force_llm: bool = False
) -> Dict:
    """
    Analyseur hybride principal
    
    Architecture:
    1. Vectorisation (TOUJOURS) → score primaire fiable
    2. LLM (CONDITIONNEL) → explication si signal significatif
    
    Args:
        article_text: Contenu de l'article
        article_title: Titre (optionnel)
        force_llm: Force l'appel LLM même si signal faible
    
    Returns:
        Dict avec tous les scores et métadonnées
    """
    
    timestamp = datetime.now().isoformat()
    
    # PHASE 1: Analyse vectorielle (rapide, fiable)
    vector_result = analyze_vectors(article_text)
    
    if vector_result.get("status") == "error":
        return {
            "status": "error",
            "error": vector_result.get("error"),
            "score": 0,
            "weighted_keywords": "",
            "financial_impact": "error",
            "justification": "Vector analysis failed",
            "category": "error",
            "method": "none",
            "analyzed_at": timestamp
        }
    
    bubble_index = vector_result["vector_bubble_index"]
    confidence = vector_result["confidence"]
    
    # PHASE 2: Décision d'appeler le LLM
    should_call_llm = force_llm or (confidence >= LLM_TRIGGER_THRESHOLD)
    
    if should_call_llm:
        llm_result = analyze_with_llm(article_text, article_title, bubble_index)
        method = "hybrid"
    else:
        # Signal trop faible, pas besoin d'explication détaillée
        llm_result = {
            "status": "skipped",
            "flagged_hype_phrases": [],
            "flagged_reality_phrases": [],
            "key_themes": [],
            "explanation": "Signal too weak to warrant detailed analysis"
        }
        method = "vector_only"
    
    # Conversion du bubble_index en score -10 à +10 (compatibilité legacy)
    legacy_score = int(bubble_index * 10)
    
    # Classification simple
    if bubble_index > 0.3:
        sentiment = "hype"
    elif bubble_index < -0.3:
        sentiment = "reality"
    else:
        sentiment = "neutral"
    
    # Construire weighted_keywords depuis key_themes
    weighted_keywords = ', '.join(llm_result.get("key_themes", [])[:3])
    
    # RÉSULTAT FINAL
    return {
        # Scores principaux
        "score": legacy_score,  # -10 à +10 pour compatibilité
        "vector_bubble_index": bubble_index,  # -1 à +1 (UTILISE CELUI-CI)
        "confidence": confidence,  # 0 à 1
        
        # Détails vectoriels
        "similarity_to_hype": vector_result["similarity_to_hype"],
        "similarity_to_reality": vector_result["similarity_to_reality"],
        
        # Explications LLM
        "flagged_hype_phrases": llm_result.get("flagged_hype_phrases", []),
        "flagged_reality_phrases": llm_result.get("flagged_reality_phrases", []),
        "key_themes": llm_result.get("key_themes", []),
        "explanation": llm_result.get("explanation", ""),
        
        # Compatibilité legacy (pour analyze_weighted.py)
        "weighted_keywords": weighted_keywords,
        "financial_impact": f"Bubble risk: {bubble_index:.2f}",
        "justification": f"Vector: {bubble_index:.2f}, Confidence: {confidence:.2f}. {llm_result.get('explanation', '')}",
        "category": sentiment,
        "sentiment": sentiment,
        "method": method,
        "llm_status": llm_result.get("status", "not_called"),
        "analyzed_at": timestamp
    }


# ============================================================================
# COMPATIBILITY WRAPPER (Pour n8n/scripts existants)
# ============================================================================

def analyze_sentiment_weighted(
    article_text: str,
    article_title: str,
    historical_context: Optional[Dict] = None
) -> Dict:
    """
    Wrapper pour compatibilité avec l'ancienne fonction
    Redirige vers l'analyseur hybride
    """
    # Le contexte historique pourrait être utilisé pour ajuster les seuils
    # mais pour l'instant on l'ignore (à implémenter si nécessaire)
    
    return analyze_article_hybrid(article_text, article_title)
