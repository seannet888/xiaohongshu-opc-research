# 依赖安装与路径速查

## 一、PDF：pandoc + MiKTeX + Eisvogel（生成报告 PDF 用）

```bash
winget install --id JohnMacFarlane.Pandoc
winget install MiKTeX.MiKTeX --silent --accept-package-agreements --accept-source-agreements
# xelatex 在 ~/AppData/Local/Programs/MiKTeX/miktex/bin/x64/
```

Eisvogel 模板（多文件版）放到 `~/AppData/Roaming/pandoc/templates/`，共 10 个文件：主文件 `eisvogel.latex` + 9 个 partial（`document-metadata.latex`、`passoptions.latex`、`fonts.latex`、`font-settings.latex`、`common.latex`、`after-header-includes.latex`、`hypersetup.latex`、`eisvogel-added.latex`、`eisvogel-title-page.latex`）。来源 `github.com/Wandmalfarbe/pandoc-latex-template` 的 `template-multi-file/`。单文件版在 GitHub release 的 tar.gz（`Eisvogel-3.5.1.tar.gz`）。

坑：GitHub raw/CDN 网络不稳，curl 直连 raw 常超时；改用 Hermes 的 web 工具通道（web_extract）抓取 raw 文件。

依赖的 LaTeX 包预装（避免首次编译逐个弹窗）：

```bash
export PATH="$HOME/AppData/Local/Programs/MiKTeX/miktex/bin/x64:$PATH"
initexmf --set-config-value="[MPM]AutoInstall=1"
mpm --install=unicode-math --install=soul --install=adjustbox --install=background \
    --install=collectbox --install=csquotes --install=framed --install=fvextra \
    --install=mdframed --install=needspace --install=pagecolor --install=titling \
    --install=upquote --install=xurl --install=zref --install=draftwatermark
```

## 二、OCR：RapidOCR（深挖爆款长图用）

```bash
cd ~ && uv venv ocr-venv
uv pip install --python ocr-venv/Scripts/python.exe rapidocr-onnxruntime
# 运行前必须清空 PYTHONPATH（否则加载到 hermes-agent 的坏 PIL）
PYTHONPATH= ~/ocr-venv/Scripts/python.exe ocr_images.py
```

## 三、路径速查（当前环境）

| 项 | 路径 |
|----|------|
| xiaohongshu-skills | `C:/Users/Administrator/xiaohongshu-skills` |
| 采集数据 | `C:/Users/Administrator/xhs_report/daily/` |
| 报告输出 | `C:/Users/Administrator/xhs_report/` |
| xelatex | `~/AppData/Local/Programs/MiKTeX/miktex/bin/x64/` |
| ocr-venv | `~/ocr-venv/Scripts/python.exe` |
| pandoc 模板 | `~/AppData/Roaming/pandoc/templates/` |
