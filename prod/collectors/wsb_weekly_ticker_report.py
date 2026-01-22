#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSB Weekly Ticker Report
------------------------
Loads local_files/wsb_data/wsb_7days_posts.json, extracts tickers per day and overall,
and writes JSON outputs:
- wsb_7days_ticker_counts.json
- wsb_7days_ticker_by_day.json
- wsb_7days_top_tickers_detail.json
"""
import os
import re
import json
import argparse
import datetime
from collections import defaultdict, Counter

FALSE_POSITIVES = set([
    # Common WSB slang/acronyms and noise
    "LMAO","LOL","ROFL","YOLO","DD","ATH","PM","CEO","CFO","AI","ML","ETF","GDP","CPI","FOMC","CAGR",
    "THIS","THAT","WHAT","WHY","USA","EU","UK","NATO","MLK","NFL","NBA","NHL","FIFA","WSB","TACO","SEC",
    "APR","IRS","CIA","FBI","USD","CAD","JPOW","PCE","GDP","PPI","CAPE","ATF","IPO","SPAC","MOASS","TENDIES",
    "FDIC","IMO","OP","IMO","ASAP","BTW","DYOR","NR","PR","EPS","PE","PEG","EV","EBITDA","FCF","RSI","MACD",
    "AMD"  # keep if needed; AMD is real ticker but often used generically; we'll whitelist in KNOWN_TICKERS
])

KNOWN_TICKERS = set([
    # ETFs & indices
    "SPY","VOO","QQQ","XIU","SLV","GLD","IWM","DIA","SOXL","SOXS",
    # Mega-cap & tech
    "NVDA","AAPL","MSFT","AMZN","META","GOOGL","TSLA","AMD","INTC","MU","CRM","NFLX","SHOP","VRT","CRWD",
    # Finance & brokers
    "HOOD","SOFI","SCHD","V","MA",
    # Space/defense
    "RKLB","LMT","ASTS","LUNR",
    # Uranium / commodities
    "UUUU","CCJ","MP","URA","SLB",
    # Meme/WSB frequent
    "DJT","GME","AMC","BBBYQ","CVNA","OPEN",
])

DOLLAR_TICKER_RE = re.compile(r"\$(?:[A-Z]{1,5})(?:\.[A-Z]{1,3})?")
UPPER_TICKER_RE = re.compile(r"\b[A-Z]{2,5}(?:\.[A-Z]{1,3})?\b")

def extract_tickers(text: str) -> set:
    if not text:
        return set()
    found = set()
    for m in DOLLAR_TICKER_RE.findall(text):
        found.add(m[1:])  # drop leading $
    for m in UPPER_TICKER_RE.findall(text):
        found.add(m)
    # filter
    clean = set()
    for t in found:
        if t in FALSE_POSITIVES:
            continue
        if len(t) == 1:
            continue
        # prefer either whitelisted or plausible stock-like uppercase
        if t in KNOWN_TICKERS or (2 <= len(t) <= 5 and t.isupper()):
            clean.add(t)
    return clean

def ensure_output_dir() -> str:
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    out_dir = os.path.join(project_root, "local_files", "wsb_data")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def group_by_day(posts):
    by_day = defaultdict(list)
    for p in posts:
        ts = p.get("created_utc") or 0
        day = datetime.datetime.utcfromtimestamp(ts).date().isoformat()
        by_day[day].append(p)
    return by_day

def analyze(posts, top_n=40):
    by_day = group_by_day(posts)

    overall_counter = Counter()
    per_day_counts = {}
    detail_map = defaultdict(list)

    for day, items in by_day.items():
        c = Counter()
        for p in items:
            txt = f"{p.get('title','')}\n{p.get('selftext','')}"
            tickers = extract_tickers(txt)
            for t in tickers:
                c[t] += 1
                overall_counter[t] += 1
                detail_map[t].append({
                    "day": day,
                    "title": p.get("title"),
                    "permalink": p.get("permalink"),
                })
        per_day_counts[day] = c

    top_overall = overall_counter.most_common(top_n)

    return {
        "overall": overall_counter,
        "per_day": per_day_counts,
        "top": top_overall,
        "detail": detail_map,
    }

def to_serializable(counter_or_map):
    if isinstance(counter_or_map, Counter):
        return dict(counter_or_map)
    if isinstance(counter_or_map, dict):
        out = {}
        for k, v in counter_or_map.items():
            if isinstance(v, Counter):
                out[k] = dict(v)
            else:
                out[k] = v
        return out
    return counter_or_map

def main():
    parser = argparse.ArgumentParser(description="WSB Weekly Ticker Report")
    parser.add_argument("--input", type=str, default=None, help="Path to wsb_7days_posts.json")
    parser.add_argument("--top", type=int, default=40)
    args = parser.parse_args()

    out_dir = ensure_output_dir()
    in_path = args.input or os.path.join(out_dir, "wsb_7days_posts.json")
    if not os.path.exists(in_path):
        print(f"Input file not found: {in_path}")
        return

    with open(in_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    posts = payload.get("posts", [])
    print(f"Loaded {len(posts)} posts from {payload.get('start')} to {payload.get('end')}")

    result = analyze(posts, top_n=args.top)

    counts_path = os.path.join(out_dir, "wsb_7days_ticker_counts.json")
    byday_path = os.path.join(out_dir, "wsb_7days_ticker_by_day.json")
    detail_path = os.path.join(out_dir, "wsb_7days_top_tickers_detail.json")

    with open(counts_path, "w", encoding="utf-8") as f:
        json.dump({"overall": to_serializable(result["overall"]), "top": result["top"]}, f, ensure_ascii=False, indent=2)
    with open(byday_path, "w", encoding="utf-8") as f:
        json.dump({"per_day": to_serializable(result["per_day"])}, f, ensure_ascii=False, indent=2)
    with open(detail_path, "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in result["detail"].items()}, f, ensure_ascii=False, indent=2)

    # Console summary
    print("\nTop tickers (7 days):")
    for i, (t, n) in enumerate(result["top"], 1):
        print(f"{i:2d}. {t} ({n})")

if __name__ == "__main__":
    main()
