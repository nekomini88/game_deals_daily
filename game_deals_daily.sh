#!/bin/bash
# 游戏折扣日报自动生成发送脚本
set -euo pipefail

cd /root/game_deals_daily

today=$(date +%Y-%m-%d)
mkdir -p files/${today}

echo "🎮 开始生成 ${today} 游戏折扣日报..."

# Step 1: 生成日报文本
python3 generate_game_deals_daily.py
text_file="files/${today}/游戏折扣日报_${today}.txt"

echo "📺 发送 Telegram..."
/root/.local/bin/hermes send --to "telegram:-1004307078905" --file "$text_file" || echo "❌ Telegram 发送失败"

echo "🎉 游戏折扣日报发送完成！"
