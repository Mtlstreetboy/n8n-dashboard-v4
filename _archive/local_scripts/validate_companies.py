# -*- coding: utf-8 -*-
"""
Validation LLM: Filtrer les articles non pertinents
Utilise llama3 pour verifier que l'article parle vraiment de la compagnie ciblee
"""

import json
import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime

DATA_DIR = "/data/files"
COMPANIES_DIR = os.path.join(DATA_DIR, "companies")
OLLAMA_URL = "http://ollama:11434/api/generate"

write_lock = Lock()

def validate_article_with_llm(article, company_name, ticker, timeout=30):
    """
    Utilise LLM pour valider si l'article parle vraiment de la compagnie
    
    Returns:
        dict: {
            'relevance': 'RELEVANT' | 'MENTION' | 'NON_PERTINENT' | 'HOMONYME',
            'confidence': float (0-1),
            'reasoning': str
        }
    """
    
    prompt = f"""Analyse cet article pour determiner s'il parle vraiment de {company_name} (ticker: {ticker}).

TITRE: {article['title']}

CONTENU: {article['content'][:800]}

SOURCE: {article['source']}

INSTRUCTIONS:
Tu dois classer l'article dans UNE de ces categories:

1. RELEVANT - L'article parle principalement de {company_name}
   Exemples: annonce produit, resultats financiers, partenariat, strategy

2. MENTION - {company_name} est mentionne mais pas le sujet principal
   Exemples: liste de compagnies, comparaison de marche, contexte industriel

3. NON_PERTINENT - Ne parle pas vraiment de {company_name}
   Exemples: article general sur l'IA sans mention specifique

4. HOMONYME - Parle d'une autre entite avec un nom similaire
   Exemples: autre compagnie, produit, personne avec nom similaire

REPONDS EN JSON:
{{
  "relevance": "RELEVANT|MENTION|NON_PERTINENT|HOMONYME",
  "confidence": 0.95,
  "reasoning": "Breve explication"
}}

REPONDS UNIQUEMENT AVEC LE JSON, RIEN D'AUTRE."""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3:latest",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 150
                }
            },
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result.get('response', '').strip()
            
            # Parser la reponse JSON
            try:
                # Extraire JSON de la reponse (peut contenir du texte avant/apres)
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = llm_response[json_start:json_end]
                    validation = json.loads(json_str)
                    
                    return {
                        'relevance': validation.get('relevance', 'NON_PERTINENT'),
                        'confidence': float(validation.get('confidence', 0.5)),
                        'reasoning': validation.get('reasoning', 'No reasoning provided'),
                        'validated_at': datetime.now().isoformat()
                    }
                else:
                    # Fallback: chercher les mots-cles
                    if 'RELEVANT' in llm_response:
                        relevance = 'RELEVANT'
                    elif 'MENTION' in llm_response:
                        relevance = 'MENTION'
                    elif 'HOMONYME' in llm_response:
                        relevance = 'HOMONYME'
                    else:
                        relevance = 'NON_PERTINENT'
                    
                    return {
                        'relevance': relevance,
                        'confidence': 0.6,
                        'reasoning': llm_response[:200],
                        'validated_at': datetime.now().isoformat()
                    }
                    
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse LLM JSON: {e}")
                print(f"Response was: {llm_response[:200]}")
                return {
                    'relevance': 'NON_PERTINENT',
                    'confidence': 0.3,
                    'reasoning': f'Parse error: {str(e)}',
                    'validated_at': datetime.now().isoformat()
                }
        else:
            return {
                'relevance': 'NON_PERTINENT',
                'confidence': 0.0,
                'reasoning': f'HTTP {response.status_code}',
                'validated_at': datetime.now().isoformat()
            }
            
    except requests.Timeout:
        return {
            'relevance': 'NON_PERTINENT',
            'confidence': 0.0,
            'reasoning': 'LLM timeout',
            'validated_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'relevance': 'NON_PERTINENT',
            'confidence': 0.0,
            'reasoning': f'Error: {str(e)}',
            'validated_at': datetime.now().isoformat()
        }

def validate_article_wrapper(article, company_name, ticker):
    """Wrapper pour threading avec gestion d'erreurs"""
    try:
        validation = validate_article_with_llm(article, company_name, ticker)
        
        # Ajouter validation au article
        article['validation'] = validation
        article['validated'] = True
        
        return {
            'success': True,
            'article': article,
            'relevance': validation['relevance']
        }
    except Exception as e:
        print(f"Error validating article: {e}")
        return {
            'success': False,
            'article': article,
            'error': str(e)
        }

def validate_company_articles(ticker, max_workers=10, min_confidence=0.6):
    """
    Valide tous les articles non-valides d'une compagnie
    
    Args:
        ticker: Ticker de la compagnie
        max_workers: Nombre de threads paralleles
        min_confidence: Confiance minimale pour garder l'article
    
    Returns:
        dict: Statistiques de validation
    """
    
    filepath = os.path.join(COMPANIES_DIR, f"{ticker}_news.json")
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return None
    
    # Charger articles
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    company_name = data['company_name']
    articles = data['articles']
    
    # Filtrer articles non-valides
    to_validate = [a for a in articles if not a.get('validated', False)]
    already_validated = [a for a in articles if a.get('validated', False)]
    
    print(f"\n{'='*60}")
    print(f"Validating: {ticker} - {company_name}")
    print(f"Total articles: {len(articles)}")
    print(f"Already validated: {len(already_validated)}")
    print(f"To validate: {len(to_validate)}")
    print(f"{'='*60}")
    
    if len(to_validate) == 0:
        print("Nothing to validate!")
        return {
            'ticker': ticker,
            'total': len(articles),
            'validated': len(already_validated),
            'new_validated': 0
        }
    
    # Validation parallele
    validated_articles = []
    stats = {
        'RELEVANT': 0,
        'MENTION': 0,
        'NON_PERTINENT': 0,
        'HOMONYME': 0,
        'ERROR': 0
    }
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(validate_article_wrapper, article, company_name, ticker): article
            for article in to_validate
        }
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            
            if result['success']:
                article = result['article']
                relevance = result['relevance']
                
                validated_articles.append(article)
                stats[relevance] = stats.get(relevance, 0) + 1
                
                # Progress
                if i % 10 == 0 or i == len(to_validate):
                    print(f"  Progress: {i}/{len(to_validate)} - "
                          f"R:{stats['RELEVANT']} M:{stats['MENTION']} "
                          f"N:{stats['NON_PERTINENT']} H:{stats['HOMONYME']}")
            else:
                stats['ERROR'] += 1
    
    # Combiner avec articles deja valides
    all_validated = already_validated + validated_articles
    
    # Filtrer: garder seulement RELEVANT et MENTION avec confiance elevee
    filtered_articles = []
    for article in all_validated:
        validation = article.get('validation', {})
        relevance = validation.get('relevance', 'NON_PERTINENT')
        confidence = validation.get('confidence', 0.0)
        
        # Criteres de filtrage
        if relevance == 'RELEVANT':
            filtered_articles.append(article)
        elif relevance == 'MENTION' and confidence >= min_confidence:
            filtered_articles.append(article)
        # Rejeter: NON_PERTINENT, HOMONYME, ou MENTION avec faible confiance
    
    # Sauvegarder
    data['articles'] = filtered_articles
    data['total_articles'] = len(filtered_articles)
    data['last_validation'] = datetime.now().isoformat()
    data['validation_stats'] = stats
    
    with write_lock:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\nValidation Summary:")
    print(f"  New validated: {len(validated_articles)}")
    print(f"  RELEVANT: {stats['RELEVANT']}")
    print(f"  MENTION: {stats['MENTION']}")
    print(f"  NON_PERTINENT: {stats['NON_PERTINENT']}")
    print(f"  HOMONYME: {stats['HOMONYME']}")
    print(f"  ERROR: {stats['ERROR']}")
    print(f"  Kept after filtering: {len(filtered_articles)}/{len(all_validated)}")
    print(f"  Saved to: {filepath}")
    
    return {
        'ticker': ticker,
        'total_before': len(articles),
        'total_after': len(filtered_articles),
        'new_validated': len(validated_articles),
        'stats': stats
    }

def validate_all_companies(max_workers=10, min_confidence=0.6):
    """Valide toutes les compagnies"""
    
    print("\n" + "="*70)
    print(f"VALIDATION LLM: All Companies")
    print(f"Workers per company: {max_workers}")
    print(f"Min confidence: {min_confidence}")
    print("="*70)
    
    # Lister tous les fichiers *_news.json
    json_files = [f for f in os.listdir(COMPANIES_DIR) if f.endswith('_news.json')]
    tickers = [f.replace('_news.json', '') for f in json_files]
    
    print(f"\nFound {len(tickers)} companies to validate")
    
    start_time = time.time()
    results = []
    
    for ticker in tickers:
        result = validate_company_articles(ticker, max_workers, min_confidence)
        if result:
            results.append(result)
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "="*70)
    print(f"VALIDATION COMPLETE")
    print(f"Time elapsed: {elapsed:.1f}s")
    print("\nPer Company:")
    for r in results:
        kept_pct = (r['total_after'] / r['total_before'] * 100) if r['total_before'] > 0 else 0
        print(f"  {r['ticker']:8} - Before: {r['total_before']:4d} -> After: {r['total_after']:4d} ({kept_pct:.1f}% kept)")
    
    total_before = sum(r['total_before'] for r in results)
    total_after = sum(r['total_after'] for r in results)
    print(f"\nGLOBAL: {total_before} -> {total_after} articles ({total_after/total_before*100:.1f}% kept)")
    print("="*70)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Valider une seule compagnie
        ticker = sys.argv[1].upper()
        max_workers = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        min_confidence = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
        
        validate_company_articles(ticker, max_workers, min_confidence)
    else:
        # Valider toutes les compagnies
        max_workers = 10
        min_confidence = 0.6
        validate_all_companies(max_workers, min_confidence)
