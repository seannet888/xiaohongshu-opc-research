#!/usr/bin/env python3
"""合并当天采集数据：读 ~/xhs_report/daily/ 今天日期下的过滤后 .json，去重，输出文本摘要。

stdout 会被 cron 注入 LLM 的 prompt，作为分析上下文。
"""
import json
import os
import sys
from datetime import date

try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DAILY_DIR = "C:/Users/Administrator/xhs_report/daily"
MAX_SHOW = 150


def to_int(s) -> int:
    s = str(s or "").strip().replace(",", "")
    if not s:
        return 0
    try:
        if s.endswith("万"):
            return int(float(s[:-1]) * 10000)
        if s.endswith("w"):
            return int(float(s[:-1]) * 10000)
        return int(float(s))
    except Exception:
        return 0


def main() -> None:
    today = date.today().strftime("%Y-%m-%d")

    if not os.path.isdir(DAILY_DIR):
        print("今日无采集数据：采集目录不存在。")
        return

    files = sorted(
        f for f in os.listdir(DAILY_DIR)
        if f.startswith(today + "__") and f.endswith(".json")
        and not f.endswith(".raw.json")
    )
    if not files:
        print("今日无采集数据：可能采集任务尚未运行，或登录态失效导致未采集。")
        return

    seen = {}
    stats = []
    for fn in files:
        kw = fn[len(today) + 2:-5].replace("_", " ")
        try:
            with open(os.path.join(DAILY_DIR, fn), encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        feeds = data.get("feeds", [])
        stats.append((kw, data.get("raw_count", 0), data.get("kept_count", 0)))
        for fd in feeds:
            fid = fd.get("id")
            if not fid or fid in seen:
                continue
            ii = fd.get("interactInfo", {}) or {}
            seen[fid] = {
                "title": (fd.get("displayTitle") or "").strip(),
                "liked": to_int(ii.get("likedCount")),
                "collected": to_int(ii.get("collectedCount")),
                "comment": to_int(ii.get("commentCount")),
                "type": fd.get("type", ""),
                "author": (fd.get("user", {}) or {}).get("nickname", ""),
                "kw": kw,
            }

    items = sorted(seen.values(), key=lambda x: x["liked"], reverse=True)

    print(f"日期: {today}")
    print(f"采集关键词 {len(stats)} 个，合并去重后共 {len(items)} 条笔记。")
    print()
    for kw, raw, kept in stats:
        print(f"  [{kw}] 原始{raw} 保留{kept}")
    print()
    print("=" * 50)
    note = f"（共 {len(items)} 条，仅显示点赞前 {MAX_SHOW} 条）" if len(items) > MAX_SHOW else ""
    print(f"去重后笔记列表（按点赞降序）{note}：")
    print("=" * 50)
    for i, it in enumerate(items[:MAX_SHOW], 1):
        print(
            f"{i}. {it['title'][:60]} | 赞{it['liked']} 藏{it['collected']} "
            f"评{it['comment']} | {it['type']} | @{it['author']} | 来源[{it['kw']}]"
        )
    if len(items) > MAX_SHOW:
        print(f"...（其余 {len(items) - MAX_SHOW} 条未列出）")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # 兜底：任何异常都输出到 stdout，避免 cron 因空输出静默跳过 AI
        import traceback
        print(f"merge_daily 执行异常: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        sys.stdout.flush()
