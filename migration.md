# 小红书 OPC 采集研究工作流 · 迁移部署手册

> 本手册用于在一台全新的 Hermes 机器上复现「小红书一人公司/OPC 采集 → 过滤 → 分析 → 报告 → 深挖」完整闭环。
> 给目标机器 Hermes 看时，直接说：「照这份手册迁移部署小红书采集研究环境」，它就能按步骤执行。

## 前置条件

- Windows 系统，Python ≥ 3.11，已装 `uv` 和 Chrome
- 一个小红书**专用小号**（脚本操作有封号风险，绝不用主账号）

## 总览：什么能迁移，什么要重装

| 类别 | 方式 |
|---|---|
| 3 个 skill 文件 | 直接复制 |
| xiaohongshu-skills 采集后端 | git clone + uv sync 重装 |
| Chrome 扩展 + 账号登录 | 手动重做 |
| pandoc / MiKTeX / Eisvogel | winget 重装 |
| RapidOCR（ocr-venv） | uv venv 重装 |
| 2 个 cron 任务 | 重建 |
| 脚本里的硬编码路径 | 改成新用户名 |

---

## 步骤 1：迁移 3 个 skill

把源机器的 skill 目录复制到目标机器同名位置（`~` = 新用户 home）：

```
~/AppData/Local/hermes/skills/
├── research/xiaohongshu-scraping/      （采集/选型/风控 umbrella）
├── research/xiaohongshu-research/      （分析/报告/深挖 umbrella，含 scripts/）
└── productivity/pandoc-pdf-generation/ （PDF 生成）
```

```bash
# 源机器打包
tar czf xhs-skills.tar.gz -C ~/AppData/Local/hermes/skills \
  research/xiaohongshu-scraping research/xiaohongshu-research productivity/pandoc-pdf-generation
# 目标机器解包
tar xzf xhs-skills.tar.gz -C ~/AppData/Local/hermes/skills/
```

> 迁移后需新开会话，skill 才会被加载。

---

## 步骤 2：装采集后端 xiaohongshu-skills

```bash
cd ~
git clone --depth 1 https://github.com/autoclaw-cc/xiaohongshu-skills.git
cd xiaohongshu-skills && uv sync
uv run python scripts/bridge_server.py    # 后台常驻，监听 ws://localhost:9333
```

**手动装 Chrome 扩展（Hermes 无法代劳，需用户操作）**：
`chrome://extensions/` → 开发者模式 → 加载已解压 → 选 `xiaohongshu-skills/extension/` → 确认「XHS Bridge」启用。

**登录 + 验证**：
```bash
uv run python scripts/cli.py check-login      # 期望 {"logged_in": true}
uv run python scripts/cli.py login            # 未登录则扫码（用专用小号）
uv run python scripts/cli.py search-feeds --keyword "一人公司" --sort-by 最新
```

---

## 步骤 3：装 PDF 工具链（pandoc + MiKTeX + Eisvogel）

```bash
# pandoc
winget install --id JohnMacFarlane.Pandoc
# LaTeX 引擎（几百 MB；xelatex 在 ~/AppData/Local/Programs/MiKTeX/miktex/bin/x64/）
winget install MiKTeX.MiKTeX --silent --accept-package-agreements --accept-source-agreements
```

开启 MiKTeX 自动装包 + 预装 Eisvogel 依赖（避免首次编译逐个弹窗）：

```bash
export PATH="$HOME/AppData/Local/Programs/MiKTeX/miktex/bin/x64:$PATH"
initexmf --set-config-value="[MPM]AutoInstall=1"
mpm --install=unicode-math --install=soul --install=adjustbox --install=background \
    --install=collectbox --install=csquotes --install=framed --install=fvextra \
    --install=mdframed --install=needspace --install=pagecolor --install=titling \
    --install=upquote --install=xurl --install=zref --install=draftwatermark
```

Eisvogel 模板（10 个文件）放到 `~/AppData/Roaming/pandoc/templates/`：
- 来源 `github.com/Wandmalfarbe/pandoc-latex-template` 的 `template-multi-file/` 目录
- 主文件 `eisvogel.latex` + 9 个 partial：`document-metadata.latex` `passoptions.latex` `fonts.latex` `font-settings.latex` `common.latex` `after-header-includes.latex` `hypersetup.latex` `eisvogel-added.latex` `eisvogel-title-page.latex`
- **坑**：GitHub raw/CDN 网络不稳，curl 直连 raw 常超时，改用 Hermes 的 web_extract 工具逐个抓取 raw 文件内容再 write_file 保存

---

## 步骤 4：装 OCR（RapidOCR，深挖爆款长图用）

```bash
cd ~ && uv venv ocr-venv
uv pip install --python ocr-venv/Scripts/python.exe rapidocr-onnxruntime
```

**关键坑**：跑 OCR 前必须 `PYTHONPATH=` 清空（Hermes 会把 PYTHONPATH 指向 hermes-agent venv，污染独立 venv 的 PIL，报 `cannot import name '_imaging'`）。

---

## 步骤 5：调整脚本里的硬编码路径（最容易漏）

迁移来的脚本里用户名是 `Administrator`，改成新机器实际用户名：

| 文件 | 要改 |
|---|---|
| `xiaohongshu-research/scripts/collect_daily.sh` | `UV`/`PY`/`XHS_DIR`/`OUT_DIR`/`FILTER` 里的 `C:/Users/Administrator/...` |
| `xiaohongshu-research/scripts/merge_daily.py` | `DAILY_DIR = "C:/Users/Administrator/xhs_report/daily"` |
| `xiaohongshu-research/scripts/ocr_images.py` | 读 `e3.json` 的路径（或改成 argv 传入） |

路径一律用 `C:/` 格式（Windows python.exe 不认 `/c/` MSYS 路径，会解析成 `C:\c\` 报错）。

---

## 步骤 6：重建 cron（2 个任务）

脚本先复制到 `~/AppData/Local/hermes/scripts/`：

```bash
cp ~/AppData/Local/hermes/skills/research/xiaohongshu-research/scripts/collect_daily.sh \
   ~/AppData/Local/hermes/scripts/
cp ~/AppData/Local/hermes/skills/research/xiaohongshu-research/scripts/merge_daily.py \
   ~/AppData/Local/hermes/scripts/
```

用 cronjob 工具建两个任务：

| 任务 | 时间 | 模式 | script |
|---|---|---|---|
| 采集 | `0 19 * * *` | no_agent 纯脚本 | `collect_daily.sh` |
| 分析简报 | `15 19 * * *` | LLM agent | `merge_daily.py` |

- cron 的 `script` 参数只传文件名（脚本已在 `~/AppData/Local/hermes/scripts/`）
- 采集任务 `no_agent=true`（省 token）；分析任务 prompt = 「语义过滤 + 分类（方法论/线下活动/案例/引流）+ 简报」
- TUI 下 cron 是 local-only；要推送设 `deliver` 指向飞书等 gateway

---

## 步骤 7：验证全链路

```bash
# 采集
bash ~/AppData/Local/hermes/scripts/collect_daily.sh
# 期望：10 词各输出 raw=N kept=N（最新排序），daily/ 出现 日期__词.json

# PDF
python ~/AppData/Local/hermes/skills/research/xiaohongshu-research/scripts/generate_pdf.py 测试.md -c
# 期望：退出码 0，生成中文 PDF（蓝色标题页）

# OCR
PYTHONPATH= ~/ocr-venv/Scripts/python.exe ~/AppData/Local/hermes/skills/research/xiaohongshu-research/scripts/ocr_images.py
```

---

## 坑速查

1. **硬编码路径**：用户名 `Administrator` 要全改（步骤 5）
2. **PYTHONPATH 污染**：独立 venv 跑脚本前必须清空
3. **Eisvogel 下载**：用 web_extract 通道，别 curl 直连 raw
4. **Chrome 扩展**：XHS Bridge 必须用户手动加载，CLI 不会自动装
5. **风控**：专用小号，只搜索不取详情，每天 1 次，词间 sleep 60s（`--sort-by 最新` 更易触发验证码），取详情每 3 篇 sleep 20s
6. **cron local-only**：TUI 下不推送，要推送设 deliver
7. **排序与关键词**：每日趋势用 `--sort-by 最新`（综合排序按热度排，爆款几天不变，日报会重复）；加新词必须同步改 `collect_daily.sh` 的 KEYWORDS 和 `filter.py` 的 CORE_TERMS（只改一处会被规则层过滤成 kept=0）
