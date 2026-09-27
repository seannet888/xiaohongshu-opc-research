---
name: pandoc-pdf-generation
description: 用 Pandoc + Eisvogel 模板把 Markdown 转成专业排版 PDF，支持中文（微软雅黑/CJK）。覆盖 MiKTeX 安装、Eisvogel 多文件模板获取、中文字体配置。当用户要把报告/文档/白皮书转成美化 PDF 时触发。
---

# Pandoc + Eisvogel 生成 PDF

把 markdown 转成带标题页/目录/表格/引用块的专业 PDF，中文用微软雅黑。核心组件：pandoc + xelatex（MiKTeX）+ Eisvogel 模板。

## 依赖安装

- pandoc（通常已装，`pandoc --version` 确认）。
- LaTeX 引擎：`winget install MiKTeX.MiKTeX`（约几百 MB）。装完 xelatex 在 `~/AppData/Local/Programs/MiKTeX/miktex/bin/x64/`，**新装后需手动 `export PATH` 加这个目录**（当前 shell 的 PATH 是旧的）。
- 中文字体系统自带：微软雅黑（`Microsoft YaHei`）、宋体（`SimSun`）。

## Eisvogel 模板获取（关键难点）

Eisvogel（Wandmalfarbe/pandoc-latex-template）新版是**多文件版**：主文件 `eisvogel.latex` 用 `$xxx.latex()$` partial 引用约 9 个拆分文件（`common.latex`、`fonts.latex`、`font-settings.latex`、`eisvogel-title-page.latex`、`eisvogel-added.latex`、`hypersetup.latex`、`passoptions.latex`、`document-metadata.latex`、`after-header-includes.latex`）。**全部文件都要放到 pandoc 模板目录** `~/AppData/Roaming/pandoc/templates/`。

release 里有合并的单文件版，但 **GitHub release/raw 直连下载常因网络中断**（curl 超时）。可靠做法：用 `web_extract` 工具逐个抓 `raw.githubusercontent.com/.../template-multi-file/*.latex`（web_extract 走独立通道，curl 不通时它能通），再 write_file 落盘。文件名在主文件里看到 `$xxx.latex()$` 就是需要的 partial。

## 中文字体配置

Eisvogel 的 `font-settings.latex` 已内置 CJK 支持（xeCJK），只需传：
```
-V CJKmainfont="Microsoft YaHei" -V mainfont="Microsoft YaHei"
```
（可加 CJKsansfont/CJKmonofont）。指定 mainfont 后 Eisvogel 不会加载 sourcesans（避免缺包）。

## 生成命令

```bash
pandoc doc.md -o doc.pdf --pdf-engine=xelatex --template=eisvogel \
  -V CJKmainfont="Microsoft YaHei" -V mainfont="Microsoft YaHei"
```
markdown 顶部用 YAML frontmatter 控制标题页：
```yaml
---
title: "标题"
subtitle: "副标题"
author: "作者"
date: "2026-09-25"
titlepage: true
titlepage-color: "1e3a8a"      # 主题色：白皮书蓝1e3a8a / 营销绿059669 / 研究紫7c3aed / 技术灰374151
titlepage-text-color: "FFFFFF"
---
```

## MiKTeX 首次编译（会下载依赖包）

首次编译中文会缺 xecjk/fontspec/unicode-math 等包，逐个下载慢且可能弹安装框。处理：
1. 开自动安装：`initexmf --set-config-value="[MPM]AutoInstall=1"`。
2. 批量预装：`mpm --install=包名`（**遇到已装包会报 "already installed" 并停止**，用 shell 循环逐个装并忽略该报错）。
3. 弹「未能找到 xxx.sty」框时点「安装」即可（正常现象）。

## 陷阱

- **Windows git-bash：传给 python.exe 的路径参数必须用 `C:/...` 格式，不能用 `/c/...`**（后者被解析成 `C:\c\...`）。临时文件别用 `/tmp`，改用 `C:/` 绝对路径。
- `mpm --install` 批量装多个包时，第一个已装的包会中断后续；用循环包裹。
- 编译 warnings（"LaTeX release 2026/06/01 vs 2025-11-01"、"not checked for MiKTeX updates"）不影响结果，退出码 0 即可。
