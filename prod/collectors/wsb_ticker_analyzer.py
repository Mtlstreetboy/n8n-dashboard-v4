#!/usr/bin/env python3
"""
WSB Ticker Analyzer - Extract and count most mentioned tickers from WSB posts
"""

import json
import re
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

# Common words that look like tickers but aren't
FALSE_POSITIVES = {
    "I", "A", "DD", "CEO", "IPO", "ETF", "GDP", "CPI", "EPS", "PE", "USA", "UK", "EU", "USD", "EUR",
    "IMO", "YOLO", "FOMO", "FUD", "ATH", "ATL", "ITM", "OTM", "IV", "DTE", "PM", "AM", "EOD", "AH",
    "THE", "FOR", "AND", "BUT", "NOT", "YOU", "ALL", "CAN", "HER", "WAS", "ONE", "OUR", "OUT", "ARE",
    "HAS", "HIS", "HOW", "ITS", "LET", "MAY", "NEW", "NOW", "OLD", "SEE", "WAY", "WHO", "BOY", "DID",
    "GET", "HIM", "GOT", "HAD", "HIM", "SAY", "SHE", "TOO", "USE", "LOL", "OMG", "WTF", "BTW", "IMO",
    "TBH", "SMH", "RN", "AF", "IRL", "TIL", "PSA", "ETA", "FAQ", "AMA", "OP", "OC", "TL", "DR", "TLDR",
    "EDIT", "UPDATE", "PT", "SP", "RSI", "MACD", "SMA", "EMA", "TA", "FA", "DD", "SEC", "FED", "FOMC",
    "NFP", "PPI", "PMI", "ISM", "JOLTS", "GDP", "CPI", "PCE", "OPEX", "VIX", "SPX", "NDX", "DJI", "RUT",
    "BTC", "ETH", "CRYPTO", "NFT", "AI", "ML", "API", "UI", "UX", "CEO", "CFO", "COO", "CTO", "IPO",
    "M&A", "P&L", "ROI", "ROE", "PE", "PB", "PS", "EV", "EBITDA", "FCF", "DCF", "NAV", "AUM", "QE",
    "QT", "ZIRP", "NIRP", "TINA", "BTFD", "GUH", "ROPE", "MOON", "TENDIES", "BAGS", "HODL", "DIAMOND",
    "PAPER", "HANDS", "APE", "APES", "REGARD", "REGARDS", "RETARD", "WSB", "GME", "MOASS", "DRS",
    "SHORT", "LONG", "BULL", "BEAR", "PUTS", "CALLS", "OPTIONS", "SHARES", "STOCK", "STOCKS",
    "BUY", "SELL", "HOLD", "PRICE", "TARGET", "SQUEEZE", "GAMMA", "THETA", "DELTA", "VEGA",
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
    "MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN", "YTD", "MTD", "QTD", "WTD", "EOY", "EOM",
    "US", "CA", "DE", "FR", "JP", "CN", "HK", "IN", "BR", "MX", "AU", "NZ", "SG", "KR", "TW",
    "NYSE", "NASDAQ", "AMEX", "OTC", "CBOE", "CME", "ICE", "LSE", "TSX", "ASX", "HKEX", "SSE",
    "LEAPS", "LEAP", "FD", "FDS", "WEEKLIES", "WEEKLY", "MONTHLIES", "MONTHLY", "EXPIRY", "STRIKE",
    "IV", "HV", "VOL", "VOLUME", "OI", "FLOAT", "SI", "CTB", "DTC", "ORTEX", "FINRA", "DTCC",
    "MM", "MMS", "HF", "HFS", "HEDGE", "FUND", "FUNDS", "RETAIL", "INSTITUTION", "INSTITUTIONAL",
    "GREEN", "RED", "UP", "DOWN", "FLAT", "PUMP", "DUMP", "RIP", "DIP", "DIPS", "RALLY", "CRASH",
    "TOP", "BOTTOM", "SUPPORT", "RESISTANCE", "TREND", "CHANNEL", "BREAKOUT", "BREAKDOWN",
    "GOLD", "SILVER", "OIL", "GAS", "CRUDE", "COPPER", "STEEL", "IRON", "COAL", "URANIUM",
    "RE", "VS", "IE", "EG", "AKA", "FYI", "ASAP", "TBA", "TBD", "TBC", "NA", "NB", "PS",
    # Additional false positives found in WSB slang
    "LMAO", "LMFAO", "ROFL", "MLK", "NATO", "NFL", "NBA", "NHL", "MLB", "UFC", "WWE", "ESPN",
    "CNN", "FOX", "BBC", "NPR", "PBS", "HBO", "AMC",  # AMC network vs AMC stock - keep as false positive, add back in known
    "TACO", "YEET", "BASED", "CHAD", "KAREN", "BOOMER", "ZOOMER", "DOOMER", "COOMER",
    "THIS", "THAT", "WILL", "HAVE", "BEEN", "WERE", "THEY", "THEM", "WHAT", "WHEN", "WHERE",
    "JUST", "ONLY", "EVEN", "ALSO", "MORE", "MOST", "SOME", "MANY", "MUCH", "VERY", "SUCH",
    "LIKE", "WANT", "NEED", "KNOW", "THINK", "LOOK", "COME", "MAKE", "TAKE", "GIVE", "KEEP",
    "FIND", "TELL", "WORK", "SEEM", "FEEL", "LIVE", "LEAVE", "CALL", "LAST", "LONG", "GOOD",
    "BEST", "WELL", "BACK", "OVER", "SUCH", "ONLY", "YEAR", "INTO", "MOST", "MADE", "AFTER",
    "OPEN", "PLUS", "NEXT", "LESS", "THAN", "THEN", "BEFORE", "MONEY", "THING", "EVERY",
    "NEVER", "STILL", "AGAIN", "THOSE", "BEING", "WOULD", "COULD", "SHOULD", "MIGHT",
    "NEWS", "REAL", "TRUE", "FAKE", "FACT", "DATA", "INFO", "LINK", "POST", "COMMENT",
    "FUCK", "SHIT", "DAMN", "HELL", "CRAP", "DUMB", "STUPID", "CRAZY", "INSANE", "WILD",
    "CIA", "FBI", "NSA", "DOJ", "DOD", "EPA", "FDA", "FTC", "IRS", "SSA", "CDC", "NIH",
    "EST", "PST", "CST", "MST", "UTC", "GMT", "EOW", "EOD", "EOY", "YOY", "MOM", "QOQ",
    "WSJ", "NYT", "WP", "AP", "CNBC", "MSNBC", "ABC", "CBS", "NBC",
    "ASS", "DICK", "BALLS", "COCK", "PUSSY", "TITS", "BOOBS",
    "WANT", "GONNA", "GOTTA", "WANNA", "KINDA", "SORTA",
    "EDIT", "UPDATE", "NOTE", "TLDR", "IMHO", "AFAIK", "IIRC",
}

# Known valid tickers (popular ones to ensure they're caught)
KNOWN_TICKERS = {
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC",
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "ARKK", "SOXL", "TQQQ", "SQQQ",
    "PLTR", "SOFI", "HOOD", "COIN", "MSTR", "RKLB", "LUNR", "ASTS", "RUM",
    "GME", "AMC", "BB", "NOK", "BBBY", "CLOV", "WISH", "WKHS", "RIDE",
    "NIO", "RIVN", "LCID", "F", "GM", "TM", "XPEV", "LI",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "PYPL", "SQ",
    "DIS", "NFLX", "ROKU", "SPOT", "SNAP", "PINS", "TWTR", "UBER", "LYFT",
    "WMT", "TGT", "COST", "HD", "LOW", "AMZN", "EBAY", "ETSY",
    "PFE", "MRNA", "JNJ", "ABBV", "LLY", "UNH", "CVS", "WBA",
    "XOM", "CVX", "COP", "OXY", "BP", "SHEL", "SLB", "HAL",
    "BA", "LMT", "RTX", "NOC", "GD", "CAT", "DE", "MMM",
    "UUUU", "MP", "CCJ", "LEU", "LYC", "NXE", "UEC", "URG", "DNN",
    "GLD", "SLV", "USO", "UNG", "WEAT", "CORN", "SOYB",
    "POET", "SMCI", "ARM", "AVGO", "MU", "QCOM", "TXN", "AMAT", "LRCX", "KLAC",
    # Additional popular tickers
    "DJT", "CVNA", "BABA", "JD", "PDD", "SHOP", "SE", "MELI", "GRAB",
    "CRWD", "NET", "ZS", "PANW", "DDOG", "SNOW", "MDB", "TEAM", "OKTA",
    "SQ", "AFRM", "UPST", "LC", "NU", "OPEN",  # Note: OPEN is fintech OpenDoor
    "IONQ", "RGTI", "QUBT", "QBTS",  # Quantum computing
    "MARA", "RIOT", "CLSK", "HUT", "BTBT", "CIFR",  # Crypto miners
}

def extract_tickers(text: str) -> list:
    """Extract potential stock tickers from text."""
    if not text:
        return []
    
    tickers = []
    
    # Pattern 1: $TICKER format (most reliable)
    dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text.upper())
    tickers.extend(dollar_tickers)
    
    # Pattern 2: Standalone uppercase words that look like tickers (2-5 chars)
    # More strict: must be surrounded by spaces or punctuation
    words = re.findall(r'\b([A-Z]{2,5})\b', text)
    for word in words:
        word_upper = word.upper()
        # Include if it's a known ticker or looks like a ticker and not a false positive
        if word_upper in KNOWN_TICKERS:
            tickers.append(word_upper)
        elif word_upper not in FALSE_POSITIVES and len(word_upper) >= 3:
            # Check if it's likely a ticker (all caps in original)
            if word == word.upper():
                tickers.append(word_upper)
    
    return tickers


def analyze_posts(input_file: str) -> dict:
    """Analyze posts and extract ticker mentions."""
    print(f"📂 Loading {input_file}...")
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    posts = data.get("posts", [])
    print(f"📊 Analyzing {len(posts)} posts...")
    
    ticker_counts = Counter()
    ticker_posts = {}  # ticker -> list of post snippets
    ticker_sentiment_texts = {}  # ticker -> list of full texts for sentiment
    
    for post in posts:
        text = post.get("full_text", "") or post.get("content", "") or post.get("body", "")
        title = post.get("title", "")
        full_text = f"{title} {text}"
        
        tickers = extract_tickers(full_text)
        unique_tickers = set(tickers)
        
        for ticker in unique_tickers:
            ticker_counts[ticker] += 1
            
            if ticker not in ticker_posts:
                ticker_posts[ticker] = []
                ticker_sentiment_texts[ticker] = []
            
            # Store snippet for display
            snippet = full_text[:200].replace("\n", " ")
            ticker_posts[ticker].append({
                "snippet": snippet,
                "author": post.get("author", "unknown"),
                "score": post.get("score", 0),
                "url": post.get("url", ""),
            })
            
            # Store full text for sentiment analysis
            ticker_sentiment_texts[ticker].append(full_text)
    
    return {
        "ticker_counts": ticker_counts,
        "ticker_posts": ticker_posts,
        "ticker_sentiment_texts": ticker_sentiment_texts,
        "total_posts": len(posts),
    }


def print_report(analysis: dict, top_n: int = 30):
    """Print ticker analysis report."""
    ticker_counts = analysis["ticker_counts"]
    ticker_posts = analysis["ticker_posts"]
    total_posts = analysis["total_posts"]
    
    print("\n" + "=" * 70)
    print("📈 WSB TICKER MENTIONS ANALYSIS")
    print("=" * 70)
    print(f"Total posts analyzed: {total_posts}")
    print(f"Unique tickers found: {len(ticker_counts)}")
    print("=" * 70)
    
    print(f"\n🔥 TOP {top_n} MOST MENTIONED TICKERS:\n")
    print(f"{'Rank':<6}{'Ticker':<10}{'Mentions':<12}{'% of Posts':<12}Sample Context")
    print("-" * 70)
    
    for i, (ticker, count) in enumerate(ticker_counts.most_common(top_n), 1):
        pct = (count / total_posts) * 100
        
        # Get best sample (highest score)
        samples = ticker_posts.get(ticker, [])
        if samples:
            best_sample = max(samples, key=lambda x: x.get("score", 0))
            snippet = best_sample["snippet"][:40] + "..."
        else:
            snippet = ""
        
        print(f"{i:<6}${ticker:<9}{count:<12}{pct:>6.1f}%     {snippet}")
    
    print("\n" + "=" * 70)
    
    # Category breakdown
    print("\n📊 CATEGORY BREAKDOWN:\n")
    
    categories = {
        "🚀 Space/Defense": ["RKLB", "LUNR", "ASTS", "RUM", "LMT", "RTX", "NOC", "BA"],
        "💻 Tech Giants": ["AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA"],
        "🔌 Semiconductors": ["AMD", "INTC", "AVGO", "MU", "QCOM", "SMCI", "ARM", "AMAT"],
        "⚛️ Uranium/Rare Earths": ["UUUU", "MP", "CCJ", "LEU", "LYC", "NXE", "UEC", "DNN"],
        "🏦 Finance": ["JPM", "BAC", "GS", "V", "MA", "PYPL", "SQ", "SOFI", "HOOD", "COIN"],
        "🛢️ Energy": ["XOM", "CVX", "OXY", "COP", "BP", "SHEL"],
        "🎮 Meme Stocks": ["GME", "AMC", "BB", "NOK", "PLTR"],
        "📊 ETFs": ["SPY", "QQQ", "IWM", "TQQQ", "SQQQ", "ARKK", "SOXL"],
        "🥇 Commodities": ["GLD", "SLV", "USO", "UNG"],
    }
    
    for cat_name, cat_tickers in categories.items():
        cat_total = sum(ticker_counts.get(t, 0) for t in cat_tickers)
        if cat_total > 0:
            top_in_cat = [(t, ticker_counts.get(t, 0)) for t in cat_tickers if ticker_counts.get(t, 0) > 0]
            top_in_cat.sort(key=lambda x: -x[1])
            top_str = ", ".join([f"${t}({c})" for t, c in top_in_cat[:5]])
            print(f"{cat_name}: {cat_total} mentions - {top_str}")
    
    print("\n" + "=" * 70)


def save_results(analysis: dict, output_dir: str):
    """Save analysis results to files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save ticker counts
    counts_file = output_path / "wsb_ticker_counts.json"
    with open(counts_file, "w", encoding="utf-8") as f:
        json.dump({
            "analyzed_at": datetime.now().isoformat(),
            "total_posts": analysis["total_posts"],
            "ticker_counts": dict(analysis["ticker_counts"].most_common(100)),
        }, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved ticker counts to {counts_file}")
    
    # Save detailed data for each top ticker
    top_tickers_file = output_path / "wsb_top_tickers_detail.json"
    top_tickers_data = {}
    for ticker, count in analysis["ticker_counts"].most_common(50):
        top_tickers_data[ticker] = {
            "mention_count": count,
            "sample_posts": analysis["ticker_posts"].get(ticker, [])[:10],
        }
    
    with open(top_tickers_file, "w", encoding="utf-8") as f:
        json.dump(top_tickers_data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved top tickers detail to {top_tickers_file}")
    
    # Save texts grouped by ticker for sentiment analysis
    sentiment_input_file = output_path / "wsb_ticker_texts_for_sentiment.json"
    sentiment_data = {}
    for ticker, count in analysis["ticker_counts"].most_common(30):
        texts = analysis["ticker_sentiment_texts"].get(ticker, [])
        sentiment_data[ticker] = {
            "mention_count": count,
            "texts": texts[:100],  # Limit to 100 texts per ticker
        }
    
    with open(sentiment_input_file, "w", encoding="utf-8") as f:
        json.dump(sentiment_data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved ticker texts for sentiment to {sentiment_input_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze WSB ticker mentions")
    parser.add_argument("--input", default="./local_files/wsb_data/wsb_enriched_posts.json",
                        help="Input JSON file with posts")
    parser.add_argument("--output-dir", default="./local_files/wsb_data",
                        help="Output directory for results")
    parser.add_argument("--top", type=int, default=30,
                        help="Number of top tickers to show")
    args = parser.parse_args()
    
    analysis = analyze_posts(args.input)
    print_report(analysis, top_n=args.top)
    save_results(analysis, args.output_dir)


if __name__ == "__main__":
    main()
