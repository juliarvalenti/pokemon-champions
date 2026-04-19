#!/usr/bin/env python3
"""Fetch Pokemon Champions meta overview from Pikalytics AI endpoints."""

import json
import re
import sys
import urllib.request

URL = "https://pikalytics.com/ai/pokedex/championspreview"


def fetch_meta():
    req = urllib.request.Request(URL, headers={"User-Agent": "pokemon-champions-agent/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8")

    pokemon = []
    # Parse the markdown table: | Rank | Pokemon | Usage % | ...
    for line in text.splitlines():
        m = re.match(
            r"\|\s*(\d+)\s*\|\s*\*\*(.+?)\*\*\s*\|\s*([\d.]+)%",
            line,
        )
        if m:
            pokemon.append({
                "rank": int(m.group(1)),
                "name": m.group(2),
                "usage": float(m.group(3)),
            })

    return {"format": "championspreview", "pokemon": pokemon}


if __name__ == "__main__":
    try:
        data = fetch_meta()
        json.dump(data, sys.stdout, indent=2)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
