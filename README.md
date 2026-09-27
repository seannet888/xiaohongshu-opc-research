# 小红书「一人公司 / OPC」采集与研究

小红书「一人公司 / OPC」主题的自动采集、语义分析、爆款拆解与 PDF 报告输出的一整套工作流。

## 内容

```
├── skills/                                  # 3 个 Hermes skill（迁移到 ~/AppData/Local/hermes/skills/）
│   ├── research/
│   │   ├── xiaohongshu-scraping/            # 采集、工具选型、风控规避
│   │   └── xiaohongshu-research/            # 采集→评估报告、爆款拆解方法论（含 scripts/）
│   └── productivity/
│       └── pandoc-pdf-generation/           # Markdown → 专业 PDF（Eisvogel + 中文）
└── migration.md                             # 迁移部署手册（新机器复现完整闭环）
```

## 采集链路（本仓库脚本实现）

```
每日采集（search-feeds，只搜索不取详情）
  → 规则过滤（filter.py：只留 note + 标题含核心主题词）
  → 合并去重（merge_daily.py，按点赞排序）
  → LLM 语义分析（过滤 + 分类 + 简报）
  → PDF 报告（generate_pdf.py，Eisvogel 中文）
```

## 当前采集配置（2026-09-26）

- 关键词 **10 个**：`opc` `一人公司` `超级个体` `创业` `AI创业` `一人公司创业` `自媒体创业` `一人公司 coffee chat` `opc社区` `opc园区`
- 排序：`--sort-by 最新`（日更趋势；综合排序按热度排、爆款几天不变、日报会重复）
- 风控：只搜索不取详情、词间 sleep 60s、每日 1 次、专用小号

## 快速开始

把 `skills/` 下的三个 skill 复制到目标机器的 `~/AppData/Local/hermes/skills/` 对应位置，然后照 `migration.md` 的 7 步执行（装采集后端 → PDF 工具链 → OCR → 改路径 → 建 cron → 验证）。

> 给其他 Hermes 用，直接说：「照这份 migration.md 迁移部署小红书采集研究环境」。
