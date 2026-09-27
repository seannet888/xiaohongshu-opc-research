#!/usr/bin/env python3
"""小红书采集结果的相关性规则过滤。

只保留 modelType == note（砍直播/热门话题/推广），
且标题含「核心主题词」的条目（滤掉顺带提到关键词、主题无关的内容）。

stdout: 过滤后的 JSON（脚本重定向到文件）
stderr: 简短摘要 raw=N kept=N（显示在 cron 日志）
"""
import json
import sys

# 核心主题词（相关性锚点，不区分大小写）
CORE_TERMS = ["一人公司", "opc", "超级个体", "一人企业", "自媒体创业"]


def hit_core(text: str) -> bool:
    t = (text or "").lower()
    return any(term.lower() in t for term in CORE_TERMS)


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: filter.py <input.json>"}, ensure_ascii=False))
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    feeds = data.get("feeds", [])
    raw_count = data.get("count", len(feeds))
    kept = [
        f for f in feeds
        if f.get("modelType") == "note" and hit_core(f.get("displayTitle"))
    ]
    print(json.dumps({
        "raw_count": raw_count,
        "kept_count": len(kept),
        "feeds": kept,
    }, ensure_ascii=False))
    print(f"raw={raw_count} kept={len(kept)}", file=sys.stderr)


if __name__ == "__main__":
    main()
