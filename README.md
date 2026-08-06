# 🎮 游戏折扣日报 (game_deals_daily)

Steam / Epic 限免与免费游戏自动检测，每日生成中文日报并推送到 Telegram 频道。

> 数据真实性第一：所有内容来自官方 API 实时抓取，无任何硬编码/伪造数据；
> 源没有限免时就如实报告，绝不编造游戏或链接。

---

## 🏗 架构

```text
┌─────────────────────┐      ┌──────────────────────────────────────┐
│ Epic Games API      │      │ Steam API                            │
│ freeGamesPromotions │      │ featuredcategories                   │
└─────────┬───────────┘      └─────────────┬────────────────────────┘
          │                                │
          ▼                                ▼
   ┌───────────────────────────────────────────────┐
   │        generate_game_deals_daily.py           │
   │  fetch_epic() + fetch_steam()  (独立 try 容错) │
   │  → build_message() 组装中文日报               │
   └─────────────────────┬─────────────────────────┘
                         ▼
          files/YYYY-MM-DD/游戏折扣日报_YYYY-MM-DD.txt
                         │
                         ▼ (game_deals_daily.sh)
                 hermes send → TG 频道 -1004307078905
```

**容错设计**：Epic 与 Steam 各自独立 try/except——单源失败不影响另一源；
单源无数据时对应区块自动省略，不产生空行或假内容。

---

## 📁 文件结构

| 文件 | 职责 |
|------|------|
| `generate_game_deals_daily.py` | 主脚本：拉取双源 → 组装日报 → 保存文本（可选 TG 直发） |
| `scripts/steam_free.py` | Steam 检测：限时免费 + 常驻免费（含链接） |
| `scripts/epic_free.py` | Epic 检测：当前免费 + 即将免费（原价/截止时间/封面） |
| `scripts/github_trending.py` | 预留模块（未启用，独立拆分用） |
| `game_deals_daily.sh` | cron 入口：生成文本 → `hermes send` 推送 |
| `config.ini.example` | 配置模板（chat_id），复制为 `config.ini` 使用 |
| `config.ini` | 私密配置（gitignored，不提交） |

---

## 🚀 运行

```bash
# 完整流程：生成 + 推送
bash game_deals_daily.sh

# 仅生成文本（不推送）
python3 generate_game_deals_daily.py

# 单独调试数据源
python3 scripts/steam_free.py
python3 scripts/epic_free.py
```

首次配置：

```bash
cp config.ini.example config.ini   # 编辑 chat_id
```

---

## ⏰ 调度

系统 crontab，每天 **12:00** 执行：

```bash
0 12 * * * cd /root/game_deals_daily && bash game_deals_daily.sh >> /root/game_deals_daily/cron.log 2>&1
```

目标频道：`-1004307078905`（经 `hermes send` 推送）

---

## 📊 数据源对比

| 维度 | Epic Games | Steam |
|------|-----------|-------|
| API | `store-site-backend-static.ak.epicgames.com/freeGamesPromotions` | `store.steampowered.com/api/featuredcategories` |
| 数据 | 当前免费 + 即将免费（每周四 23:00 UTC 更新） | 限时免费 + 常驻免费 |
| 关键字段 | `discountPercentage==0` 判定免费 | `discount_expiration` 区分限时/常驻 |
| 链接 | `store.epicgames.com/zh-CN/p/{slug}` | `store.steampowered.com/app/{app_id}` |
| 原价 | `fmtPrice.originalPrice`（如 ¥56.00） | `original_price`（分） |
| 封面 | `keyImages` 中 Thumbnail/OfferImageTall | 未使用 |

---

## 📄 日报格式示例

```text
🎮 游戏折扣日报
📅 2026-08-06 08:00

🎁 Epic Games 当前免费
 ● OTXO
   ~~¥56.00~~ → 免费
   ⏰ 截止: 2026-08-06 15:00 UTC
   🔗 https://store.epicgames.com/zh-CN/p/otxo-396b8b

⏳ Epic 即将免费
 ● Beacon Pines
   🕐 开始: 2026-08-06 15:00 UTC

🆓 Steam 免费游戏 (常驻)
 ● The Syndicate: Classified Operations
   🔗 https://store.steampowered.com/app/4598120

💡 Epic 每周四 23:00 更新限免
💡 Steam 不定期限时免费，留意推送
```

---

## 🔧 Steam 修复记录（v0.1.1）

**问题**：`featuredcategories` API 顶层各分类是 `dict {id,name,items:[...]}` 结构。
旧代码用 `data.get("specials", [])` 拿到 dict 后按 list 处理 → 永远匹配不到任何游戏；
且顶层不存在 `items` 键 → `get_free_games()` 也恒空。
**结果**：Steam 免费游戏区块长期缺失，且原实现连链接都不打印。

**修复**：
1. 新增 `_iter_all_items()`：统一遍历顶层所有分类下的 `items`（兼容 dict/list 两种容器）
2. `get_free_games()`：`final_price==0` **且无 `discount_expiration`** = 常驻免费
3. `get_limted_time_free()`：`100% off` **且带 `discount_expiration`** = 限时免费（与常驻区分）
4. `build_message()`：Steam 免费/限时免费条目补 `🔗 链接` + `⏰ 截止` 时间

**验证**：修复后 Steam 常驻免费 12 条全部检测到并带可点击链接
（The Syndicate / 拆迁地球及爱情事故 / 神之一手 / 我不是魔王 等）；
当前 Steam 无 100% off 项目时限时免费如实为空（不伪造）。

---

## ⚠️ 已知限制

- Steam 限时免费**只在 Steam 官方有 100% off 活动时出现**；`featuredcategories` 的
  `specials` 平时是普通折扣，此时限时免费区块为空属正常现象
- Epic 截止时间为 UTC；如需本地时间可自行转换（+8h）
- 日报为纯文本格式（Telegram 友好），不支持富文本/图片
- `github_trending.py` 为预留模块，当前未接入日报

## 🔒 隐私

- `config.ini`（TG 频道配置）已写入 `.gitignore`，凭据不提交 GitHub
- `cron.log`、`files/`（每日产物）同样 gitignored

## 📌 开发注意

- Steam `discount_expiration` 是区分"限时免费"与"常驻免费"的**唯一可靠字段**
- Epic `discountType == "PERCENTAGE"` 且 `discountPercentage == 0` 才是免费
- 修改分类/判断逻辑后务必跑 `python3 scripts/steam_free.py` 实测真实数据
