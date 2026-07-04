#!/usr/bin/env python3
"""Steam 限免检测 — 检查 Steam 当前免费/限时免费游戏"""
import json
import urllib.request
import sys

STEAM_URL = "https://store.steampowered.com/api/featuredcategories?cc=us&l=schinese"

def fetch_steam():
    """Fetch Steam featured categories"""
    try:
        req = urllib.request.Request(STEAM_URL, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: Steam API failed: {e}", file=sys.stderr)
        return {}


def get_free_games(data):
    """Extract free-to-play games from Steam data"""
    results = []
    seen = set()
    
    # Check various categories that may contain free games
    for key in ["items", "free_to_play"]:
        items = data.get(key, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            app_id = str(item.get("id", ""))
            if app_id in seen or not app_id:
                continue
            seen.add(app_id)
            final_price = item.get("final_price", -1)
            if final_price == 0:
                results.append({
                    "name": item.get("name", "Unknown"),
                    "id": app_id,
                    "url": f"https://store.steampowered.com/app/{app_id}",
                    "original_price": item.get("original_price", 0),
                    "final_price": 0,
                    "discount_percent": 100 if item.get("original_price", 0) > 0 else 0,
                    "platform": "Steam 🆓常驻免费"
                })
    
    return results


def get_limted_time_free(data):
    """Extract limited-time free games (100% discount on paid games)"""
    results = []
    seen = set()
    
    for key in ["specials"]:
        items = data.get(key, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            app_id = str(item.get("id", ""))
            if app_id in seen or not app_id:
                continue
            orig = item.get("original_price", 0) or 0
            final = item.get("final_price", 0) or 0
            disc = item.get("discount_percent", 0) or 0
            # 100% off = limited time free
            if (disc == 100) or (orig > 0 and final == 0):
                seen.add(app_id)
                results.append({
                    "name": item.get("name", "Unknown"),
                    "id": app_id,
                    "url": f"https://store.steampowered.com/app/{app_id}",
                    "original_price": orig,
                    "final_price": 0,
                    "discount_percent": 100,
                    "platform": "Steam ⚡限时免费"
                })
    
    return results


if __name__ == "__main__":
    data = fetch_steam()
    free = get_free_games(data)
    limited = get_limted_time_free(data)
    all_games = limited + free
    
    if not all_games:
        print("NO_FREE_GAMES")
    else:
        print(json.dumps(all_games, ensure_ascii=False, indent=2))
