# 小红书采集部署 runbook

## A2（xiaohongshu-skills）部署步骤

仓库：`https://github.com/autoclaw-cc/xiaohongshu-skills`（MIT，Python + Chrome 扩展）

1. **克隆 + 装依赖**
   ```bash
   git clone --depth 1 https://github.com/autoclaw-cc/xiaohongshu-skills.git
   cd xiaohongshu-skills && uv sync
   ```

2. **装 Chrome 扩展（用户手动，无法代劳）**
   - `chrome://extensions/` → 开发者模式 → 加载已解压 → 选 `extension/` 目录
   - 扩展名 **XHS Bridge**，manifest v3，含 `debugger` 权限（这是风控暴露点）

3. **启动 bridge server（后台）**
   ```bash
   uv run python scripts/bridge_server.py   # 监听 ws://localhost:9333
   ```
   CLI 会自动拉起 server 和 Chrome，扩展会自动重连。

4. **登录**：`uv run python scripts/cli.py check-login` → 未登录则扫码。

5. **验证**：`uv run python scripts/cli.py search-feeds --keyword "露营"`

### 关键命令

| 命令 | 作用 |
|---|---|
| `check-login` | 检查登录态（`{"logged_in": true}`） |
| `search-feeds --keyword K --sort-by 最多点赞/最新` | 搜索（默认「综合」最安全） |
| `get-feed-detail --feed-id ID --xsec-token T` | 取详情（重灾区，每 3 篇 sleep） |
| `check-risk` | 风控诊断（验证码弹窗、API 500 伪装拦截） |

- 搜索返回结构：`{feeds:[{id, xsecToken, modelType, displayTitle, type, user, interactInfo, cover}], count}`。`id` + `xsecToken` 必须配对使用。
- 过滤非 note 类型（live_v2=直播、hot_query=话题）和标题不含核心词的内容。

## 风控触发后的 runbook

1. 立即停止一切自动化操作（不再跑任何 CLI 命令）。
2. 关 Chrome 重开，扩展自动重连。
3. 若弹验证码，**手动**滑一次通过（真人操作）。
4. `check-login` 确认登录态恢复。
5. 冷却几小时到一天，期间正常用手机 App 刷（降风险分）。
6. 连续 3 次触发 = 账号被标记，本轮收手。

## Agent-Reach + OpenCLI（方案 B，能力层）

仓库：`https://github.com/Panniantong/Agent-Reach`（MIT，Python），小红书首选后端 OpenCLI。

1. **装 agent-reach**（无 pipx 用 uv）：
   ```bash
   uv tool install "https://github.com/Panniantong/agent-reach/archive/main.zip"
   agent-reach install --env=auto          # 只读检查
   agent-reach install --env=auto --system --channels=opencli,xiaohongshu
   ```
2. **OpenCLI 手动装**（agent-reach 内部 npm 超时，直接装反而快）：
   ```bash
   npm install -g @jackwener/opencli       # 需要 Node >= 20.18.1
   ```
3. **装 Chrome 扩展**：Chrome Web Store 搜「OpenCLI」或 GitHub releases + load unpacked。扩展叫 Browser Bridge，daemon 跑在 `localhost:19825`。
4. **验证**：`opencli doctor`（看 Extension: connected）→ `opencli xiaohongshu search "关键词" -f yaml`

### OpenCLI 与 A2 是同构架构
OpenCLI 也是「浏览器扩展 bridge + 本地 daemon + CDP」，和 A2 的 XHS Bridge 同类，只是更成熟（多平台、doctor 诊断、多后端路由）。换 OpenCLI 不是换架构，是换工具对比风控表现。

### OpenCLI 实测结果（2026-09）

- `opencli xiaohongshu feed`（读首页推荐）✅ 能出数据，格式干净：`id / title / author / likes / url`。
- `opencli xiaohongshu search "关键词"` ❌ 报 `filter layout did not match the expected visible panel (ambiguous_option)`——适配器与小红书当前搜索页 DOM 脱节（小红书改版、适配器未跟上，非配置问题）。
- `opencli xiaohongshu note <id>` ⚠️ 需要完整签名 URL（含 xsec_token），同 A2。
- **对比结论**：就「关键词搜索」核心需求，当前 xiaohongshu-skills 的 search 更可用；OpenCLI 优势在多平台统一（16 平台）+ creator 创作者中心数据（`creator-stats` / `creator-notes` / `creator-profile` 等 A2 没有的能力）。

### OpenCLI 扩展连接排障

装了 Browser Bridge 扩展但 `opencli doctor` 显示 `Extension: disconnected` 时：
- 最常见是 MV3 扩展的 service worker 休眠——先 `opencli daemon restart` 再 `opencli doctor`，通常能连上（扩展 v1.0.24）。
- 仍连不上：确认 `chrome://extensions` 里 Browser Bridge 已启用，点击扩展图标激活 SW。
- daemon 接口 `curl localhost:19825/status` 需要 `X-OpenCLI` header，直接用 `opencli daemon status` / `opencli doctor` 查，别裸 curl。

### OpenCLI 的 xiaohongshu 命令（比 A2 多 creator 系列）

`search`（搜索）、`feed`（首页推荐）、`note`（详情，需签名 URL）、`comments`（评论，支持楼中楼）、`user`（用户主页）、`whoami`（当前登录号）、`creator-stats` / `creator-notes` / `creator-note-detail` / `creator-profile`（创作者中心数据，A2 没有）。

## 每日采集 cron 脚本要点

- `collect_daily.sh`（放 `~/AppData/Local/hermes/scripts/`，cron 只传文件名）：
  - 路径一律 `C:/...`（python.exe 参数）；`UV`/`PY` 用绝对路径。
  - 循环关键词 → `search-feeds` 存 `.raw.json` → `filter.py` 过滤存 `.json` → 词间 `sleep 45`。
- `filter.py`：只留 `modelType==note` + 标题含核心主题词；stdout 出 JSON，stderr 出 `raw=N kept=N` 摘要（显示在 cron 日志）。
- `merge_daily.py`：读当天过滤后 `.json`，按 `id` 去重，按点赞降序输出文本（stdout 注入 LLM prompt）。
- 两个 cron：采集（no_agent 纯脚本）+ 分析（LLM agent，`script=merge_daily.py`，script 的 stdout 自动注入 prompt）。
- **cron 采集失败排查**：首跑 `last_status=error` + daily 目录空，最常见根因是 XHS Bridge 扩展未启用（手动 `check-login` 报「Extension 未连接」）。诊断 → 启用扩展 → 手动 `bash collect_daily.sh` 补跑。分析 cron 在采集失败时会照常跑出「今日无数据」简报（连锁，属正常）。

### 核心主题词锚点
用 `["一人公司", "opc", "超级个体", "一人企业"]` 做相关性锚点（不区分大小写），而不是用搜索词本身——宽泛词（创业/AI创业）搜出海量噪音，靠核心词锚定「真在讲一人公司/OPC」的内容。

### 废词修复：kept=0 时改成「核心词+该词」组合
首跑后逐词看 `filter.py` 的 `raw=N kept=N`。某词 kept=0（结果标题全不含核心词）说明它是废词——该词本身不锚定主题，如「coffee chat」单搜全是泛咖啡社交。修复 = 改成「核心词 + 该词」组合（「coffee chat」→「一人公司 coffee chat」，实测 kept 0→10）。
