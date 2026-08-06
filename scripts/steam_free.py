#!/usr/bin/env python3
"""Steam 限免/免费检测 — 检查 Steam 当前免费/限时免费游戏（含链接推送）"""
import json
import logging
import urllib.request
import sys

STEAM_URL = "https://store.steampowered.com/api/featuredcategories?cc=us&l=schinese"
logger = logging.getLogger(__name__)


def fetch_steam():
    """Fetch Steam featured categories (dict {key: {items:[...]}})."""
    try:
        req = urllib.request.Request(STEAM_URL, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error("Steam API failed: %s", e)
        return {}


def _iter_all_items(data):
    """统一遍历顶层所有分类下的 items 列表。
    featuredcategories 顶层各分类都是 {id,name,items:[...]} 结构（dict items 键）。
    """
    for k, v in data.items():
        if isinstance(v, dict) and isinstance(v.get("items"), list):
            for item in v["items"]:
                if isinstance(item, dict):
                    yield item
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    yield item


def get_free_games(data, limit=15):
    """常驻免费游戏（final_price==0 且 original_price 有真实值 且无折扣到期时间）。

    关键坑: featuredcategories 对 new_releases/coming_soon 未发售/刚发售新品
    返回占位价格 original_price=None, final_price=0 —— 这类"无价格信息"的游戏
    不是免费（实测多为 10-15% 折扣新品）。必须排除 original_price is None 的项。
    真免费游戏(CS2/Dota2 is_free=True)不在此 API 中, 无需担心漏掉。
    """
    results = []
    seen = set()
    for item in _iter_all_items(data):
        app_id = str(item.get("id", ""))
        if not app_id or app_id in seen:
            continue
        final = item.get("final_price", -1)
        orig = item.get("original_price")
        # 常驻免费: 0 元且无限时到期时间, 且原价字段有真实值(排除未定价占位)
        if final == 0 and orig is not None and not item.get("discount_expiration"):
            seen.add(app_id)
            results.append({
                "name": item.get("name", "Unknown"),
                "id": app_id,
                "url": f"https://store.steampowered.com/app/{app_id}",
                "original_price": orig,
                "final_price": 0,
                "discount_percent": 0,
                "platform": "Steam 🆓常驻免费",
            })
    return results[:limit]


def get_limted_time_free(data, limit=10):
    """限时免费游戏（discount_expiration 存在 即 100% off 且为限时）。
    这类游戏的 final_price 为 0，但有 discount_expiration 到期时间 → 限时免费。
    """
    results = []
    seen = set()
    for item in _iter_all_items(data):
        app_id = str(item.get("id", ""))
        if not app_id or app_id in seen:
            continue
        orig = item.get("original_price", 0) or 0
        final = item.get("final_price", 0) or 0
        disc = item.get("discount_percent", 0) or 0
        exp = item.get("discount_expiration") or ""
        # 限时免费: 100% off (final==0 & orig>0) 且存在到期时间（真限时而非常驻）
        is_limited = (disc == 100 or (orig > 0 and final == 0)) and bool(exp)
        if is_limited:
            seen.add(app_id)
            results.append({
                "name": item.get("name", "Unknown"),
                "id": app_id,
                "url": f"https://store.steampowered.com/app/{app_id}",
                "original_price": orig,
                "final_price": 0,
                "discount_percent": 100,
                "discount_expiration": exp,
                "platform": "Steam ⚡限时免费",
            })
    return results[:limit]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = fetch_steam()
    free = get_free_games(data)
    limited = get_limted_time_free(data)
    print("=== 限时免费 ===")
    for g in limited:
        print(f"  ⚡ {g['name']} | {g['url']} | 到期 {g['discount_expiration']}")
    print("=== 常驻免费 ===")
    for g in free:
        print(f"  🆓 {g['name']} | {g['url']}")
    if not free and not limited:
        print("NO_FREE_GAMES")