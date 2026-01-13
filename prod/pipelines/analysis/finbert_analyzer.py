#!/usr/bin/env python3
"""
🤖 FinBERT Sentiment Analyzer - Finance-Specific Transformer Model
--------------------------------------------------------------------
Remplace VADER avec précision supérieure (~88% vs ~65%) sur textes financiers.

Avantages vs VADER:
- Entraîné sur corpus financier (Reuters, Bloomberg, SEC filings)
- Comprend le contexte et les nuances
- Détecte sarcasme et sentiment implicite
- Meilleure performance sur termes techniques

Usage:
    from finbert_analyzer import FinBERTAnalyzer
    analyzer = FinBERTAnalyzer()
    scores = analyzer.polarity_scores("Stock surged after earnings beat")
    # {'pos': 0.92, 'neg': 0.02, 'neu': 0.06, 'compound': 0.90}
"""

import os
import warnings
from typing import Dict, List, Optional
import numpy as np
import requests

# Suppress warnings during import
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Lazy imports for transformers (heavy)
_model = None
_tokenizer = None
_device = None
_torch = None

def _ensure_dependencies():
    """Install transformers and torch if not present"""
    global _torch
    try:
        import torch
        _torch = torch
    except ImportError:
        print("📦 Installing PyTorch (CPU)...")
        os.system("pip install torch --index-url https://download.pytorch.org/whl/cpu -q")
        try:
            import torch
            _torch = torch
        except ImportError:
            return None, None
    
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        return AutoTokenizer, AutoModelForSequenceClassification
    except ImportError:
        print("📦 Installing transformers...")
        os.system("pip install transformers -q")
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            return AutoTokenizer, AutoModelForSequenceClassification
        except ImportError:
            return None, None


class FinBERTAnalyzer:
    """
    FinBERT pour analyse de sentiment financier.
    Singleton pattern pour éviter de recharger le modèle (~500MB).
    API compatible avec VADER (polarity_scores).
    """
    
    _instance = None
    MODEL_NAME = "ProsusAI/finbert"
    
    def __new__(cls):
        """Singleton - une seule instance du modèle en mémoire"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        global _model, _tokenizer, _device, _torch, _api_url
        
        # Check if API URL is set (microservice mode)
        _api_url = os.environ.get('FINBERT_API_URL', '').strip()
        
        if _api_url:
            print(f"🌐 FinBERT en mode API: {_api_url}")
            self._initialized = True
            return
        
        print("🤖 Chargement FinBERT local (ProsusAI/finbert)...")
        
        AutoTokenizer, AutoModelForSequenceClassification = _ensure_dependencies()
        
        if AutoTokenizer is None or AutoModelForSequenceClassification is None:
            print("   ❌ Impossible de charger les dépendances")
            print("   ⚠️ Fallback sur mode dégradé (mots-clés)")
            self._initialized = False
            return
        
        try:
            _tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            _model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)
            _model.eval()
            
            # GPU si disponible, sinon CPU
            _device = _torch.device("cuda" if _torch.cuda.is_available() else "cpu")
            _model.to(_device)
            
            self._initialized = True
            print(f"   ✅ FinBERT chargé sur {_device}")
            
            # Info mémoire
            if _device.type == 'cuda':
                mem = _torch.cuda.memory_allocated() / 1024**2
                print(f"   📊 GPU Memory: {mem:.0f} MB")
            
        except Exception as e:
            print(f"   ❌ Erreur chargement FinBERT: {e}")
            print(f"   ⚠️ Fallback sur mode dégradé (mots-clés)")
            self._initialized = False
    
    @property
    def is_available(self) -> bool:
        """Vérifie si le modèle est chargé"""
        return self._initialized and (_model is not None or bool(_api_url))
    
    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyse un texte et retourne scores de sentiment.
        
        Args:
            text: Texte à analyser (max ~512 tokens)
        
        Returns:
            {'positive': 0.x, 'negative': 0.x, 'neutral': 0.x, 'compound': -1 to +1}
        """
        if not self.is_available:
            return self._fallback_analyze(text)
        
        if not text or len(text.strip()) < 3:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0, 'compound': 0.0}
        
        # API mode
        if _api_url:
            try:
                response = requests.post(
                    f"{_api_url}/analyze",
                    json={"text": text},
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"⚠️ FinBERT API error: {e}")
                return self._fallback_analyze(text)
        
        # Local mode
        try:
            # Tokenize avec truncation (BERT max 512 tokens)
            inputs = _tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(_device)
            
            # Inference
            with _torch.no_grad():
                outputs = _model(**inputs)
                probs = _torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            probs = probs.cpu().numpy()[0]
            
            # FinBERT labels: [positive, negative, neutral]
            positive = float(probs[0])
            negative = float(probs[1])
            neutral = float(probs[2])
            
            # Compound score compatible VADER (-1 à +1)
            compound = positive - negative
            
            return {
                'positive': round(positive, 4),
                'negative': round(negative, 4),
                'neutral': round(neutral, 4),
                'compound': round(compound, 4)
            }
            
        except Exception as e:
            print(f"⚠️ FinBERT error: {e}")
            return self._fallback_analyze(text)
    
    def analyze_batch(self, texts: List[str], batch_size: int = 8) -> List[Dict[str, float]]:
        """
        Analyse batch pour performance optimale.
        ~5-10x plus rapide que boucle individuelle.
        
        Args:
            texts: Liste de textes à analyser
            batch_size: Taille des batches (8 pour CPU, 16-32 pour GPU)
        
        Returns:
            Liste de dicts avec scores pour chaque texte
        """
        if not self.is_available:
            return [self._fallback_analyze(t) for t in texts]
        
        # API mode
        if _api_url:
            try:
                response = requests.post(
                    f"{_api_url}/analyze_batch",
                    json={"texts": texts, "batch_size": batch_size},
                    timeout=60
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"⚠️ FinBERT API batch error: {e}")
                return [self._fallback_analyze(t) for t in texts]
        
        # Local mode
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Filter textes vides
            valid_indices = []
            valid_texts = []
            for j, t in enumerate(batch):
                if t and len(t.strip()) >= 3:
                    valid_indices.append(j)
                    valid_texts.append(t)
            
            # Résultats par défaut pour textes invalides
            batch_results = [{'positive': 0.0, 'negative': 0.0, 'neutral': 1.0, 'compound': 0.0}] * len(batch)
            
            if not valid_texts:
                results.extend(batch_results)
                continue
            
            try:
                inputs = _tokenizer(
                    valid_texts,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                    padding=True
                ).to(_device)
                
                with _torch.no_grad():
                    outputs = _model(**inputs)
                    probs = _torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                probs = probs.cpu().numpy()
                
                for idx, p in zip(valid_indices, probs):
                    batch_results[idx] = {
                        'positive': round(float(p[0]), 4),
                        'negative': round(float(p[1]), 4),
                        'neutral': round(float(p[2]), 4),
                        'compound': round(float(p[0] - p[1]), 4)
                    }
                
                results.extend(batch_results)
                
            except Exception as e:
                print(f"⚠️ Batch error: {e}")
                results.extend([self._fallback_analyze(t) for t in batch])
        
        return results
    
    def polarity_scores(self, text: str) -> Dict[str, float]:
        """
        API compatible VADER.
        
        Args:
            text: Texte à analyser
        
        Returns:
            {'pos': 0.x, 'neg': 0.x, 'neu': 0.x, 'compound': -1 to +1}
        """
        result = self.analyze(text)
        return {
            'pos': result['positive'],
            'neg': result['negative'],
            'neu': result['neutral'],
            'compound': result['compound']
        }
    
    def _fallback_analyze(self, text: str) -> Dict[str, float]:
        """
        Fallback simple par mots-clés si FinBERT non disponible.
        Utilise lexique financier basique.
        """
        if not text:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0, 'compound': 0.0}
        
        text_lower = text.lower()
        
        # Lexique financier pondéré
        positive_words = {
            'surge': 3, 'soar': 3, 'breakthrough': 3, 'beat': 2.5, 'exceed': 2.5,
            'record': 2.5, 'boom': 2.5, 'stellar': 2.5, 'outperform': 2.5,
            'growth': 2, 'profit': 2, 'gain': 2, 'rally': 2, 'bullish': 2,
            'upgrade': 2, 'positive': 1.5, 'improve': 1.5, 'strong': 1.5,
            'rise': 1, 'increase': 1, 'up': 0.5, 'higher': 0.5
        }
        
        negative_words = {
            'crash': -3, 'collapse': -3, 'plunge': -3, 'scandal': -3, 'fraud': -3,
            'crisis': -2.5, 'disaster': -2.5, 'miss': -2.5, 'downgrade': -2.5,
            'loss': -2, 'decline': -2, 'fall': -2, 'bearish': -2, 'concern': -2,
            'lawsuit': -2, 'investigation': -2, 'weak': -1.5, 'negative': -1.5,
            'drop': -1, 'decrease': -1, 'down': -0.5, 'lower': -0.5, 'risk': -1
        }
        
        pos_score = sum(w * text_lower.count(k) for k, w in positive_words.items())
        neg_score = sum(abs(w) * text_lower.count(k) for k, w in negative_words.items())
        
        total = pos_score + neg_score
        if total > 0:
            positive = pos_score / (total + 5)  # +5 pour normalisation douce
            negative = neg_score / (total + 5)
            neutral = 1 - positive - negative
            compound = np.tanh((pos_score - neg_score) / 10)
        else:
            positive, negative, neutral, compound = 0.0, 0.0, 1.0, 0.0
        
        return {
            'positive': round(max(0, min(1, positive)), 4),
            'negative': round(max(0, min(1, negative)), 4),
            'neutral': round(max(0, min(1, neutral)), 4),
            'compound': round(max(-1, min(1, compound)), 4)
        }
    
    def clear_cache(self):
        """Libère la mémoire GPU si nécessaire"""
        global _model, _tokenizer
        if _torch and _torch.cuda.is_available():
            _torch.cuda.empty_cache()
        import gc
        gc.collect()


# Singleton global pour import facile
_analyzer_instance: Optional[FinBERTAnalyzer] = None

def get_analyzer() -> FinBERTAnalyzer:
    """Retourne l'instance singleton de FinBERTAnalyzer"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = FinBERTAnalyzer()
    return _analyzer_instance


# Test standalone
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TEST FINBERT ANALYZER")
    print("="*60 + "\n")
    
    analyzer = FinBERTAnalyzer()
    
    test_texts = [
        "Stock surged 15% after earnings beat expectations",
        "Company faces fraud investigation, shares plunge",
        "Market remains stable amid mixed economic signals",
        "CEO announces major acquisition, investors optimistic",
        "Quarterly revenue misses analyst estimates by 10%",
        "The weather is nice today",  # Neutral/non-financial
    ]
    
    print("📊 Single text analysis:\n")
    for text in test_texts:
        scores = analyzer.polarity_scores(text)
        emoji = "🟢" if scores['compound'] > 0.2 else "🔴" if scores['compound'] < -0.2 else "⚪"
        print(f"{emoji} [{scores['compound']:+.3f}] {text[:50]}...")
        print(f"   pos={scores['pos']:.3f} neg={scores['neg']:.3f} neu={scores['neu']:.3f}\n")
    
    print("\n📊 Batch analysis:\n")
    batch_results = analyzer.analyze_batch(test_texts)
    for text, scores in zip(test_texts, batch_results):
        print(f"[{scores['compound']:+.3f}] {text[:40]}...")
    
    print("\n✅ Test completed!")
