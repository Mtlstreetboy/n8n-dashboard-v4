"""
WSB Ticker Validator - Validates extracted tickers against real market data.
Removes false positives by checking against known ticker lists and market APIs.
"""

import json
import requests
from pathlib import Path
from typing import Set, Dict, List
import time

# Extended false positives list - common words that aren't tickers
EXTENDED_FALSE_POSITIVES = {
    # Common words
    'THE', 'IS', 'TO', 'AND', 'FOR', 'ON', 'IN', 'AT', 'OF', 'BY', 'WITH', 'FROM',
    'IT', 'BE', 'AS', 'OR', 'IF', 'BUT', 'SO', 'NO', 'NOT', 'NOW', 'ALL', 'YOU',
    'YOUR', 'ME', 'MY', 'WE', 'US', 'ARE', 'AM', 'WAS', 'HAVE', 'HAS', 'HAD',
    'DO', 'DOES', 'DID', 'WILL', 'JUST', 'SOME', 'MORE', 'OVER', 'UNDER', 'THEN',
    'THAN', 'UP', 'OUT', 'OFF', 'ABOUT', 'WHEN', 'WHERE', 'HOW', 'WHY', 'WHO',
    'WHAT', 'WAY', 'TIME', 'DAY', 'YEAR', 'WEEK', 'YEARS', 'TODAY', 'HERE', 'THERE',
    'MAKE', 'MADE', 'GET', 'GOT', 'GIVE', 'GAVE', 'GO', 'GOING', 'WANT', 'NEED',
    'LIKE', 'FEEL', 'HOPE', 'THINK', 'BEST', 'ONLY', 'NEVER', 'EVER', 'EVEN',
    'STILL', 'EVERY', 'SUCH', 'VERY', 'MUCH', 'NEW', 'OLD', 'OTHER', 'EACH',
    'THESE', 'THOSE', 'THEM', 'THEIR', 'BACK', 'EARLY', 'RIGHT', 'WRONG',
    
    # Slang & expressions
    'FUCK', 'SHIT', 'DAMN', 'HELL', 'WTF', 'OMG', 'LOL', 'LMAO', 'LMFAO', 'YALL',
    'GONNA', 'WANNA', 'DUDE', 'BRO', 'BRUH', 'DOPE', 'HOLY', 'DAMN', 'DUMB',
    'CRAZY', 'WILD', 'INSANE', 'WEIRD', 'FREAK', 'BULLS', 'BEARS', 'BULL', 'BEAR',
    'BTFD', 'YOLO', 'FOMO', 'FUD', 'HODL', 'MOON', 'ROCKET', 'PUMP', 'DUMP',
    'DIAMOND', 'HANDS', 'PAPER', 'APES', 'APE', 'RETARD', 'RETARDS', 'AUTIST',
    'TARD', 'GANG', 'CALLS', 'PUTS', 'CALL', 'PUT', 'STOCK', 'STOCKS', 'TRADE',
    'TRADING', 'BUY', 'SELL', 'BOUGHT', 'SOLD', 'LONG', 'SHORT', 'CASH', 'MONEY',
    
    # Time/dates
    'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY',
    'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
    
    # Numbers/measures
    'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'ZERO', 'HALF', 'FULL',
    
    # Places/entities
    'NYC', 'LA', 'SF', 'DC', 'USA', 'UK', 'EU', 'CHINA', 'JAPAN', 'EURO',
    'NATO', 'UN', 'FBI', 'CIA', 'SEC', 'FED', 'IRS', 'NASA', 'NFL', 'NBA', 'MLB',
    'ESPN', 'CNN', 'BBC', 'CBS', 'NBC', 'PBS', 'FOX', 'CNBC', 'WSJ', 'NYT',
    
    # Tech/internet
    'AI', 'ML', 'GPT', 'VPN', 'IP', 'URL', 'PDF', 'JPG', 'PNG', 'GIF', 'HTML',
    'CSS', 'API', 'UI', 'UX', 'APP', 'APPS', 'EMAIL', 'TEXT', 'POST', 'THREAD',
    
    # Actions/verbs
    'TELL', 'TOLD', 'SAY', 'SAID', 'TALK', 'SPEAK', 'LOOK', 'SEE', 'SHOW',
    'WAIT', 'STOP', 'START', 'END', 'OPEN', 'CLOSE', 'KEEP', 'TAKE', 'LEAVE',
    'COME', 'WENT', 'BEEN', 'EDIT', 'MADE', 'GETS', 'GAVE', 'TOLD', 'CAUSE',
    
    # Misc
    'LETS', 'LET', 'UNTIL', 'WHILE', 'SINCE', 'BECAUSE', 'THOUGH', 'ALTHOUGH',
    'ELSE', 'UNLESS', 'BOTH', 'EITHER', 'NEITHER', 'BETWEEN', 'AMONG',
    'THANKS', 'THANK', 'PLEASE', 'SORRY', 'HELLO', 'GOODBYE', 'OKAY', 'OK',
    'YES', 'NO', 'MAYBE', 'SURE', 'PROBABLY', 'DEFINITELY', 'EXACTLY',
    'ANYWAY', 'SOMEHOW', 'SOMEWHAT', 'SOMEWHERE', 'ANYWHERE', 'EVERYWHERE',
    'ANYONE', 'EVERYONE', 'SOMEONE', 'NOBODY', 'NOTHING', 'EVERYTHING',
    'ANYTHING', 'SOMETHING', 'TOPIC', 'TOPICS', 'QUESTION', 'ANSWER',
    'BELOW', 'ABOVE', 'UNDER', 'OVER', 'AROUND', 'THROUGH', 'ACROSS',
    'PROUD', 'HAPPY', 'SAD', 'ANGRY', 'WORRY', 'HOPE', 'FEAR', 'PEACE',
    'POWER', 'LIGHT', 'DARK', 'BLACK', 'WHITE', 'COLOR', 'EARTH', 'WORLD',
    'HOUSE', 'HOME', 'WALL', 'FLOOR', 'ROOF', 'DOOR', 'WINDOW',
    'MINE', 'OURS', 'YOURS', 'THEIRS', 'ITS', 'WHOSE',
    'DEAL', 'DEALS', 'PLAN', 'PLANS', 'PLAY', 'PLAYS', 'GAME', 'GAMES',
    'WIN', 'WON', 'LOSE', 'LOST', 'FALL', 'FELL', 'RISE', 'ROSE',
    'FIGHT', 'KILL', 'DIE', 'DEAD', 'ALIVE', 'BORN', 'GROW', 'GROWN',
    'BOYS', 'GIRLS', 'MAN', 'MEN', 'GUYS', 'DUDE', 'KING', 'QUEEN',
    'FACT', 'FACTS', 'TRUE', 'FALSE', 'REAL', 'FAKE', 'TRUTH', 'LIE',
}


def load_known_tickers() -> Set[str]:
    """Load a curated list of known valid tickers from multiple sources."""
    known_tickers = set()
    
    # Major US exchanges (manually curated subset - expand as needed)
    # Top 500 most traded stocks
    us_major = {
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'BRK.A',
        'UNH', 'XOM', 'JNJ', 'JPM', 'V', 'PG', 'MA', 'HD', 'CVX', 'MRK', 'LLY', 'ABBV',
        'COST', 'AVGO', 'PEP', 'KO', 'TMO', 'CSCO', 'MCD', 'ACN', 'ABT', 'WMT', 'DIS',
        'ADBE', 'VZ', 'CRM', 'NFLX', 'NKE', 'DHR', 'TXN', 'PM', 'NEE', 'UNP', 'BMY',
        'RTX', 'ORCL', 'INTC', 'AMD', 'QCOM', 'HON', 'INTU', 'UPS', 'LOW', 'SBUX',
        'BA', 'CAT', 'AMGN', 'GE', 'SPGI', 'BLK', 'DE', 'MDT', 'AXP', 'GILD', 'PLD',
        'MDLZ', 'CI', 'LMT', 'C', 'NOW', 'SYK', 'CB', 'TGT', 'MMC', 'PFE', 'BKNG',
        'CVS', 'AMT', 'MO', 'ZTS', 'ADP', 'VRTX', 'SCHW', 'REGN', 'TMUS', 'DUK',
        'BDX', 'SO', 'WM', 'ITW', 'PNC', 'CL', 'MMM', 'BSX', 'APD', 'USB', 'TJX',
        'SLB', 'NSC', 'GD', 'SHW', 'FI', 'HCA', 'CCI', 'ISRG', 'ICE', 'EOG', 'MAR',
        # Add more...
        'PLTR', 'HOOD', 'SOFI', 'COIN', 'RKLB', 'ASTS', 'LUNR', 'RDDT', 'MSTR',
        'GME', 'AMC', 'BB', 'NOK', 'BBBY', 'WISH', 'CLOV', 'SPCE',
        'RIOT', 'MARA', 'CLSK', 'IREN', 'CIFR', 'WULF',
        'NIO', 'XPEV', 'LI', 'LCID', 'RIVN', 'FSR',
        'SNAP', 'PINS', 'SPOT', 'UBER', 'LYFT', 'DASH', 'ABNB',
    }
    known_tickers.update(us_major)
    
    # ETFs
    etfs = {
        'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO', 'VEA', 'VWO', 'IEFA', 'IEMG',
        'AGG', 'BND', 'LQD', 'HYG', 'TLT', 'IEF', 'SHY', 'MUB',
        'GLD', 'SLV', 'GDX', 'GDXJ', 'IAU', 'USO', 'UNG', 'DBA',
        'XLF', 'XLE', 'XLV', 'XLK', 'XLI', 'XLP', 'XLY', 'XLU', 'XLB', 'XLRE',
        'VIG', 'VYM', 'SCHD', 'JEPI', 'JEPQ', 'QYLD', 'RYLD',
        'ARKK', 'ARKG', 'ARKF', 'ARKW', 'ARKQ',
        'SQQQ', 'TQQQ', 'SPXU', 'UPRO', 'SOXL', 'SOXS', 'TECL', 'TECS',
        'TNA', 'TZA', 'FAS', 'FAZ', 'ERX', 'ERY', 'LABU', 'LABD',
        'UVXY', 'SVXY', 'VXX', 'VIXY',
    }
    known_tickers.update(etfs)
    
    # Indices & Futures
    indices = {
        'SPX', 'NDX', 'DJI', 'RUT', 'VIX', 'ES', 'NQ', 'YM', 'RTY',
    }
    known_tickers.update(indices)
    
    # Crypto-related
    crypto = {
        'BTC', 'ETH', 'GBTC', 'ETHE', 'BITO', 'MSTR', 'COIN', 'BTCZ',
    }
    known_tickers.update(crypto)
    
    # Commodities
    commodities = {
        'GLD', 'SLV', 'GDX', 'GDXJ', 'GOLD', 'SILVER', 'OIL', 'GAS',
    }
    known_tickers.update(commodities)
    
    return known_tickers


def validate_ticker_yfinance(ticker: str) -> bool:
    """Validate ticker using Yahoo Finance API (lightweight check)."""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            'interval': '1d',
            'range': '5d',
        }
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # Check if there's valid chart data
            result = data.get('chart', {}).get('result', [])
            if result and result[0].get('meta', {}).get('symbol'):
                return True
        
        return False
    except Exception:
        return False


def filter_valid_tickers(ticker_data: Dict[str, dict], 
                         use_api_validation: bool = False,
                         min_mentions: int = 3) -> Dict[str, dict]:
    """
    Filter ticker data to keep only valid tickers.
    
    Args:
        ticker_data: Dictionary of {ticker: info_dict}
        use_api_validation: If True, validate against Yahoo Finance (slow)
        min_mentions: Minimum mentions to keep a ticker (helps filter noise)
    
    Returns:
        Filtered ticker data dictionary
    """
    known_tickers = load_known_tickers()
    filtered = {}
    
    print(f"\n🔍 Validating {len(ticker_data)} tickers...")
    print(f"   Known tickers in database: {len(known_tickers)}")
    print(f"   Minimum mentions threshold: {min_mentions}")
    
    validated = 0
    removed_false_positive = 0
    removed_low_volume = 0
    api_validated = 0
    
    for ticker, info in ticker_data.items():
        # Skip obvious false positives
        if ticker in EXTENDED_FALSE_POSITIVES:
            removed_false_positive += 1
            continue
        
        # Filter by mention count
        if info.get('total_mentions', 0) < min_mentions:
            removed_low_volume += 1
            continue
        
        # Check against known tickers
        if ticker in known_tickers:
            filtered[ticker] = info
            validated += 1
            continue
        
        # Optional API validation for unknown tickers with decent volume
        if use_api_validation and info.get('total_mentions', 0) >= 5:
            if validate_ticker_yfinance(ticker):
                filtered[ticker] = info
                known_tickers.add(ticker)  # Add to known list
                api_validated += 1
                validated += 1
                time.sleep(0.2)  # Rate limiting
            else:
                removed_false_positive += 1
    
    print(f"\n✅ Validation complete:")
    print(f"   ✓ Validated: {validated}")
    print(f"   ✗ False positives removed: {removed_false_positive}")
    print(f"   ✗ Low volume removed: {removed_low_volume}")
    if use_api_validation:
        print(f"   🌐 API validated: {api_validated}")
    
    return filtered


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate WSB tickers and remove false positives")
    parser.add_argument("--input", default="local_files/wsb_data/wsb_ticker_analysis.json",
                        help="Input ticker analysis JSON")
    parser.add_argument("--output", default="local_files/wsb_data/wsb_ticker_analysis_validated.json",
                        help="Output validated JSON")
    parser.add_argument("--min-mentions", type=int, default=3,
                        help="Minimum mentions to keep ticker")
    parser.add_argument("--api-validate", action="store_true",
                        help="Use Yahoo Finance API for unknown tickers (slow)")
    args = parser.parse_args()
    
    # Load analysis data
    base_dir = Path(__file__).parent.parent.parent
    input_path = base_dir / args.input
    output_path = base_dir / args.output
    
    print(f"📥 Loading ticker data from {input_path}")
    with open(input_path, 'r') as f:
        ticker_data = json.load(f)
    
    print(f"📊 Original ticker count: {len(ticker_data)}")
    
    # Filter
    validated_data = filter_valid_tickers(
        ticker_data,
        use_api_validation=args.api_validate,
        min_mentions=args.min_mentions
    )
    
    print(f"📊 Validated ticker count: {len(validated_data)}")
    
    # Save
    print(f"\n💾 Saving validated data to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validated_data, f, indent=2, ensure_ascii=False)
    
    # Show top 20
    print("\n🔝 Top 20 validated tickers:")
    sorted_tickers = sorted(validated_data.items(), 
                           key=lambda x: x[1].get('total_mentions', 0), 
                           reverse=True)[:20]
    for ticker, info in sorted_tickers:
        print(f"   {ticker:6s} | {info.get('total_mentions', 0):4d} mentions | "
              f"Momentum: {info.get('momentum', 0):+.1f}%")


if __name__ == "__main__":
    main()
