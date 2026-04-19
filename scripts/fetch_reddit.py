#!/usr/bin/env python3
"""One-off Reddit search / top-posts fetcher using public .json endpoints.

Examples:
    python3 scripts/fetch_reddit.py PokemonChampions --top week
    python3 scripts/fetch_reddit.py PokemonChampions --search "rain team"
    python3 scripts/fetch_reddit.py stunfisk --search archaludon --limit 10
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

UA = "pokemon-champions-agent/1.0 (personal research, one-off)"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_url(sub, search, top, limit):
    sub = sub.lstrip("r/").lstrip("/")
    if search:
        q = urllib.parse.urlencode({
            "q": search,
            "restrict_sr": "1",
            "sort": "top",
            "t": top or "all",
            "limit": limit,
        })
        return f"https://www.reddit.com/r/{sub}/search.json?{q}"
    q = urllib.parse.urlencode({"t": top or "week", "limit": limit})
    return f"https://www.reddit.com/r/{sub}/top.json?{q}"


def simplify(data):
    posts = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        posts.append({
            "title": d.get("title"),
            "score": d.get("score"),
            "num_comments": d.get("num_comments"),
            "author": d.get("author"),
            "flair": d.get("link_flair_text"),
            "url": f"https://www.reddit.com{d.get('permalink', '')}",
            "created_utc": d.get("created_utc"),
            "selftext": (d.get("selftext") or "")[:500],
            "external_url": d.get("url_overridden_by_dest"),
        })
    return posts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("subreddit")
    ap.add_argument("--search", help="search query within the subreddit")
    ap.add_argument("--top", choices=["hour", "day", "week", "month", "year", "all"])
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()

    url = build_url(args.subreddit, args.search, args.top, args.limit)
    try:
        data = fetch(url)
        json.dump({"url": url, "posts": simplify(data)}, sys.stdout, indent=2)
    except Exception as e:
        print(json.dumps({"error": str(e), "url": url}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
