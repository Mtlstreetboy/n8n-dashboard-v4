#!/usr/bin/env python3
"""
WSB Thread Scraper - Extracts comments from mega-threads (Daily Discussion, What Are Your Moves)
Uses Reddit JSON endpoint with pagination to get all comments.
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configuration
WSB_DATA_DIR = os.environ.get("WSB_DATA_DIR", "./local_files/wsb_data")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_DELAY = 2  # seconds between requests to avoid rate limiting
MIN_COMMENT_LENGTH = 20  # minimum characters to include a comment

# Thread IDs to scrape (without t3_ prefix)
DEFAULT_THREADS = [
    "1qh2cle",  # Daily Discussion Thread for January 19, 2026
    "1qgk3q8",  # What Are Your Moves Tomorrow, January 19, 2026
]


def fetch_thread_json(thread_id: str, limit: int = 500, sort: str = "new") -> dict:
    """Fetch thread JSON from Reddit with higher limit."""
    url = f"https://www.reddit.com/r/wallstreetbets/comments/{thread_id}.json"
    params = {"limit": limit, "sort": sort, "depth": 10, "showmore": True}
    
    headers = {"User-Agent": USER_AGENT}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ❌ Error fetching {thread_id}: {e}")
        return None


def fetch_more_comments(thread_id: str, children_ids: list, link_id: str) -> list:
    """Fetch additional comments using Reddit's morechildren endpoint."""
    if not children_ids:
        return []
    
    url = "https://www.reddit.com/api/morechildren.json"
    headers = {"User-Agent": USER_AGENT}
    
    all_comments = []
    # Process in batches of 100 (Reddit limit)
    batch_size = 100
    
    for i in range(0, len(children_ids), batch_size):
        batch = children_ids[i:i + batch_size]
        params = {
            "api_type": "json",
            "link_id": f"t3_{link_id}",
            "children": ",".join(batch),
            "limit_children": False,
            "sort": "new",
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            things = data.get("json", {}).get("data", {}).get("things", [])
            for thing in things:
                if thing.get("kind") == "t1":
                    comment_data = thing.get("data", {})
                    body = comment_data.get("body", "")
                    if body and len(body) >= MIN_COMMENT_LENGTH and body not in ["[deleted]", "[removed]"]:
                        all_comments.append({
                            "id": comment_data.get("id", ""),
                            "author": comment_data.get("author", "[deleted]"),
                            "body": body,
                            "score": comment_data.get("score", 0),
                            "created_utc": comment_data.get("created_utc", 0),
                            "permalink": comment_data.get("permalink", ""),
                            "depth": comment_data.get("depth", 0),
                        })
            
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            print(f"    ⚠️ Error fetching more comments: {e}")
            continue
    
    return all_comments


def extract_comments_recursive(comment_data: dict, comments: list, more_ids: list, depth: int = 0):
    """Recursively extract comments from nested structure and collect 'more' IDs."""
    if not isinstance(comment_data, dict):
        return
    
    kind = comment_data.get("kind", "")
    data = comment_data.get("data", {})
    
    if kind == "t1":  # Comment
        body = data.get("body", "")
        if body and len(body) >= MIN_COMMENT_LENGTH and body not in ["[deleted]", "[removed]"]:
            comments.append({
                "id": data.get("id", ""),
                "author": data.get("author", "[deleted]"),
                "body": body,
                "score": data.get("score", 0),
                "created_utc": data.get("created_utc", 0),
                "permalink": data.get("permalink", ""),
                "depth": depth,
            })
        
        # Process replies
        replies = data.get("replies", "")
        if isinstance(replies, dict):
            children = replies.get("data", {}).get("children", [])
            for child in children:
                extract_comments_recursive(child, comments, more_ids, depth + 1)
    
    elif kind == "more":  # More comments to load
        children = data.get("children", [])
        more_ids.extend(children)
    
    elif kind == "Listing":
        children = data.get("children", [])
        for child in children:
            extract_comments_recursive(child, comments, more_ids, depth)


def scrape_thread(thread_id: str, max_more_batches: int = 50) -> dict:
    """Scrape all comments from a thread including 'more' comments."""
    print(f"\n📥 Scraping thread: {thread_id}")
    
    all_comments = []
    more_ids = []
    thread_info = {}
    
    # Initial fetch with high limit
    print(f"  📄 Fetching initial comments...")
    data = fetch_thread_json(thread_id, limit=500, sort="new")
    
    if not data or len(data) < 2:
        print(f"  ❌ Failed to fetch thread")
        return {"thread": {}, "comments": [], "scraped_at": datetime.now().isoformat()}
    
    # Extract thread info
    post_data = data[0].get("data", {}).get("children", [{}])[0].get("data", {})
    thread_info = {
        "id": thread_id,
        "title": post_data.get("title", ""),
        "author": post_data.get("author", ""),
        "created_utc": post_data.get("created_utc", 0),
        "num_comments": post_data.get("num_comments", 0),
        "url": f"https://www.reddit.com/r/wallstreetbets/comments/{thread_id}/",
    }
    print(f"  📝 Thread: {thread_info['title'][:60]}...")
    print(f"  💬 Total comments reported: {thread_info['num_comments']}")
    
    # Extract initial comments and collect "more" IDs
    comments_data = data[1] if len(data) > 1 else {}
    extract_comments_recursive(comments_data, all_comments, more_ids)
    print(f"  ➕ Initial: {len(all_comments)} comments, {len(more_ids)} 'more' IDs found")
    
    # Fetch additional comments from "more" objects
    if more_ids and max_more_batches > 0:
        print(f"  🔄 Fetching additional comments...")
        batches_to_process = min(len(more_ids), max_more_batches * 100)
        ids_to_fetch = more_ids[:batches_to_process]
        
        additional = fetch_more_comments(thread_id, ids_to_fetch, thread_id)
        
        # Deduplicate
        existing_ids = {c["id"] for c in all_comments}
        new_comments = [c for c in additional if c["id"] not in existing_ids]
        all_comments.extend(new_comments)
        print(f"  ➕ Additional: {len(new_comments)} new comments (total: {len(all_comments)})")
    
    # Also try fetching with different sort orders for more coverage
    for sort_order in ["top", "controversial"]:
        print(f"  🔄 Fetching with sort={sort_order}...")
        data = fetch_thread_json(thread_id, limit=500, sort=sort_order)
        if data and len(data) > 1:
            sort_comments = []
            sort_more = []
            extract_comments_recursive(data[1], sort_comments, sort_more)
            
            existing_ids = {c["id"] for c in all_comments}
            new_comments = [c for c in sort_comments if c["id"] not in existing_ids]
            all_comments.extend(new_comments)
            print(f"    ➕ Added {len(new_comments)} new (total: {len(all_comments)})")
        
        time.sleep(REQUEST_DELAY)
    
    return {
        "thread": thread_info,
        "comments": all_comments,
        "scraped_at": datetime.now().isoformat(),
    }


def convert_to_posts_format(thread_data: dict) -> list:
    """Convert scraped comments to the same format as wsb_raw_posts.json."""
    posts = []
    thread_info = thread_data.get("thread", {})
    thread_title = thread_info.get("title", "Unknown Thread")
    
    for comment in thread_data.get("comments", []):
        created_utc = comment.get("created_utc", 0)
        created_dt = datetime.fromtimestamp(created_utc) if created_utc else datetime.now()
        
        posts.append({
            "id": f"t1_{comment['id']}",
            "title": f"[Comment] {thread_title[:50]}...",
            "content": comment["body"],
            "author": f"/u/{comment['author']}",
            "score": comment.get("score", 0),
            "num_comments": 0,
            "created_utc": created_utc,
            "url": f"https://www.reddit.com{comment.get('permalink', '')}",
            "flair": "comment",
            "source": "thread_scraper",
            "created_datetime": created_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "full_text": comment["body"],
            "thread_id": thread_info.get("id", ""),
            "thread_title": thread_title,
        })
    
    return posts


def merge_with_existing(new_posts: list, existing_file: str) -> dict:
    """Merge new posts with existing wsb_raw_posts.json."""
    existing_data = {"posts": []}
    
    if os.path.exists(existing_file):
        try:
            with open(existing_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load existing file: {e}")
    
    existing_posts = existing_data.get("posts", [])
    existing_ids = {p["id"] for p in existing_posts}
    
    # Add only new posts
    added = 0
    for post in new_posts:
        if post["id"] not in existing_ids:
            existing_posts.append(post)
            existing_ids.add(post["id"])
            added += 1
    
    # Sort by created_utc descending
    existing_posts.sort(key=lambda x: x.get("created_utc", 0), reverse=True)
    
    return {
        "collection_time": datetime.now().isoformat(),
        "source": "r/wallstreetbets",
        "total_posts": len(existing_posts),
        "posts": existing_posts,
    }, added


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape WSB mega-threads for comments")
    parser.add_argument("--threads", nargs="+", default=DEFAULT_THREADS,
                        help="Thread IDs to scrape (without t3_ prefix)")
    parser.add_argument("--max-batches", type=int, default=50,
                        help="Max batches of 'more' comments to fetch per thread")
    parser.add_argument("--output", default=None,
                        help="Output file (default: wsb_data/wsb_thread_comments.json)")
    parser.add_argument("--merge", action="store_true",
                        help="Merge with existing wsb_raw_posts.json")
    args = parser.parse_args()
    
    # Setup paths
    data_dir = Path(WSB_DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = args.output or str(data_dir / "wsb_thread_comments.json")
    raw_posts_file = str(data_dir / "wsb_raw_posts.json")
    
    print("=" * 60)
    print("🔍 WSB Thread Scraper")
    print("=" * 60)
    print(f"📂 Output: {output_file}")
    print(f"🧵 Threads: {args.threads}")
    
    all_scraped = []
    all_posts = []
    
    for thread_id in args.threads:
        thread_data = scrape_thread(thread_id, max_more_batches=args.max_batches)
        all_scraped.append(thread_data)
        
        posts = convert_to_posts_format(thread_data)
        all_posts.extend(posts)
        print(f"  📊 Converted {len(posts)} comments to posts format")
        
        time.sleep(REQUEST_DELAY)
    
    # Save raw scraped data
    print(f"\n💾 Saving {len(all_posts)} comments to {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "scraped_at": datetime.now().isoformat(),
            "threads": all_scraped,
            "total_comments": len(all_posts),
        }, f, indent=2, ensure_ascii=False)
    
    # Optionally merge with existing raw posts
    if args.merge:
        print(f"\n🔀 Merging with {raw_posts_file}...")
        merged_data, added = merge_with_existing(all_posts, raw_posts_file)
        
        merged_file = str(data_dir / "wsb_enriched_posts.json")
        with open(merged_file, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Merged! Added {added} new posts")
        print(f"📊 Total posts in enriched file: {merged_data['total_posts']}")
        print(f"💾 Saved to: {merged_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SCRAPING SUMMARY")
    print("=" * 60)
    for scraped in all_scraped:
        thread = scraped.get("thread", {})
        comments = scraped.get("comments", [])
        print(f"  • {thread.get('title', 'Unknown')[:50]}...")
        print(f"    └─ {len(comments)} comments extracted")
    print(f"\n🎯 Total comments: {len(all_posts)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
