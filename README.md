# 游戏折扣日报

独立 Telegram 项目，只做 Steam/Epic 限免。

## 目录

- `generate_game_deals_daily.py`：主脚本，生成日报并直发 Telegram
- `scripts/steam_free.py`：Steam 限免数据
- `scripts/epic_free.py`：Epic 限免数据
- `scripts/github_trending.py`：预留模块，后续独立拆分
- `config.ini`：私密配置，写入 `.gitignore`，不提交

## 本地运行

```bash
cp config.ini.example config.ini   # 填入 bot_token / chat_id
python3 generate_game_deals_daily.py
```

## 调度

使用系统 crontab，每天 12:00 执行 `game_deals_daily.sh`。

```bash
0 12 * * * cd /root/game_deals_daily && bash game_deals_daily.sh >> /root/game_deals_daily/cron.log 2>&1
```
