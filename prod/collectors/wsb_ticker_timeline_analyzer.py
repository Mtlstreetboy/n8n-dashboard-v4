#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSB Ticker Timeline Analyzer
-----------------------------
Analyzes when tickers are mentioned over time.
Groups by day, detects trends, new entries, momentum shifts.
Outputs complete timeline, not just top 40.
"""
import os
import re
import json
import argparse
import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

FALSE_POSITIVES = set([
    # Interjections & slang
    "LMAO","LOL","ROFL","YOLO","DD","ATH","PM","OMG","WTF","FML","BRUH","LMFAO","LUL","HA","YO","OG",
    "CEO","CFO","AI","ML","ETF","GDP","CPI","FOMC","CAGR","HOW","WHY","WHAT","WHERE","WHEN","WHO",
    # Common words often in caps
    "THE","AND","FOR","ARE","NOT","BUT","ALL","YOU","CAN","WAS","ONE","TWO","OUT","NOW","NEW","OLD",
    "GET","GOT","PUT","SET","LET","YES","YET","WAY","DAY","MAY","SAY","PAY","BUY","SELL","CALL","CALLS","PUTS",
    "THIS","THAT","THEN","THAN","THEM","THEY","SOME","SAME","SUCH","EVEN","EVER","JUST","ONLY","ALSO",
    "WILL","WOULD","SHOULD","COULD","MAKE","MADE","TAKE","TOOK","GIVE","GAVE","TELL","TOLD","KEEP","KEPT",
    "GOING","GONNA","WANT","NEED","LIKE","LOVE","HATE","HOPE","WISH","THINK","FEEL","KNOW","MEAN",
    "VERY","MORE","MOST","LESS","MUCH","MANY","LONG","SHORT","HIGH","FULL","HALF","BEST","WORST",
    "HERE","THERE","WHERE","BACK","AWAY","DOWN","OVER","UNDER","ABOUT","AFTER","AGAIN","BELOW","ABOVE",
    "EARLY","LATE","NEVER","STILL","WHILE","UNTIL","SINCE","CAUSE","BECAUSE",
    # Finance/trading terms
    "MONEY","CASH","BULL","BEAR","BEARS","PUMP","DUMP","MOON","TANK","CRASH","DIP","LOSS","GAIN",
    "STOCK","TRADE","PRICE","VALUE","WORTH","PROFIT","DEBIT","CREDIT","HOLD","YOLO","FOMO","FUD",
    "IPO","SPAC","MOASS","TENDIES","STONK","STONKS","HEDGE","ALPHA","BETA","THETA","DELTA","VEGA","GAMMA",
    # Organizations & geography
    "USA","EU","UK","NATO","MLK","NFL","NBA","NHL","FIFA","WSB","SEC","IRS","CIA","FBI","ATF","FDA",
    "JPOW","PCE","PPI","CAPE","FDIC","CNN","BBC","CBS","NYT","WSJ","PBS","CNBC",
    "US","UK","EU","UN","UAE","USSR","USA","NYC","SF","LA","CA","AL","FL","TX","NY",
    # Acronyms & abbreviations
    "IMO","OP","ASAP","BTW","DYOR","NR","PR","EPS","PE","PEG","EV","EBITDA","FCF","RSI","MACD",
    "CEO","CFO","CTO","COO","VP","HR","IT","QA","RN","MD","MBA","PhD","JR","SR","III","VIII",
    "AM","PM","EST","PST","UTC","GMT","EOD","EOW","EOM","EOY","YTD","MTD","QTD",
    # Random common caps
    "OK","NO","YES","OH","AH","UM","ER","UH","HM","MM","SO","TO","IN","ON","AT","BY","UP","OR","IF","AS",
    "IS","IT","BE","DO","GO","HE","ME","MY","WE","RE","IM","ID","TV","PC","CD","DVD","USB","PDF","JPG","PNG",
    "FREE","OPEN","CLOSE","START","STOP","PLAY","PAUSE","NEXT","PREV","SAVE","LOAD","EXIT","QUIT",
    "TIME","DATE","YEAR","WEEK","TODAY","EDIT","COPY","PASTE","UNDO","REDO","SEND","READ","VIEW","SHOW",
    "DUDE","GUYS","BOYS","GIRLS","KIDS","MAN","BRO","SIS","MOM","DAD","UNCLE","AUNT",
    "FUCK","SHIT","DAMN","HELL","ASS","DICK","BITCH","PUSSY","COCK","BALLS","CUNT",
    "HOLY","JESUS","GOD","LORD","DEVIL","SATAN","ANGEL","HEAVEN","HELL",
    "FOOD","BEER","WINE","MILK","BREAD","RICE","MEAT","FISH","FRUIT","TACO","TACOS","BBQ","PIZZA",
    "HOUSE","HOME","ROOM","DOOR","WALL","FLOOR","ROOF","YARD","PARK","ROAD","PATH",
    "COLOR","BLACK","WHITE","RED","GREEN","BLUE","BROWN","GRAY","PINK","PURPLE","ORANGE",
    "LIGHT","DARK","BRIGHT","SHADE","GLOW","FIRE","WATER","EARTH","WIND","METAL","ROCK",
    "KING","QUEEN","PRINCE","DUKE","LORD","KNIGHT","WIZARD","MAGE","HERO","ZERO",
    "GAME","PLAY","PLAYS","WIN","LOSE","DRAW","TEAM","PLAYER","COACH","REFEREE",
    "MUSIC","SONG","BAND","ROCK","JAZZ","BLUES","METAL","PUNK","POP","RAP","HIP","HOP",
    "BOOK","PAGE","TEXT","WORD","LINE","NOTE","EDIT","DRAFT","FINAL","TOPIC","FACTS",
    "DOPE","COOL","NICE","GOOD","BAD","UGLY","CUTE","HOT","COLD","WARM","WEIRD","WILD","CRAZY","SICK",
    "PROUD","HAPPY","SAD","MAD","ANGRY","CALM","PEACE","WAR","FIGHT","BATTLE",
    "WORLD","EARTH","MOON","STAR","SUN","SKY","SPACE","ALIEN","MARS","VENUS",
    "PEOPLE","PERSON","HUMAN","LIFE","DEATH","BIRTH","BABY","CHILD","ADULT","OLD","YOUNG","GROWN",
    "WORK","JOB","HIRE","FIRE","QUIT","RETIRE","PAY","EARN","PAID","BROKE","RICH","POOR","POORS",
    "SCHOOL","CLASS","TEACH","LEARN","STUDY","TEST","EXAM","GRADE","PASS","FAIL",
    "CLUB","PARTY","EVENT","MEET","GREET","INVITE","GUEST","HOST",
    "TRUE","FALSE","RIGHT","WRONG","CORRECT","ERROR","MISTAKE","ISSUE","PROBLEM","FIX",
    "PAPER","CARD","BOARD","SHEET","FILE","FILES","FOLDER","STACK","PILE",
    "DRIVE","RIDE","WALK","RUN","JUMP","CLIMB","SWIM","FLY","FALL","STAND","SIT",
    "WAIT","STAY","LEAVE","ARRIVE","DEPART","RETURN","VISIT","TRAVEL","TRIP",
    "PHONE","CALL","TEXT","EMAIL","MESSAGE","LETTER","NOTE","MEMO","ALERT",
    "THANK","THANKS","PLEASE","SORRY","EXCUSE","PARDON","FORGIVE",
    "AGREE","DISAGREE","SUPPORT","OPPOSE","DEFEND","ATTACK","PROTECT","GUARD",
    "BUILD","BREAK","FIX","REPAIR","DAMAGE","DESTROY","CREATE","MAKE","CRAFT",
    "BIG","SMALL","LARGE","TINY","HUGE","GIANT","MINI","MICRO","MACRO",
    "FAST","SLOW","QUICK","RAPID","SPEED","PACE","RUSH","HURRY",
    "SAFE","DANGER","RISK","THREAT","WARN","CAUTION","ALERT","ALARM",
    "STRONG","WEAK","POWER","FORCE","ENERGY","MIGHT","STRENGTH",
    "SMART","DUMB","WISE","FOOL","GENIUS","IDIOT","STUPID","CLEVER","BRIGHT",
    "EASY","HARD","SIMPLE","COMPLEX","BASIC","ADVANCED","EXPERT","NOVICE",
    "READY","STEADY","WAIT","PAUSE","RESUME","CONTINUE","PROCEED",
    "EACH","EVERY","ANY","SOME","NONE","FEW","SEVERAL","MANY",
    "FIRST","LAST","NEXT","PREV","CURRENT","PAST","FUTURE","PRESENT",
    "LEFT","RIGHT","CENTER","MIDDLE","SIDE","EDGE","CORNER","POINT",
    "TOP","BOTTOM","FRONT","REAR","INSIDE","OUTSIDE","INNER","OUTER",
    "MAIN","SIDE","SUB","SUPER","EXTRA","BONUS","SPECIAL","REGULAR","NORMAL",
    "REAL","FAKE","TRUE","FALSE","HONEST","LIE","TRUTH","FAKE","PHONY",
    "LIVE","DEAD","ALIVE","DYING","KILL","MURDER","DEATH","LIFE",
    "MALE","FEMALE","MAN","WOMAN","BOY","GIRL","MENS","WOMENS",
    "NORTH","SOUTH","EAST","WEST","CENTRAL","COASTAL",
    # Reddit/WSB specific
    "MODS","ADMIN","USER","USERS","POST","POSTS","THREAD","COMMENT","REPLY",
    "UPVOTE","DOWNVOTE","KARMA","FLAIR","SIDEBAR","WIKI","FAQ","RULES","BAN","MUTE",
    # Crypto (often false positives)
    "BTC","ETH","DOGE","SHIB","PEPE","MOON","LAMBO","HODL","WAGMI","NGMI","GM","GN",
    # Days/months
    "MON","TUE","WED","THU","FRI","SAT","SUN","JAN","FEB","MAR","APR","MAY","JUN",
    "JUL","AUG","SEP","OCT","NOV","DEC","MONDAY","TUESDAY","WEDNESDAY","THURSDAY",
    "FRIDAY","SATURDAY","SUNDAY",
])

KNOWN_TICKERS = set([
    "SPY","VOO","QQQ","XIU","SLV","GLD","IWM","DIA","SOXL","SOXS",
    "NVDA","AAPL","MSFT","AMZN","META","GOOGL","TSLA","AMD","INTC","MU","CRM","NFLX","SHOP","VRT","CRWD",
    "HOOD","SOFI","SCHD","V","MA",
    "RKLB","LMT","ASTS","LUNR",
    "UUUU","CCJ","MP","URA","SLB",
    "DJT","GME","AMC","BBBYQ","CVNA","OPEN",
])

DOLLAR_TICKER_RE = re.compile(r"\$(?:[A-Z]{1,5})(?:\.[A-Z]{1,3})?")
UPPER_TICKER_RE = re.compile(r"\b[A-Z]{2,5}(?:\.[A-Z]{1,3})?\b")

def extract_tickers(text: str) -> set:
    if not text:
        return set()
    found = set()
    for m in DOLLAR_TICKER_RE.findall(text):
        found.add(m[1:])
    for m in UPPER_TICKER_RE.findall(text):
        found.add(m)
    clean = set()
    for t in found:
        if t in FALSE_POSITIVES or len(t) == 1:
            continue
        if t in KNOWN_TICKERS or (2 <= len(t) <= 5 and t.isupper()):
            clean.add(t)
    return clean

def ensure_output_dir() -> str:
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    out_dir = os.path.join(project_root, "local_files", "wsb_data")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def load_posts(input_file: str) -> List[Dict]:
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return []
    with open(input_file, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("posts", [])

def build_timeline(posts: List[Dict]) -> Dict[str, Dict[str, int]]:
    """
    Build timeline: {date_str -> {ticker -> count}}
    """
    timeline = defaultdict(lambda: Counter())
    
    for post in posts:
        ts = post.get("created_utc") or 0
        dt = datetime.datetime.utcfromtimestamp(ts)
        day = dt.date().isoformat()
        
        txt = f"{post.get('title','')}\n{post.get('content','')}\n{post.get('full_text','')}"
        tickers = extract_tickers(txt)
        
        for t in tickers:
            timeline[day][t] += 1
    
    return {k: dict(v) for k, v in sorted(timeline.items())}

def analyze_timeline(timeline: Dict[str, Dict[str, int]]) -> Dict:
    """
    Analyze timeline for trends, new entries, momentum.
    """
    days = sorted(timeline.keys())
    all_tickers = set()
    for day_data in timeline.values():
        all_tickers.update(day_data.keys())
    
    # First appearance, momentum, total
    ticker_info = {}
    for ticker in all_tickers:
        appearances = []
        for day in days:
            count = timeline[day].get(ticker, 0)
            if count > 0:
                appearances.append((day, count))
        
        if appearances:
            first_day = appearances[0][0]
            last_day = appearances[-1][0]
            total = sum(c for _, c in appearances)
            
            # Momentum: last day vs average before
            if len(appearances) > 1:
                avg_before = sum(c for _, c in appearances[:-1]) / (len(appearances) - 1)
                last_count = appearances[-1][1]
                momentum = ((last_count - avg_before) / avg_before) if avg_before > 0 else 0
            else:
                momentum = 0
            
            ticker_info[ticker] = {
                "first_mention": first_day,
                "last_mention": last_day,
                "total_mentions": total,
                "days_active": len(appearances),
                "momentum": momentum,
                "appearances": appearances,
            }
    
    return ticker_info

def generate_report(timeline: Dict, ticker_info: Dict) -> str:
    """Generate human-readable report."""
    report = []
    report.append("=" * 80)
    report.append("🎯 WSB TICKER TIMELINE REPORT")
    report.append("=" * 80)
    
    days = sorted(timeline.keys())
    report.append(f"\n📅 Date Range: {days[0]} to {days[-1]}")
    report.append(f"📊 Total Days: {len(days)}")
    report.append(f"🏷️ Unique Tickers: {len(ticker_info)}\n")
    
    # Sort by momentum (new & trending)
    trending = sorted(
        [(t, info) for t, info in ticker_info.items()],
        key=lambda x: x[1]["momentum"],
        reverse=True
    )
    
    report.append("\n" + "=" * 80)
    report.append("🚀 TOP GAINERS (Momentum - Trending UP)")
    report.append("=" * 80)
    for ticker, info in trending[:15]:
        mom = info["momentum"]
        icon = "📈" if mom > 0.5 else "⬆️" if mom > 0.1 else "➡️"
        report.append(
            f"{icon} {ticker:6s} | Total: {info['total_mentions']:3d} | "
            f"Active: {info['days_active']}d | Momentum: {mom:+.1%} | "
            f"First: {info['first_mention']} | Last: {info['last_mention']}"
        )
    
    # New entries (appeared in last day or two)
    report.append("\n" + "=" * 80)
    report.append("✨ NEW ENTRIES (First mention in last 2 days)")
    report.append("=" * 80)
    cutoff_day = sorted([d for d in days])[-2] if len(days) > 1 else days[-1]
    new_tickers = [
        (t, info) for t, info in ticker_info.items()
        if info["first_mention"] >= cutoff_day
    ]
    if new_tickers:
        for ticker, info in sorted(new_tickers, key=lambda x: x[1]["total_mentions"], reverse=True):
            report.append(
                f"✨ {ticker:6s} | First: {info['first_mention']} | "
                f"Mentions: {info['total_mentions']} | Days: {info['days_active']}"
            )
    else:
        report.append("(No new tickers in last 2 days)")
    
    # All tickers by total volume
    report.append("\n" + "=" * 80)
    report.append("📊 ALL TICKERS (Sorted by Total Mentions)")
    report.append("=" * 80)
    by_volume = sorted(ticker_info.items(), key=lambda x: x[1]["total_mentions"], reverse=True)
    for ticker, info in by_volume:
        report.append(
            f"{ticker:6s} | Total: {info['total_mentions']:3d} | Days: {info['days_active']:2d} | "
            f"First: {info['first_mention']} | Momentum: {info['momentum']:+.1%}"
        )
    
    # Daily breakdown (sample)
    report.append("\n" + "=" * 80)
    report.append("📅 DAILY BREAKDOWN (Top 5 per day)")
    report.append("=" * 80)
    for day in days:
        day_data = timeline[day]
        top_5 = sorted(day_data.items(), key=lambda x: x[1], reverse=True)[:5]
        mentions_str = ", ".join([f"{t}({c})" for t, c in top_5])
        report.append(f"{day}: {mentions_str}")
    
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="WSB Ticker Timeline Analyzer")
    parser.add_argument("--input", type=str, default=None, help="Path to wsb_enriched_posts.json or similar")
    args = parser.parse_args()
    
    out_dir = ensure_output_dir()
    in_path = args.input or os.path.join(out_dir, "wsb_enriched_posts.json")
    
    print(f"📂 Loading posts from {in_path}...")
    posts = load_posts(in_path)
    
    if not posts:
        print("No posts found!")
        return
    
    print(f"✅ Loaded {len(posts)} posts")
    print("🔍 Building timeline...")
    
    timeline = build_timeline(posts)
    print(f"📊 Timeline complete: {len(timeline)} days")
    
    print("📈 Analyzing trends...")
    ticker_info = analyze_timeline(timeline)
    print(f"🎯 Analyzed {len(ticker_info)} unique tickers")
    
    # Generate and print report
    report = generate_report(timeline, ticker_info)
    print("\n" + report)
    
    # Save outputs
    timeline_path = os.path.join(out_dir, "wsb_ticker_timeline.json")
    analysis_path = os.path.join(out_dir, "wsb_ticker_analysis.json")
    report_path = os.path.join(out_dir, "wsb_ticker_report.txt")
    
    with open(timeline_path, "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(ticker_info, f, ensure_ascii=False, indent=2)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✅ Saved timeline to {timeline_path}")
    print(f"✅ Saved analysis to {analysis_path}")
    print(f"✅ Saved report to {report_path}")

if __name__ == "__main__":
    main()
