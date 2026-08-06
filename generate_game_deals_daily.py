#!/usr/bin/env python3
"""
游戏折扣日报 — Steam/Epic 限免检测 + Telegram 推送
"""

import configparser
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from steam_free import fetch_steam, get_free_games, get_limted_time_free
from epic_free import fetch_epic, parse_epic_free


def _load_config():
    cfg_path = BASE_DIR / "config.ini"
    if not cfg_path.exists():
        raise RuntimeError("缺少 config.ini")
    cfg = configparser.ConfigParser()
    cfg.read(cfg_path, encoding="utf-8")
    tg = cfg["telegram"]
    return tg.get("bot_token", ""), tg.get("chat_id", "")


def _tg_send(token: str, chat_id: str, text: str) -> bool:
    import urllib.request

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("ok", False)
    except Exception as exc:
        print(f"TG send error: {exc}", file=sys.stderr)
        return False


def build_message(epic_games, steam_limited, steam_free):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = ["🎮 游戏折扣日报", f"📅 {now}", ""]

    has_content = False

    epic_current = [g for g in epic_games if "当前免费" in g.get("platform", "")]
    epic_upcoming = [g for g in epic_games if "即将免费" in g.get("platform", "")]

    if epic_current:
        has_content = True
        lines.append("🎁 Epic Games 当前免费")
        for g in epic_current:
            original = g.get("original_price")
            price_info = f"~~{original}~~ → 免费" if original and original != "免费" else "免费"
            lines.append(f" ● {g['name']}")
            lines.append(f"   {price_info}")
            if g.get("end_date"):
                lines.append(f"   ⏰ 截止: {g['end_date']} UTC")
            if g.get("url"):
                lines.append(f"   🔗 {g['url']}")
            lines.append("")

    if epic_upcoming:
        has_content = True
        lines.append("⏳ Epic 即将免费")
        for g in epic_upcoming:
            lines.append(f" ● {g['name']}")
            if g.get("start_date"):
                lines.append(f"   🕐 开始: {g['start_date']} UTC")
            lines.append("")

    if steam_limited:
        has_content = True
        lines.append("⚡ Steam 限时免费")
        for g in steam_limited[:5]:
            lines.append(f" ● {g['name']}")
            if g.get("url"):
                lines.append(f"   🔗 {g['url']}")
            if g.get("discount_expiration"):
                lines.append(f"   ⏰ 截止: {g['discount_expiration']}")
            lines.append("")

    if steam_free:
        has_content = True
        lines.append("🆓 Steam 免费游戏 (常驻)")
        for g in steam_free[:8]:
            lines.append(f" ● {g['name']}")
            if g.get("url"):
                lines.append(f"   🔗 {g['url']}")
        lines.append("")

    if not has_content:
        lines.append("📭 今日没有新的限免游戏")
        lines.append("")

    lines.append("💡 Epic 每周四 23:00 更新限免")
    lines.append("💡 Steam 不定期限时免费，留意推送")

    return "\n".join(lines)


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = BASE_DIR / "files" / today
    out_dir.mkdir(parents=True, exist_ok=True)

    epic_games = []
    steam_limited = []
    steam_free = []

    try:
        epic_data = fetch_epic()
        epic_games = parse_epic_free(epic_data)
    except Exception as exc:
        print(f"Epic error: {exc}", file=sys.stderr)

    try:
        steam_data = fetch_steam()
        steam_limited = get_limted_time_free(steam_data)
        steam_free = get_free_games(steam_data)
    except Exception as exc:
        print(f"Steam error: {exc}", file=sys.stderr)

    msg = build_message(epic_games, steam_limited, steam_free)

    text_path = out_dir / f"游戏折扣日报_{today}.txt"
    text_path.write_text(msg, encoding="utf-8")
    print(f"✅ 日报已生成: {text_path}")
    print(msg)


if __name__ == "__main__":
    main()
