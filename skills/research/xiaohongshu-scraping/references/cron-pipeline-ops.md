# 每日采集→分析 cron 流水线运维手册

配合 SKILL.md「每日采集的防风控架构」一起看。记录两条 cron 的实操细节、文件落点、静默失败排查。

## 两条 cron 任务

| 任务 | 时间 | 模式 | script | 落点 |
|---|---|---|---|---|
| 小红书每日采集 | `0 19 * * *` | no_agent=true 纯脚本 | `collect_daily.sh` | `~/xhs_report/daily/日期__词.json` |
| 小红书每日分析简报 | `15 19 * * *` | no_agent=false LLM agent | `merge_daily.py` | 简报在 cron 会话里，deliver=local，**不落盘成文件** |

## 文件落点 & 脚本真实路径

- 数据：`~/xhs_report/daily/`，每个关键词两个文件：
  - `日期__词.raw.json` = 原始搜索
  - `日期__词.json` = 规则过滤后，结构 `{raw_count, kept_count, feeds[]}`（merge 只读这个）
- **cron 真正执行的脚本在 `~/AppData/Local/hermes/scripts/`**（不是 xhs_report 下）：
  - `~/AppData/Local/hermes/scripts/collect_daily.sh`
  - `~/AppData/Local/hermes/scripts/merge_daily.py`
  - 过滤脚本：`~/xhs_report/filter.py`
- ⚠️ `~/xhs_report/collect_daily.sh` 是**旧草稿**（只有「一人公司」一个词、无 raw/filter 步骤、sleep 60），别误改它。改关键词改 `~/AppData/Local/hermes/scripts/collect_daily.sh`。

## 加关键词必须改两处（否则静默 kept=0）

1. `collect_daily.sh` 的 `KEYWORDS=(...)` 数组
2. `filter.py` 的 `CORE_TERMS=[...]` 列表

规则过滤只保留「标题含 CORE_TERMS 中任一锚点词」的 note（`modelType==note` 且标题命中）。只加 KEYWORDS 不加 CORE_TERMS，新词搜到的笔记标题几乎不含原锚点词（一人公司/opc/超级个体/一人企业），会被全部过滤成 `kept=0` —— 白加、无报错、静默。反之，含锚点词的短语关键词（如「一人公司 coffee chat」）自带锚点词，无需额外加 CORE_TERMS。

## 编辑时机：改了当天不生效

`collect_daily.sh` 的 `KEYWORDS` 行在脚本启动时就被 bash 读定。19:00 采集启动后再改关键词，要等**次日 19:00** 才生效。当天想验证只能手动 `bash ~/AppData/Local/hermes/scripts/collect_daily.sh` 重跑（注意防风控，别一天跑两次）。

## 静默失败排查：「简报没出」

症状：采集成功（daily/ 有数据文件），但没收到简报。

1. 看 cron 状态 `~/AppData/Local/hermes/cron/jobs.json` 里分析任务的 `last_status`。**`ok` 不代表 LLM 分析真跑了**——它只是「任务没崩」。
2. 看日志 `~/AppData/Local/hermes/logs/agent.log`，搜分析任务 ID 或 `merge_daily`：
   - `script produced no output, skipping AI call` + `agent returned [SILENT]` = merge 脚本 stdout 为空，LLM 被跳过。**这是静默失败**：不报错、不投递，只表现为「没简报」。
3. 手动复现：`python ~/AppData/Local/hermes/scripts/merge_daily.py`
   - 手动正常输出「日期…合并去重后共 N 条」= 数据没问题，是 cron 子进程里脚本 stdout 为空（根因：一次瞬时空输出，已逐一排除编码/时区/.pyc 新鲜度/redact/CREATE_NO_WINDOW，未能复现，非脚本逻辑 bug）。
   - 手动也空 = 数据或脚本本身有问题（数据文件缺失 / 日期不匹配）。

关键认知：`no_agent=false` + script 的 cron，脚本 stdout 为空时 Hermes 会「跳过 AI 调用 + 返回 [SILENT]」，不报错。排查「简报没出」先看 agent.log 有没有上面两行，再手动跑 merge 脚本隔离「数据问题 vs 脚本执行问题」。

## 防御：让 merge 脚本「不可能静默空输出」

原理：只要脚本 stdout 非空，cron 就把内容注入 prompt 并照常跑 LLM；空输出才触发「跳过 AI」。所以「保证非空」=「保证分析永远执行」。给 `merge_daily.py` 加两处兜底：

```python
# 1) reconfigure 兜底（Windows 下 stdout 状态异常时 reconfigure 可能抛异常）
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 2) main() 顶层 try/except：任何异常都打印到 stdout（走 traceback），不静默
if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback
        print(f"merge_daily 执行异常: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        sys.stdout.flush()
```

## 并发编辑冲突

`collect_daily.sh` / `filter.py` 可能被并行会话改（patch 会提示 `modified by sibling subagent ... never read it`）。patch 前先 read_file 拿最新内容；patch 后再 read_file 确认没被 fuzzy match 顺手 revert 掉别人的改动（例如把并发会话刚改的「coffee chat」→「一人公司 coffee chat」还原回去）。
