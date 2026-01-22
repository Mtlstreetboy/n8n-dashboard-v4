#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSB 7-Day Collector
-------------------
Fetches r/wallstreetbets posts from the "new" feed over a date range,
using old.reddit JSON + pagination via "after".
Outputs: local_files/wsb_data/wsb_7days_posts.json
"""
import os
import json
import time
import argparse
import datetime
import requests
from typing import List, Dict

OLD_REDDIT_NEW = "https://old.reddit.com/r/wallstreetbets/new.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WSB-Collector/1.0",
    "Accept": "application/json"
}

def ensure_output_dir() -> str:
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    out_dir = os.path.join(project_root, "local_files", "wsb_data")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def fetch_page(after: str = None, limit: int = 100) -> Dict:
    params = {"limit": limit}
    if after:
        params["after"] = after
    resp = requests.get(OLD_REDDIT_NEW, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()

def parse_posts(payload: Dict) -> List[Dict]:
    children = payload.get("data", {}).get("children", [])
    posts = []
    for item in children:
        d = item.get("data", {})
        posts.append({
            "id": d.get("id"),
            "name": d.get("name"),  # fullname like t3_...
            "title": d.get("title"),
            "selftext": d.get("selftext"),
            "permalink": d.get("permalink"),
            "url": d.get("url"),
            "author": d.get("author"),
            "created_utc": d.get("created_utc"),
            "num_comments": d.get("num_comments"),
            "score": d.get("score"),
            "over_18": d.get("over_18"),
        })
    return posts

def collect_range(start_ts: int, end_ts: int, max_pages: int = 200) -> List[Dict]:
    all_posts = []
    after = None
    pages = 0
    while pages < max_pages:
        payload = fetch_page(after=after, limit=100)
        posts = parse_posts(payload)
        if not posts:
            break
        # Filter by time bounds
        for p in posts:
            ts = p.get("created_utc") or 0
            if ts >= start_ts and ts < end_ts:
                all_posts.append(p)
        # Pagination: get last post's fullname
        last = posts[-1]
        after = last.get("name")  # e.g., t3_xxxxx
        pages += 1
        # Stop if we're already older than start_ts
        last_ts = last.get("created_utc") or 0
        if last_ts < start_ts:
            break
        time.sleep(0.5)  # be polite
    return all_posts

def main():
    parser = argparse.ArgumentParser(description="Collect WSB posts for a 7-day window")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD) exclusive")
    parser.add_argument("--anchor", type=str, help="Anchor date (YYYY-MM-DD) to collect last 7 days ending before it")
    args = parser.parse_args()

    if args.anchor:
        anchor = datetime.datetime.strptime(args.anchor, "%Y-%m-%d")
        start_dt = anchor - datetime.timedelta(days=7)
        end_dt = anchor
    else:
        if not args.start or not args.end:
            # Default: last 7 full days before today
            today = datetime.datetime.utcnow().date()
            end_dt = datetime.datetime.combine(today, datetime.time.min)
            start_dt = end_dt - datetime.timedelta(days=7)
        else:
            start_dt = datetime.datetime.strptime(args.start, "%Y-%m-%d")
            end_dt = datetime.datetime.strptime(args.end, "%Y-%m-%d")

    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    print(f"Collecting WSB posts from {start_dt.date()} to {end_dt.date()} (UTC)")
    posts = collect_range(start_ts, end_ts)
    print(f"Collected {len(posts)} posts in range")

    out_dir = ensure_output_dir()
    out_path = os.path.join(out_dir, "wsb_7days_posts.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "start": start_dt.strftime("%Y-%m-%d"),
            "end": end_dt.strftime("%Y-%m-%d"),
            "count": len(posts),
            "posts": posts,
        }, f, ensure_ascii=False, indent=2)
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()
