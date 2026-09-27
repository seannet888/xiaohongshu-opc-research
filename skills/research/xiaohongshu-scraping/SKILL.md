---
name: xiaohongshu-scraping
description: 小红书数据采集、工具选型与风控规避。当用户需要采集/搜索小红书笔记、生成内容评估报告、搭建每日采集任务、处理小红书风控或登录失效、或对比小红书采集工具（xiaohongshu-mcp / xiaohongshu-skills / Agent-Reach+OpenCLI）时触发。关键词：小红书、XHS、OPC、一人公司、采集、搜索、风控、验证码、评估报告。
---

# 小红书数据采集

## 头号风险：风控（先立这个认知）

小红书没有公开 API，所有采集都靠浏览器自动化，必然面对风控。风控是**行为评分累积制**——不是一次性封号，而是每次触发异常警告就涨风险分，反复触发会升级到限流/封号。

**实战踩坑总结（本 session 连续触发 3 次换来的）：**

- **搜索（search-feeds）比取详情（get-feed-detail）安全得多**。取详情会连续打开页面+加载评论，是最重灾区；搜索一次就返回列表。
- 连续访问 4~5 篇详情会触发扫码验证。取详情必须**每 3 篇 sleep 10-20s**。
- **连续 3 次触发风控警告 = 账号已被标记**，立即停止、冷却几小时，别再硬试。
- 风控触发后的应对 runbook：关 Chrome 重开 → 手动过验证码 → `check-login` 确认恢复。
- 长期策略：**只搜索不取详情 + 每日低频（1 次）+ 词间 sleep + 专用小号**。

## 模拟人类操作三层次（回答「能否更安全」）

- ① 直接 executeScript / debugger（A2 bridge 现状）— 最易检测
- ② CDP 输入轨迹拟人（真实鼠标贝塞尔曲线/加减速/点击前复核落点，A1 的 humanize）— 中
- ③ 系统级 PyAutoGUI 真实鼠标键盘 — 最安全但极脆弱（屏幕坐标 + OCR，窗口一动就废）

最优 = 有头浏览器（真实指纹）+ 输入轨迹拟人。但低频场景「只搜索 + 每日 1 次」已足够，不必上系统级模拟。

## CLI 约定

- exit code：0=成功、1=未登录、2=错误；输出 JSON（`ensure_ascii=False`）。
- 平台约束（发布场景才用到）：标题 ≤20 字（UTF-16）、正文 ≤1000 字；同一账号不允许多个网页端同时登录（会踢掉另一处）。

## 工具选型

| 方案 | 架构 | 优点 | 软肋 |
|---|---|---|---|
| xiaohongshu-mcp（A1） | Go + CDP + humanize 鼠标轨迹 | 拟人化程度高 | 默认无头浏览器，指纹暴露 |
| xiaohongshu-skills（A2） | Python + Chrome 扩展 bridge + debugger | 真实浏览器指纹干净 | debugger 权限 + 直接执行脚本，行为暴露 |
| Agent-Reach + OpenCLI | 能力层，OpenCLI 也是扩展 bridge | 多平台、成熟、doctor 诊断 | 本质仍是扩展 bridge，风控风险同类 |
| RednoteMCP（JonaFly） | Playwright + 硬编码选择器 | 简单直接 | 停更即失效（选择器脱节） |

**关键判断**：三者都逃不出「复用真实浏览器」大框架。真实浏览器只降**指纹**风险，不免疫**行为**检测。「模拟人类操作」分三层：① 直接执行脚本（最暴露）② CDP 输入轨迹拟人（humanize）③ 系统级输入 PyAutoGUI（最真实但极脆弱）。日常采集用「只搜索+低频」就够，不必上系统级模拟。

**OpenCLI 实测（2026-09，关键对比结论）**：Agent-Reach + OpenCLI 装好后，`opencli xiaohongshu feed`（读首页推荐）能出干净数据（直接 `id/title/author/likes/url`），但 `opencli xiaohongshu search`（关键词搜索）报 `filter layout did not match the expected visible panel (ambiguous_option)`——OpenCLI 适配器与小红书当前搜索页 DOM 脱节（小红书改版、适配器未跟上，非配置问题）。`note` 需要完整签名 URL（含 xsec_token，同 A2）。**结论：就「关键词搜索」这个核心需求，当前 xiaohongshu-skills 的 search 更可用；OpenCLI 的优势在多平台统一（16 平台）和 creator 创作者中心数据（creator-stats/creator-notes 等 A2 没有的能力）。** 换 OpenCLI 前先手动打开小红书搜索页确认是「适配器过时」还是「风控未解除」——两者症状相同，都表现为搜索页异常。

**RednoteMCP 实测（2026-09）**：JonaFly/RednoteMCP 停更 17 个月（最后提交 2025-04），其搜索用 `a[href*="/search_result/"]` 硬编码选择器找帖子，但小红书笔记链接现在是 `/explore/{id}`（实测数据证实），选择器匹配不到任何内容，搜索必返回空。**通用教训：判断一个采集方案还能不能用，先看最近 commit 时间 + 选择器是否硬编码**——停更方案在「平台改版快」的小红书上会确定性失效（静默返回空 / ambiguous / not-found 报错），不是偶发；读代码看选择器就能判断，不必装依赖跑一遍去验证。

## 每日采集的防风控架构

- 采集层：纯脚本（no_agent cron），只 `search-feeds` 不取详情，词间 sleep 45-60s。
- **排序选型（关键）**：默认「综合」按热度排，头部爆款几天不变 → 每日简报会反复重复同样几条爆款、「趋势观察」失效。做**每日监控/趋势**要改用 `--sort-by 最新`（按发布时间，日更新鲜内容；点赞整体偏低是正常的，新帖还没攒赞）；代价是更易触发验证码，词间 sleep 拉到 60s。折中：核心词保留综合做主流对照，其余切最新。
- 规则过滤层：只留 `modelType==note` + 标题含**核心主题词**（不是搜索词本身——宽泛词如「创业」搜出海量噪音，靠核心词锚定相关性）。
- 语义过滤层：LLM agent（cron 采集后 15 分钟跑），合并去重 + 语义相关性判断 + 分类 + 出简报。
- 数据落盘成时间序列（`日期__关键词.json`），供趋势对比。

**两条运维红线（详见 `references/cron-pipeline-ops.md`）：**
- **加关键词必须改两处**——`collect_daily.sh` 的 `KEYWORDS` 数组 + `filter.py` 的 `CORE_TERMS`。只改 KEYWORDS 不改 CORE_TERMS，新词结果会被规则层全过滤成 `kept=0`（静默白加，无报错）。
- **「简报没出」先查 agent.log**——分析 cron（no_agent=false + merge_daily.py）脚本 stdout 为空时，Hermes 会打 `script produced no output, skipping AI call` 并返回 `[SILENT]`，不报错不投递。`last_status=ok` 不代表 LLM 真跑了分析。

## Windows / git-bash 技术坑（都踩过）

- **Windows 的 python.exe 不认 MSYS `/c/...` 路径**——作为 python 参数必须用 `C:/...` 格式（bash 能识别两种，但传给 Windows 程序要用后者）。
- **fnm 管理 node 时，`npm install -g` 的全局 bin（`~/AppData/Roaming/npm`）不在 PATH**——用完整路径或 `export PATH`。
- 无 pipx 时用 `uv tool install <git-url>` 替代。
- **Hermes cron 的 `script` 参数要求脚本放在 `~/AppData/Local/hermes/scripts/`，只传文件名**（不是绝对路径）。
- cron `no_agent=true`：脚本 stdout 直接投递；空 stdout 静默；非零 exit 发错误告警。TUI 会话 cron 是 local-only，不推送。

## 领域知识

**OPC = One Person Company = 一人公司**（国家工商定义「一人有限责任公司」，上海是落地最活跃地区）。小红书和整个社会语境里「OPC」与「一人公司」是同一概念，搜索时不要当成噪音过滤掉。用户纠正过这一点——把「上海 OPC 线下沙龙」当不相关内容是错的。

## 支持文件

- `references/deployment.md` — A2（xiaohongshu-skills）与 Agent-Reach/OpenCLI 的具体部署命令、风控应对 runbook、可复用脚本要点。
- `references/cron-pipeline-ops.md` — 每日采集→分析 cron 的运维手册：脚本真实路径（含 xhs_report 旧草稿陷阱）、加关键词两处同步、静默失败排查（agent.log 关键行）、编辑时机。
