#!/usr/bin/env python3
"""
🎯 Analyseur de Sentiment Contextualisé par Ticker
--------------------------------------------------------------------
Analyse le sentiment spécifiquement pour le ticker mentionné,
en isolant les segments de texte qui parlent de cette compagnie.

Usage:
    from contextual_sentiment_analyzer import analyze_contextual_sentiment
"""
import sys
sys.path.insert(0, '/data/scripts')

import re
import requests
import os
from typing import Dict, List, Tuple

# Détecter l'environnement et ajuster l'URL FinBERT
# En local (Windows), utiliser localhost:8089 (port mappé)
# Dans Docker, utiliser finbert_api_gpu:8080 (nom du conteneur)
if os.path.exists('/data/scripts'):
    # Environnement Docker
    FINBERT_API_URL = os.environ.get('FINBERT_API_URL', 'http://finbert_api_gpu:8080')
else:
    # Environnement local (Windows)
    FINBERT_API_URL = os.environ.get('FINBERT_API_URL', 'http://localhost:8089')

# Health check pour valider que FinBERT est accessible
def check_finbert_health() -> bool:
    """
    Vérifie que le service FinBERT est accessible.
    Retourne True si accessible, False sinon.
    Affiche des instructions claires si le service n'est pas disponible.
    """
    try:
        response = requests.get(f"{FINBERT_API_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ FinBERT API accessible")
            return True
    except:
        pass
    
    # Si on arrive ici, FinBERT n'est pas accessible
    print("\n" + "="*80)
    print("❌ ERREUR: FinBERT API non accessible")
    print("="*80)
    print("\n🐳 Le service FinBERT nécessite Docker.\n")
    print("📋 Vérifications:")
    print("   1. Docker Desktop est-il démarré ?")
    print("   2. Le conteneur FinBERT est-il en cours d'exécution ?\n")
    print("▶️  Commandes pour démarrer FinBERT:\n")
    print("   # Version GPU (recommandé si carte NVIDIA disponible):")
    print("   docker-compose -f docker-compose.finbert.gpu.yml up -d\n")
    print("   # Version CPU (si pas de GPU):")
    print("   docker-compose -f docker-compose.finbert.yml up -d\n")
    print("🔍 Vérifier l'état:")
    print("   docker-compose ps\n")
    print("="*80 + "\n")
    return False

# Vérification au chargement du module
_FINBERT_AVAILABLE = check_finbert_health()

if not _FINBERT_AVAILABLE:
    raise RuntimeError(
        "\n🚨 ERREUR FATALE: FinBERT n'est pas accessible.\n"
        "Le script ne peut pas continuer sans Docker.\n"
        "Veuillez démarrer Docker avec la commande appropriée (voir ci-dessus).\n"
    )

# Mapping complet ticker → noms de compagnies
TICKER_NAMES = {
    "ADBE": ["Adobe", "Photoshop", "Illustrator", "Creative Cloud"],
    "AMD": ["AMD", "Advanced Micro Devices", "Ryzen", "EPYC", "Radeon"],
    "AMZN": ["Amazon", "AWS", "Amazon Web Services", "Prime", "Alexa"],
    "ANTHROPIC": ["Anthropic", "Claude"],
    "AVGO": ["Broadcom", "Avago"],
    "COHERE": ["Cohere"],
    "CRM": ["Salesforce", "Slack"],
    "GOOGL": ["Google", "Alphabet", "Gemini", "Bard", "DeepMind", "YouTube"],
    "INTC": ["Intel", "Xeon"],
    "META": ["Meta", "Facebook", "Instagram", "WhatsApp", "Threads"],
    "MISTRAL": ["Mistral", "Mistral AI"],
    "MSFT": ["Microsoft", "Azure", "Bing", "Windows", "Office"],
    "NOW": ["ServiceNow"],
    "NVDA": ["NVIDIA", "Nvidia", "GeForce", "RTX"],
    "OPENAI": ["OpenAI", "ChatGPT", "GPT"],
    "ORCL": ["Oracle"],
    "PLTR": ["Palantir"],
    "SNOW": ["Snowflake"],
    "TSLA": ["Tesla", "Elon Musk"]
}

def detect_companies_in_text(text: str) -> Dict[str, List[str]]:
    """
    Détecte toutes les compagnies mentionnées et retourne
    les phrases qui les mentionnent.
    
    Returns:
        {ticker: [phrases...]}
    """
    text_lower = text.lower()
    
    # Séparer en phrases (simple split sur . ! ?)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    company_sentences = {}
    
    for ticker, names in TICKER_NAMES.items():
        matching_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Vérifier si une des variations du nom est présente
            for name in names:
                pattern = r'\b' + re.escape(name.lower()) + r'\b'
                if re.search(pattern, sentence_lower):
                    matching_sentences.append(sentence)
                    break  # Une seule fois par phrase
        
        if matching_sentences:
            company_sentences[ticker] = matching_sentences
    
    return company_sentences

def analyze_with_finbert(text: str) -> Dict:
    """Envoie un texte au service FinBERT pour analyse"""
    try:
        response = requests.post(
            f"{FINBERT_API_URL}/analyze",
            json={"text": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Erreur FinBERT: {e}")
        return None

def analyze_contextual_sentiment(title: str, description: str, target_ticker: str) -> Dict:
    """
    Analyse le sentiment spécifiquement pour le ticker ciblé.
    
    Args:
        title: Titre de l'article
        description: Description/contenu
        target_ticker: Ticker principal (ex: "NVDA")
    
    Returns:
        {
            'global_sentiment': {...},  # Sentiment de l'article complet
            'target_sentiment': {...},  # Sentiment spécifique au ticker
            'relevance': float,         # % du texte qui parle du ticker
            'other_companies': [...]    # Autres compagnies mentionnées
        }
    """
    full_text = f"{title}. {description}".strip()
    
    if not full_text or len(full_text) < 20:
        return None
    
    # 1. Analyser le sentiment global
    global_sentiment = analyze_with_finbert(full_text)
    
    if not global_sentiment:
        return None
    
    # 2. Détecter toutes les compagnies mentionnées
    company_sentences = detect_companies_in_text(full_text)
    
    # 3. Extraire les phrases qui parlent du ticker ciblé
    target_sentences = company_sentences.get(target_ticker, [])
    
    # 4. Si le ticker n'est pas mentionné, utiliser le sentiment global
    if not target_sentences:
        return {
            'global_sentiment': global_sentiment,
            'target_sentiment': global_sentiment,  # Fallback
            'relevance': 0.0,  # Ticker pas mentionné
            'target_text': None,
            'other_companies': list(company_sentences.keys()),
            'method': 'global_fallback'
        }
    
    # 5. Combiner les phrases du ticker en un texte contextualisé
    target_text = ". ".join(target_sentences)
    
    # 6. Analyser le sentiment du texte contextualisé
    target_sentiment = analyze_with_finbert(target_text)
    
    if not target_sentiment:
        # Fallback si l'analyse échoue
        target_sentiment = global_sentiment
    
    # 7. Calculer la pertinence (% du texte consacré au ticker)
    relevance = len(target_text) / len(full_text) if full_text else 0.0
    
    # 8. Identifier les autres compagnies mentionnées
    other_companies = [t for t in company_sentences.keys() if t != target_ticker]
    
    return {
        'global_sentiment': global_sentiment,
        'target_sentiment': target_sentiment,
        'relevance': relevance,
        'target_text': target_text if len(target_text) < 500 else target_text[:500] + "...",
        'other_companies': other_companies,
        'method': 'contextual'
    }

def format_sentiment_for_storage(contextual_result: Dict) -> Dict:
    """
    Formate le résultat pour le stockage dans le JSON.
    
    Returns le format compatible avec l'ancien système + nouvelles infos.
    """
    if not contextual_result:
        return None
    
    target_sent = contextual_result['target_sentiment']
    global_sent = contextual_result['global_sentiment']
    
    return {
        # Scores principaux (ceux du ticker ciblé)
        'positive': target_sent.get('positive', 0.0),
        'negative': target_sent.get('negative', 0.0),
        'neutral': target_sent.get('neutral', 0.0),
        'compound': target_sent.get('compound', 0.0),
        
        # Métadonnées
        'model': 'finbert',
        'method': contextual_result['method'],
        'relevance': contextual_result['relevance'],
        
        # Sentiment global pour comparaison
        'global_compound': global_sent.get('compound', 0.0),
        
        # Autres compagnies mentionnées
        'other_companies': contextual_result['other_companies'],
        
        # Texte analysé (optionnel, pour debug)
        # 'analyzed_text': contextual_result.get('target_text', '')[:200]
    }

# Test rapide si exécuté directement
if __name__ == '__main__':
    # Exemple 1: Article sur NVDA uniquement
    result1 = analyze_contextual_sentiment(
        title="NVIDIA announces record earnings",
        description="NVIDIA reported strong Q4 earnings with GPU sales up 50%.",
        target_ticker="NVDA"
    )
    print("Test 1 - NVDA seul:")
    print(f"  Target compound: {result1['target_sentiment']['compound']:+.3f}")
    print(f"  Relevance: {result1['relevance']:.1%}")
    print(f"  Other companies: {result1['other_companies']}")
    print()
    
    # Exemple 2: Article multi-compagnies
    result2 = analyze_contextual_sentiment(
        title="AMD and Intel struggle while NVIDIA dominates",
        description="NVIDIA continues to lead the GPU market. AMD faces challenges in AI chips. Intel's new processors disappoint investors.",
        target_ticker="NVDA"
    )
    print("Test 2 - Article multi-compagnies:")
    print(f"  Global compound: {result2['global_sentiment']['compound']:+.3f}")
    print(f"  Target compound (NVDA): {result2['target_sentiment']['compound']:+.3f}")
    print(f"  Relevance: {result2['relevance']:.1%}")
    print(f"  Other companies: {result2['other_companies']}")
    print(f"  Target text: {result2['target_text']}")
