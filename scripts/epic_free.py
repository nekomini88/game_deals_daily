#!/usr/bin/env python3
"""Epic Games 限免检测 — 检查 Epic Games Store 当前/即将免费游戏"""
import json
import urllib.request
import sys
from datetime import datetime, timezone

EPIC_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=zh-CN&country=CN&allowCountries=CN"

def fetch_epic():
    """获取 Epic Games Store 当前免费游戏"""
    try:
        req = urllib.request.Request(EPIC_URL, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: Epic API failed: {e}", file=sys.stderr)
        return None


def parse_epic_free(data):
    """Parse Epic free games from API response"""
    if not data:
        return []
    
    results = []
    try:
        elements = data["data"]["Catalog"]["searchStore"]["elements"]
    except (KeyError, TypeError):
        print("WARNING: Epic API structure changed", file=sys.stderr)
        return []
    
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    for game in elements:
        title = game.get("title", "Unknown")
        promotions = game.get("promotions")
        if not promotions:
            continue
        
        current_promos = promotions.get("promotionalOffers", [])
        upcoming_promos = promotions.get("upcomingPromotionalOffers", [])
        
        is_currently_free = False
        is_upcoming = False
        start_date = ""
        end_date = ""

        # Check current promotions
        for promo_group in current_promos:
            offers = promo_group.get("promotionalOffers", [])
            for offer in offers:
                discount_type = offer.get("discountSetting", {}).get("discountType", "")
                discount_pct = offer.get("discountSetting", {}).get("discountPercentage", -1)
                start = offer.get("startDate", "")
                end = offer.get("endDate", "")
                
                if discount_type == "PERCENTAGE" and discount_pct == 0:
                    is_currently_free = True
                    start_date = start[:16].replace("T", " ") if start else ""
                    end_date = end[:16].replace("T", " ") if end else ""

        # Check upcoming promotions
        if not is_currently_free:
            for promo_group in upcoming_promos:
                offers = promo_group.get("promotionalOffers", [])
                for offer in offers:
                    discount_type = offer.get("discountSetting", {}).get("discountType", "")
                    discount_pct = offer.get("discountSetting", {}).get("discountPercentage", -1)
                    start = offer.get("startDate", "")
                    end = offer.get("endDate", "")
                    
                    if discount_type == "PERCENTAGE" and discount_pct == 0:
                        is_upcoming = True
                        start_date = start[:16].replace("T", " ") if start else ""
                        end_date = end[:16].replace("T", " ") if end else ""

        if is_currently_free or is_upcoming:
            # Price
            price = game.get("price", {})
            total_price = price.get("totalPrice", {}) if isinstance(price, dict) else {}
            fmt_price = total_price.get("fmtPrice", {}) if isinstance(total_price, dict) else {}
            original = fmt_price.get("originalPrice", "")
            
            # URL
            mappings = game.get("catalogNs", {}).get("mappings", []) if isinstance(game.get("catalogNs"), dict) else []
            page_slug = game.get("productSlug", "") or game.get("urlSlug", "")
            if mappings and isinstance(mappings, list) and len(mappings) > 0:
                page_slug = mappings[0].get("pageSlug", page_slug) if isinstance(mappings[0], dict) else page_slug
            
            url = f"https://store.epicgames.com/zh-CN/p/{page_slug}" if page_slug else ""
            
            # Image
            key_images = game.get("keyImages", [])
            image_url = ""
            for img in key_images:
                if isinstance(img, dict) and img.get("type") in ("Thumbnail", "OfferImageTall", "DieselStoreFrontWide"):
                    image_url = img.get("url", "")
                    break
            if not image_url and key_images and isinstance(key_images[0], dict):
                image_url = key_images[0].get("url", "")

            results.append({
                "name": title,
                "id": game.get("id", ""),
                "url": url,
                "original_price": original,
                "final_price": "免费",
                "start_date": start_date,
                "end_date": end_date,
                "image": image_url,
                "platform": "Epic 🎁当前免费" if is_currently_free else "Epic ⏳即将免费"
            })

    return results


if __name__ == "__main__":
    data = fetch_epic()
    games = parse_epic_free(data)
    if not games:
        print("NO_FREE_GAMES")
    else:
        print(json.dumps(games, ensure_ascii=False, indent=2))
