# 游戏折扣日报 (game_deals_daily)

Steam / Epic 限免与免费游戏检测，每日定时生成中文日报并推送 Telegram 频道。

## 🏗 架构

```text
Epic API (store-site-backend-static) ─┐
                                      ├─► generate_game_deals_daily.py ──► files/YYYY-MM-DD/游戏折扣日报.txt ──► hermes send ──► TG 频道
Steam API (featuredcategories) ───────┘
```

## 📁 文件

| 文件 | 职责 |
|------|------|
| `generate_game_deals_daily.py` | 主脚本：拉取 Epic+Steam → 组装日报 → 保存文本 |
| `scripts/steam_free.py` | Steam 检测：限时免费（discount_expiration 判定）+ 常驻免费 |
| `scripts/epic_free.py` | Epic 检测：当前免费 + 即将免费（含原价/截止时间） |
| `scripts/github_trending.py` | 预留模块（未启用） |
| `game_deals_daily.sh` | cron 入口：生成 + hermes send 推送 |
| `config.ini(.example)` | 私密配置（gitignored） |

## 🚀 运行

```bash
bash game_deals_daily.sh        # 完整：生成 + 推送
python3 generate_game_deals_daily.py   # 仅生成文本
python3 scripts/steam_free.py   # 仅测 Steam
python3 scripts/epic_free.py    # 仅测 Epic
```

## ⏰ 调度

系统 crontab，每天 12:00：

```bash
0 12 * * * cd /root/game_deals_daily && bash game_deals_daily.sh >> /root/game_deals_daily/cron.log 2>&1
```

目标频道：`-1004307078905`（经 `hermes send`）

## 🔧 Steam 修复记录（v0.1.1）

**问题**：`featuredcategories` API 顶层各分类是 `dict {items:[...]}` 结构，旧代码用
`data.get("specials", [])` 拿到 dict 后按 list 处理 → 永远匹配不到任何游戏；
且 `items` 顶层键不存在，`get_free_games` 也恒空 → **Steam 免费游戏区块长期缺失**。

**修复**：
1. 新增 `_iter_all_items()` 统一遍历所有分类的 `items`
2. `get_free_games`：`final_price==0` 且无 `discount_expiration` = 常驻免费
3. `get_limted_time_free`：`100% off` 且**有 `discount_expiration`** = 限时免费（避免与常驻混淆）
4. `build_message`：Steam 免费/限时免费条目补上 `🔗 链接`（原来只有名字）
5. 限时免费补充 `⏰ 截止` 时间显示

**验证**：修复后 Steam 常驻免费 12 条全部带链接（The Syndicate / 拆迁地球 / 神之一手 等），
限时免费按真实数据判断（当前 Steam 无 100% off 项时如实为空，不伪造）。

## 📌 注意

- Steam `discount_expiration` 是区分"限时免费"与"常驻免费"的关键字段
- Epic 每周四 23:00 更新限免（UTC），日报中的截止时间为 UTC
- 无数据时不伪造：源无限免就输出"今日没有新的限免游戏"

## 🔒 隐私

`config.ini` 已 gitignored，不提交 GitHub。