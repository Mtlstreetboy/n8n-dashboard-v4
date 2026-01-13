#!/usr/bin/env python3
"""
LLM-based Relative Sentiment Analysis with Temporal Trends
Uses Llama3 for deep contextual analysis
"""

import requests
import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from email.utils import parsedate_to_datetime

OLLAMA_URL = "http://ollama_local_ai:11434"

def llm_analyze_sentiment_relative(
    article: Dict,
    recent_articles: List[Dict],
    ticker: str,
    company_name: str
) -> Dict:
    """
    Analyze article sentiment relative to other company news
    
    Args:
        article: Article to analyze
        recent_articles: Recent company news (context)
        ticker: Company ticker
        company_name: Company name
    
    Returns:
        dict: {
            'sentiment_score': -100 to +100,
            'category': 'very positive' | 'positive' | 'neutral' | 'negative' | 'very negative',
            'confidence': 0-1,
            'reasoning': 'Detailed explanation',
            'key_factors': ['factor1', 'factor2', ...],
            'comparative_context': 'How it compares to other news'
        }
    """
    
    # Prepare recent news context (top 5)
    context_news = []
    for i, ctx_article in enumerate(recent_articles[:5], 1):
        pub_date = ctx_article.get('published_at', 'Unknown')
        context_news.append(
            f"{i}. [{pub_date}] {ctx_article['title']}\n"
            f"   {ctx_article.get('description', 'N/A')[:200]}"
        )
    
    context_text = "\n".join(context_news) if context_news else "No recent news available"
    
    prompt = f"""You are an expert financial analyst specialized in sentiment analysis of stock market news.

COMPANY: {company_name} ({ticker})

CONTEXT - Recent news about this company:
{context_text}

NEWS TO ANALYZE:
Date: {article.get('published_at', 'Unknown')}
Title: {article['title']}
Description: {article.get('description', 'N/A')}

TASK:
Analyze the sentiment of this news by COMPARING it to other recent news about {company_name}.

Respond ONLY with valid JSON (no markdown, no ```json):
{{
    "sentiment_score": <number between -100 (very negative) and +100 (very positive)>,
    "category": "<very positive|positive|neutral|negative|very negative>",
    "confidence": <number between 0 and 1>,
    "reasoning": "<detailed explanation in 2-3 sentences>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"],
    "comparative_context": "<how this news compares to recent ones: better/similar/worse>"
}}

EVALUATION CRITERIA:
- Financial performance (earnings, revenue, guidance)
- Strategic partnerships and major deals
- Product innovations and technology
- Management and leadership
- Legal issues, regulations
- Competition and market position
- Overall market sentiment toward the company

IMPORTANT: 
- Compare this news to others to determine if it's more positive, negative, or similar
- If all recent news is negative, this one should also be negative even if it seems "neutral" in isolation
- The score should reflect the relative impact on stock price"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 1000  # Increased from 500 to prevent JSON truncation
            },
            timeout=60
        )
        
        if response.status_code != 200:
            return {
                'sentiment_score': 0,
                'category': 'neutral',
                'confidence': 0,
                'reasoning': f'API Error: HTTP {response.status_code}',
                'key_factors': [],
                'comparative_context': 'Error',
                'error': True
            }
        
        result = response.json()
        llm_output = result.get('response', '').strip()
        
        # Parse JSON - clean markdown blocks if present
        if '```json' in llm_output:
            llm_output = llm_output.split('```json')[1].split('```')[0].strip()
        elif '```' in llm_output:
            llm_output = llm_output.split('```')[1].split('```')[0].strip()
        
        # Extract JSON if LLM adds text before/after
        start_idx = llm_output.find('{')
        end_idx = llm_output.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            llm_output = llm_output[start_idx:end_idx+1]
        
        # Clean problematic characters that break JSON parsing
        # Replace smart quotes with regular quotes
        llm_output = llm_output.replace('\u201c', '\"').replace('\u201d', '\"')
        llm_output = llm_output.replace('\u2018', "'").replace('\u2019', "'")
        llm_output = llm_output.replace('\u2013', '-').replace('\u2014', '-')
        
        # Try parsing with error recovery
        try:
            sentiment_data = json.loads(llm_output)
        except json.JSONDecodeError as e:
            # Attempt to fix common issues
            # Remove trailing commas before }
            llm_output = llm_output.replace(',\n}', '\n}').replace(', }', ' }')
            # Try again
            try:
                sentiment_data = json.loads(llm_output)
            except json.JSONDecodeError:
                # Last resort: return error with original message
                return {
                    'sentiment_score': 0,
                    'category': 'neutral',
                    'confidence': 0,
                    'reasoning': f'JSON parsing error: {str(e)} | Output length: {len(llm_output)}',
                    'key_factors': [],
                    'comparative_context': 'Parsing error - output may be truncated',
                    'error': True,
                    'raw_output': llm_output[:500]  # Store first 500 chars for debugging
                }
        
        # Validation
        sentiment_score = max(-100, min(100, sentiment_data.get('sentiment_score', 0)))
        
        return {
            'sentiment_score': sentiment_score,
            'category': sentiment_data.get('category', 'neutral'),
            'confidence': max(0, min(1, sentiment_data.get('confidence', 0.5))),
            'reasoning': sentiment_data.get('reasoning', ''),
            'key_factors': sentiment_data.get('key_factors', []),
            'comparative_context': sentiment_data.get('comparative_context', ''),
            'error': False
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"LLM output: {llm_output[:500]}")
        return {
            'sentiment_score': 0,
            'category': 'neutral',
            'confidence': 0,
            'reasoning': f'Parsing error: {str(e)}',
            'key_factors': [],
            'comparative_context': 'Parsing error',
            'error': True
        }
        
    except requests.exceptions.RequestException as e:
        print(f"LLM request error: {e}")
        return {
            'sentiment_score': 0,
            'category': 'neutral',
            'confidence': 0,
            'reasoning': f'LLM API connection error: {str(e)}',
            'key_factors': [],
            'comparative_context': 'API error',
            'error': True
        }
    except Exception as e:
        print(f"LLM analysis error: {e}")
        return {
            'sentiment_score': 0,
            'category': 'neutral',
            'confidence': 0,
            'reasoning': f'Error: {str(e)}',
            'key_factors': [],
            'comparative_context': 'Error',
            'error': True
        }


def calculate_temporal_trend(articles: List[Dict], days: int = 7) -> Dict:
    """
    Calculate temporal trend over N days
    
    Returns:
        dict: {
            'trend_coefficient': -1 to +1 (negative = decline, positive = rise),
            'momentum': -1 to +1 (acceleration),
            'avg_sentiment_7d': 7-day average,
            'avg_sentiment_30d': 30-day average,
            'volatility': standard deviation,
            'direction': 'strong rise' | 'rise' | 'stable' | 'decline' | 'strong decline'
        }
    """
    
    # Filter articles with sentiment analyzed
    analyzed = [a for a in articles if 'llm_sentiment' in a]
    
    if len(analyzed) < 3:
        return {
            'trend_coefficient': 0,
            'momentum': 0,
            'avg_sentiment_7d': 0,
            'avg_sentiment_30d': 0,
            'volatility': 0,
            'direction': 'insufficient data',
            'insufficient_data': True
        }
    
    # Sort by date (handle both ISO and RSS formats) - ALWAYS return tz-aware datetimes
    def parse_date(article):
        date_str = article.get('published_at', '2000-01-01')
        from datetime import timezone
        dt = None

        # If the stored value is already a datetime, use it
        try:
            if isinstance(date_str, datetime):
                dt = date_str
            else:
                # Try ISO format first
                dt = datetime.fromisoformat(date_str)
        except (ValueError, TypeError, AttributeError):
            try:
                # Try RSS format parser
                dt = parsedate_to_datetime(date_str)
            except Exception:
                # Fallback: use a distant past date but timezone-aware
                dt = datetime(2000, 1, 1, tzinfo=timezone.utc)

        # Ensure timezone-aware for comparisons/sorting
        if dt is not None and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    
    analyzed_sorted = sorted(
        analyzed,
        key=parse_date,
        reverse=True
    )
    
    from datetime import timezone
    now = datetime.now(timezone.utc)
    cutoff_7d = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)
    
    # Separate by period
    last_7d = []
    last_30d = []
    
    for article in analyzed_sorted:
        pub_date_str = article.get('published_at', '2000-01-01')
        try:
            pub_date = datetime.fromisoformat(pub_date_str)
        except:
            try:
                pub_date = parsedate_to_datetime(pub_date_str)
            except:
                # Fallback: use current date if parsing fails
                pub_date = now
        
        # Make timezone-aware if naive
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
        
        sentiment = article['llm_sentiment']['sentiment_score']
        
        if pub_date >= cutoff_7d:
            last_7d.append(sentiment)
        if pub_date >= cutoff_30d:
            last_30d.append(sentiment)
    
    # Averages
    avg_7d = np.mean(last_7d) if last_7d else 0
    avg_30d = np.mean(last_30d) if last_30d else avg_7d
    
    # Volatility
    volatility = np.std(last_7d) if len(last_7d) > 1 else 0
    
    # Trend coefficient (compare 7d vs 30d)
    if avg_30d != 0:
        trend_coefficient = (avg_7d - avg_30d) / (abs(avg_30d) + 10)
    else:
        trend_coefficient = 0
    
    # Momentum (acceleration): compare last 3d vs 7d
    if len(last_7d) >= 6:
        last_3d_avg = np.mean(last_7d[:3])
        days_4_to_7_avg = np.mean(last_7d[3:7])
        momentum = (last_3d_avg - days_4_to_7_avg) / 50
    else:
        momentum = 0
    
    # Direction
    if trend_coefficient > 0.3:
        direction = 'strong rise'
    elif trend_coefficient > 0.1:
        direction = 'rise'
    elif trend_coefficient < -0.3:
        direction = 'strong decline'
    elif trend_coefficient < -0.1:
        direction = 'decline'
    else:
        direction = 'stable'
    
    return {
        'trend_coefficient': float(np.clip(trend_coefficient, -1, 1)),
        'momentum': float(np.clip(momentum, -1, 1)),
        'avg_sentiment_7d': float(avg_7d),
        'avg_sentiment_30d': float(avg_30d),
        'volatility': float(volatility),
        'direction': direction,
        'insufficient_data': False,
        'sample_size_7d': len(last_7d),
        'sample_size_30d': len(last_30d)
    }


def adjust_sentiment_with_trend(
    sentiment_score: float,
    trend_data: Dict
) -> float:
    """
    Adjust raw sentiment with temporal trend
    
    Formula:
    sentiment_final = sentiment_score * 0.70 +
                      trend_coefficient * 20 +
                      momentum * 10
    """
    
    if trend_data.get('insufficient_data'):
        return sentiment_score
    
    trend_coef = trend_data['trend_coefficient']
    momentum = trend_data['momentum']
    
    adjusted = (
        sentiment_score * 0.70 +
        trend_coef * 20 +
        momentum * 10
    )
    
    return float(np.clip(adjusted, -100, 100))


def analyze_article_full(
    article: Dict,
    all_articles: List[Dict],
    ticker: str,
    company_name: str
) -> Dict:
    """
    Full article analysis: relative sentiment + temporal adjustment
    """
    
    # 1. Relative sentiment analysis via LLM
    article_url = article.get('url', '')
    recent_articles = [a for a in all_articles if a.get('url', '') != article_url][:10]
    
    llm_result = llm_analyze_sentiment_relative(
        article,
        recent_articles,
        ticker,
        company_name
    )
    
    # 2. Calculate temporal trend
    trend_data = calculate_temporal_trend(all_articles)
    
    # 3. Adjust sentiment with trend
    sentiment_raw = llm_result['sentiment_score']
    sentiment_adjusted = adjust_sentiment_with_trend(sentiment_raw, trend_data)
    
    return {
        'llm_sentiment': llm_result,
        'sentiment_raw': sentiment_raw,
        'sentiment_adjusted': sentiment_adjusted,
        'trend_data': trend_data,
        'sentiment_analyzed': True,
        'analysis_timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("Testing LLM relative sentiment...")
    
    test_article = {
        'url': 'test1',
        'title': 'NVIDIA announces record Q4 earnings, beating analyst expectations',
        'description': 'The AI chip maker reported revenue growth of 265% year-over-year',
        'published_at': datetime.now().isoformat()
    }
    
    context_articles = [
        {
            'url': 'ctx1',
            'title': 'NVIDIA faces new competition from AMD in AI chip market',
            'description': 'AMD announces competitive pricing strategy',
            'published_at': (datetime.now() - timedelta(days=1)).isoformat()
        }
    ]
    
    result = llm_analyze_sentiment_relative(
        test_article,
        context_articles,
        'NVDA',
        'NVIDIA Corporation'
    )
    
    print(f"\nResult:")
    print(f"Score: {result['sentiment_score']}")
    print(f"Category: {result['category']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Reasoning: {result['reasoning']}")
