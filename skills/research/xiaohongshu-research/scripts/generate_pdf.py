#!/usr/bin/env python3
"""生成专业 PDF：Pandoc + Eisvogel 模板，支持中文/英文。

中文文档自动使用微软雅黑（系统自带），通过 CJKmainfont 传给 xeCJK。
"""
import argparse
import subprocess
import sys
from pathlib import Path

THEMES = {
    'white-paper': '1e3a8a',  # Blue
    'marketing': '059669',    # Green
    'research': '7c3aed',     # Purple
    'technical': '374151',    # Gray
}

CJK_FONT = "Microsoft YaHei"


def generate_pdf(input_file, output_file=None, theme='white-paper', chinese=False,
                 toc=True, toc_depth=2, margin='2.5cm', fontsize='11pt', mobile=False):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: 输入文件 '{input_file}' 不存在", file=sys.stderr)
        return 1

    if output_file is None:
        output_file = str(input_path.with_suffix('.pdf')) if not mobile \
            else input_path.stem + '-mobile.pdf'

    if mobile:
        margin = '0.5in'
        fontsize = '10pt'

    cmd = [
        'pandoc', str(input_file), '-o', str(output_file),
        '--pdf-engine=xelatex',
        '--template', 'eisvogel',
        '-V', f'geometry:margin={margin}',
        '-V', f'fontsize={fontsize}',
        '-V', 'colorlinks=true',
        '-V', 'linkcolor=blue',
        '-V', 'urlcolor=blue',
        '-V', 'titlepage=true',
        '-V', f'titlepage-color={THEMES.get(theme, THEMES["white-paper"])}',
        '-V', 'titlepage-text-color=ffffff',
    ]

    if mobile:
        cmd.extend([
            '-V', 'geometry:paperwidth=6in',
            '-V', 'geometry:paperheight=9in',
            '-V', 'linestretch=1.2',
        ])

    if toc:
        cmd.extend(['--toc', f'--toc-depth={toc_depth}'])

    if chinese:
        cmd.extend([
            '-V', f'CJKmainfont={CJK_FONT}',
            '-V', f'CJKsansfont={CJK_FONT}',
            '-V', f'CJKmonofont={CJK_FONT}',
            '-V', f'mainfont={CJK_FONT}',
        ])

    print(f"生成 PDF: {output_file}")
    print(f"主题: {theme} ({THEMES.get(theme)})")
    print(f"中文: {'是 (微软雅黑)' if chinese else '否'}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ 生成失败：", file=sys.stderr)
            print(result.stderr[-2000:], file=sys.stderr)
            return 1
        print(f"✅ 成功：{output_file}")
        return 0
    except FileNotFoundError:
        print("Error: pandoc 未安装", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description='生成专业 PDF（Pandoc + Eisvogel，支持中文）')
    parser.add_argument('input', help='输入 markdown 文件')
    parser.add_argument('-o', '--output', help='输出 PDF 文件')
    parser.add_argument('-t', '--theme', choices=list(THEMES.keys()), default='white-paper')
    parser.add_argument('-c', '--chinese', action='store_true', help='使用中文字体（微软雅黑）')
    parser.add_argument('-m', '--mobile', action='store_true', help='手机布局（6x9in）')
    parser.add_argument('--no-toc', action='store_true', help='禁用目录')
    parser.add_argument('--toc-depth', type=int, default=2)
    parser.add_argument('--margin', default='2.5cm')
    parser.add_argument('--fontsize', default='11pt')

    args = parser.parse_args()
    return generate_pdf(
        input_file=args.input, output_file=args.output, theme=args.theme,
        chinese=args.chinese, toc=not args.no_toc, toc_depth=args.toc_depth,
        margin=args.margin, fontsize=args.fontsize, mobile=args.mobile,
    )


if __name__ == '__main__':
    sys.exit(main())
