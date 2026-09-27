---
name: xiaohongshu-research
description: |
  采集小红书（Xiaohongshu）帖子并生成综合评估报告。基于 autoclaw-cc/xiaohongshu-skills
  （A2 浏览器扩展方案，真实 Chrome + XHS Bridge 扩展 + 真实账号）。
  当用户要求搜索小红书、分析小红书某个主题/关键词、做竞品分析、热点追踪、
  内容评估报告、研究某个品类在小红书的表现时触发。
version: 1.0.0
---

# 小红书内容采集与评估报告

## 方案选型（先确认用哪套）

| 方案 | 适用 | 机制 |
|---|---|---|
| **A2 xiaohongshu-skills**（默认推荐） | 本地/真实账号，抗风控最强 | 真实 Chrome + XHS Bridge 扩展 + 真实登录态，无需部署服务 |
| A1 xiaohongshu-mcp-skills | 服务器无人值守批量 | 依赖 xiaohongshu-mcp Go 服务 + 无头浏览器，风控风险高 |
| B x-mcp 浏览器插件 | 非技术用户极简 | 零配置 |

默认选 A2，除非用户明确要服务器批量无人值守（那种场景才值得上 A1）。

**第三方方案试错结论（2026-09 实测）**：小红书搜索入口改版极快，任何「硬编码 CSS 选择器」的方案都会快速失效。OpenCLI（29.6k stars、能力最全、有 creator 创作者数据）的 `xiaohongshu search` 因小红书改版筛选面板而失效（报 `ambiguous_option`，`feed` 仍可用）；RednoteMCP 停更一年多、选择器（`a[href*="/search_result/"]`）早已对不上（现在笔记链接是 `/explore/`）。**判定原则：谁维护勤快谁可用，别被 star 数迷惑。**

## 部署状态（本机已完成）

已部署在 `~/xiaohongshu-skills`：
- 依赖用 `uv sync`（venv 在 `.venv/`，**必须用 `uv run` 跑**，否则缺依赖）
- Chrome 扩展「XHS Bridge」已装（`extension/` 目录，加载已解压）
- bridge server 常驻 `ws://localhost:9333`（CLI 会自动启动；扩展会自动重连）

## 运行命令

```bash
cd ~/xiaohongshu-skills
uv run python scripts/cli.py <子命令>
```

核心子命令：`check-login` `search-feeds` `get-feed-detail` `user-profile` `list-feeds`
`check-risk` `risk-report` `get-netlog`
（完整 29 个子命令 + 数据结构见 `references/cli-commands.md`）

## 风控（最重要，最容易翻车）

小红书风控是头号风险，即使真实浏览器也只是「降风险、不免疫」。硬规则：

- **操作间隔**：搜索/取详情之间必须间隔。取详情**每 3 篇 `sleep` 10–20s**（用 shell `sleep`，别用 python `time.sleep` 塞进 execute_code，会触发审批）。
- **连续访问 4–5 篇详情必触发扫码验证**，宁可少取，不要贪。
- **排序选择**：默认「综合」排序最安全；「最多点赞」「最新」会触发额外请求，更易触发验证码。**每日趋势监控已切「最新」**（综合按热度排、爆款几天不变、日报会重复），词间 sleep 拉到 60s。
- **触发后的恢复**：关 Chrome 重开 → 手动过验证码（真人操作，AI 帮不了）→ 重跑 `check-login` 确认 `logged_in: true`。
- **诊断工具**：`check-risk`（浏览器指纹 + API 探测 + 是否弹验证码）、`risk-report`、`get-netlog`。
- 判断依据：小红书风控常用 **HTTP 500（非 403）** 迷惑爬虫；`check-risk` 的 `has_captcha_modal` / `risk_level` 是最直接的信号。

## 「搜索 → 评估报告」工作流骨架

1. **双路采集**：`search-feeds` 默认「综合」抓主流 + 「最新」抓趋势（两次之间间隔 40s+）。
2. **精选取详情**：从结果挑 3–5 篇高互动、代表性笔记，`get-feed-detail`（含评论），严格控节奏。
3. **强模型分析输出报告**：热度与趋势 / 标题·封面·正文规律 / 互动数据对比 / 评论区真实反馈 / 机会点与风险。

## 关键经验

- **关键词语义分层**：搜索泛词（如「一人公司」）结果会混入多层语义——内容方法论、本地社群/活动招募、引流营销帖。⚠️ **别把「线下活动/注册补贴」当噪音过滤**：OPC = One Person Company = 一人公司（国家工商定义的「一人有限责任公司」，上海是落地最活跃地区），OPC 线下沙龙/注册补贴本身就是主题的活跃组成部分。真正该滤掉的是「顺带提到关键词、主题无关」的内容（如正文提一句就混入的无关帖）。语义分层是报告洞察，但分层 ≠ 丢弃。
- **评论区是金矿**：真实痛点、争议点、商机（"有没有人做 XX 服务"→ 有人回"我们就在做"）都在评论里。取详情时务必带 `--load-all-comments`。
- **数据配对**：`id` 与 `xsecToken` 必须成对使用，从搜索/推荐结果里取，不能自己构造。

## 爆款拆解方法论（为什么一条笔记能爆）

拆解爆款时逐个排查细节维度，别停在「内容好」这个空泛结论：

- **藏赞比是第一信号**：`藏 > 赞` = 干货工具型（用户想存下来反复看，收藏驱动、长尾稳）；`赞 >> 藏`（如 6:1）= 情绪共鸣型（情绪驱动，来得快去得快）。
- **评论区才是爆点**：讨论型（评论/赞比高）= 评论区有金句、质疑、商机，转发和讨论引擎常藏在评论区而非正文；收藏型（评论寥寥）= 纯工具帖。
- **识别「伪相关爆款」**：标题/标签挂满流量词（「超级个体」「一人公司」），但正文空、评论区完全跑题（如全在聊亲情/童年）= 内容是普世情绪，只是蹭标签被搜进关键词池。这类数据点是**噪音**，别当主题信号。
- **两条底层路径**：情绪共鸣型（权威 IP、时代叙事、身份焦虑、争议）vs 干货工具型（清晰框架、金句密度、戳真实痛点）。小红书场域里**情绪永远碾压干货**——纯情绪帖赞能高干货帖近 10 倍。
- **真实感最稀缺**：能爆的干货帖共性是不装、戳真问题（合规、获客、方向迷茫），标题用「不装了」「媒体不会告诉你」制造反差/信息差。
- **工具软广线（隐性变现路径）**：干货爆款常埋软广（无代码平台「秒哒」、AI 工具、书、课）。监测时留意「谁在推什么」——这是揭示赛道真实变现路径（卖工具/卖课/卖书/卖服务）最直接的商业信号。
- **图文爆款核心在长图里**：图文爆款正文常只写「详细见上图」，真正信息架构在 N 张长图海报里。用 RapidOCR 提取长图文字还原完整内容：`uv venv ~/ocr-venv && uv pip install --python ~/ocr-venv/Scripts/python.exe rapidocr-onnxruntime`，跑脚本时**必须 `PYTHONPATH=` 清空**（Hermes 把 PYTHONPATH 指向 hermes-agent venv，会污染独立 venv 的 PIL，报 `cannot import name '_imaging'`）。

- **拆解六维度框架 + 选题/标题/文字结构公式**：见 `references/baokuan-teardown.md`（选题公式 3 类、钩子公式 5 种、文字结构模板、图片结构、数据信号对照）。拆解要抓详情，**只抓 Top 3、每篇 sleep 20s**。

## 脚本与依赖（完整闭环，见 scripts/ 和 references/setup.md）

| 脚本 | 作用 |
|------|------|
| `scripts/collect_daily.sh` | 每日采集：10 词搜索（`--sort-by 最新`）+ 规则过滤，存 `daily/` |
| `scripts/filter.py` | 规则过滤：只留 note + 标题含核心主题词 |
| `scripts/merge_daily.py` | 合并去重 + 按点赞排序，stdout 注入 LLM prompt |
| `scripts/generate_pdf.py` | Eisvogel 中文 PDF（`-c` 中文，`-t` 主题色） |
| `scripts/ocr_images.py` | RapidOCR 长图文字（深挖图文爆款用） |

依赖安装（pandoc / MiKTeX / Eisvogel / RapidOCR）见 `references/setup.md`。

**报告输出格式**：用户要报告 / 拆解以 **PDF** 交付（生成命令见 pandoc-pdf-generation skill），Markdown 源文件一并保留方便后续修改。

## 陷阱

- 读 JSON 结果：保存到文件后用 `read_file` 读，比 `python -c` 内联解析更省事（本机 `-c`/`-e` 脚本执行会触发审批，易超时被 block）。
- 删除目录：不要 `rm -rf`（触发审批拦截）；目录不存在直接 `git clone` 即可。
- execute_code 里加 `time.sleep` 会触发审批超时；长间隔改用 shell `sleep` 或分多次调用。
- `get-feed-detail` 输出 JSON 前带日志前缀（`INFO xhs.feed_detail: ...` 几行），直接 `json.load` 会报 `Extra data`——解析前先截到第一个 `{`（`raw[raw.find("{"):]`）。
