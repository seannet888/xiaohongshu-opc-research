import json, io, sys, urllib.request
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

# 读图片 URL
d = json.load(open('C:/Users/Administrator/xhs_report/e3.json', encoding='utf-8'))
imgs = d['note']['imageList']
print(f'共 {len(imgs)} 张图，开始 OCR...')

# 初始化 OCR 引擎（首次加载模型）
ocr = RapidOCR()

for i, im in enumerate(imgs[:20]):
    url = im['urlDefault']
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        data = urllib.request.urlopen(req, timeout=40).read()
        img = Image.open(io.BytesIO(data)).convert('RGB')
        result, _ = ocr(img)
        texts = [r[1] for r in result] if result else []
        print(f'\n===== 第{i+1}张 =====')
        print(' | '.join(texts))
        sys.stdout.flush()
    except Exception as e:
        print(f'\n===== 第{i+1}张 失败: {e} =====')
        sys.stdout.flush()
