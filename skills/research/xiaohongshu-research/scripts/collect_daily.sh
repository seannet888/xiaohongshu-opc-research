#!/usr/bin/env bash
# 每日小红书采集：只搜索，不取详情（防风控）
# 数据落盘：.raw.json=原始结果，.json=规则过滤后（只留 note + 标题含核心主题词）
# 路径统一用 C:/ 格式（Windows 程序需要）
set -u

UV="C:/Users/Administrator/AppData/Local/hermes/bin/uv"
PY="C:/Users/Administrator/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
XHS_DIR="C:/Users/Administrator/xiaohongshu-skills"
OUT_DIR="C:/Users/Administrator/xhs_report/daily"
FILTER="C:/Users/Administrator/xhs_report/filter.py"
DATE="$(date +%F)"

# ===== 可配置：监测关键词（一行一个，可增删）=====
KEYWORDS=("opc" "一人公司" "超级个体" "创业" "AI创业" "一人公司创业" "自媒体创业" "一人公司 coffee chat" "opc社区" "opc园区")

mkdir -p "$OUT_DIR"
cd "$XHS_DIR" || { echo "❌ 找不到项目目录 $XHS_DIR"; exit 2; }

# 1) 登录态检查（失效则告警退出，避免静默失败）
LOGIN="$("$UV" run python scripts/cli.py check-login 2>/dev/null || true)"
if ! echo "$LOGIN" | grep -q '"logged_in": true'; then
  echo "⚠️ 小红书登录态失效，需手动重新扫码登录。"
  exit 2
fi

# 2) 逐词搜索 + 规则过滤（最新排序，只搜索不取详情；词间 sleep 60s——最新排序更易触发验证码，故拉长间隔）
for KW in "${KEYWORDS[@]}"; do
  SAFE="$(echo "$KW" | tr ' /' '__')"
  RAW="$OUT_DIR/${DATE}__${SAFE}.raw.json"
  OUT="$OUT_DIR/${DATE}__${SAFE}.json"
  "$UV" run python scripts/cli.py search-feeds --keyword "$KW" --sort-by 最新 2>/dev/null > "$RAW"
  echo -n "✅ [$KW] "
  "$PY" "$FILTER" "$RAW" > "$OUT"   # stderr 摘要(raw=N kept=N)直接显示在日志
  sleep 60
done
echo "DONE"
