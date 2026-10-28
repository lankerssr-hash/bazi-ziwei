# -*- coding: utf-8 -*-
"""扫描版 PDF → 文字：渲染 + OCR，带断点续跑。

用法：
    python pdf2text.py <文件.pdf> [起始页] [结束页]

产出（放在 <项目目录>/ocr/<书名>/ 下）：
    pages.jsonl   一行一页，{page, text}，用于断点续跑
    全文.txt      全部文字，按页分隔
"""
import io
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
import json
import os
import sys
import time

import pymupdf as fitz
from rapidocr_onnxruntime import RapidOCR

OUT_ROOT = _os.path.join(HERE, "ocr")
ZOOM = 2.4          # 约 172 DPI，中文竖排也能认


def book_dir(pdf):
    name = os.path.splitext(os.path.basename(pdf))[0]
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, "_")
    d = os.path.join(OUT_ROOT, name)
    os.makedirs(d, exist_ok=True)
    return d


def load_done(jsonl):
    done = {}
    if os.path.exists(jsonl):
        with io.open(jsonl, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    o = json.loads(line)
                    done[o["page"]] = o["text"]
                except Exception:
                    pass
    return done


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print(__doc__)
        return
    pdf = sys.argv[1]
    if not os.path.exists(pdf):
        print("找不到:", pdf)
        return

    doc = fitz.open(pdf)
    n = doc.page_count
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end = int(sys.argv[3]) if len(sys.argv) > 3 else n

    d = book_dir(pdf)
    jsonl = os.path.join(d, "pages.jsonl")
    done = load_done(jsonl)
    print("书名: %s" % os.path.basename(pdf))
    print("页数: %d   已做: %d   本次: %d~%d" % (n, len(done), start, end))

    ocr = RapidOCR()
    mtx = fitz.Matrix(ZOOM, ZOOM)
    t0 = time.time()
    made = 0

    with io.open(jsonl, "a", encoding="utf-8") as fout:
        for p in range(start, min(end, n) + 1):
            if p in done:
                continue
            page = doc[p - 1]
            pix = page.get_pixmap(matrix=mtx)
            img = os.path.join(d, "_tmp.png")
            pix.save(img)
            try:
                res, _ = ocr(img)
                lines = [r[1] for r in res] if res else []
                text = "\n".join(lines)
            except Exception as e:
                text = ""
                print("  第 %d 页 OCR 失败: %s" % (p, e))
            fout.write(json.dumps({"page": p, "text": text},
                                  ensure_ascii=False) + "\n")
            fout.flush()
            made += 1
            if made % 10 == 0:
                sp = (time.time() - t0) / made
                left = (min(end, n) - p) * sp
                print("  已做 %d 页（本次 %d），%.2f 秒/页，预计还要 %.0f 分钟"
                      % (p, made, sp, left / 60))

    try:
        os.remove(os.path.join(d, "_tmp.png"))
    except Exception:
        pass

    # 合成全文
    done = load_done(jsonl)
    txt_path = os.path.join(d, "全文.txt")
    with io.open(txt_path, "w", encoding="utf-8") as f:
        for p in sorted(done):
            if done[p].strip():
                f.write("\n\n===== 第 %d 页 =====\n" % p)
                f.write(done[p])
    total = sum(len(v) for v in done.values())
    print()
    print("√ 完成：%d 页，共 %d 字" % (len(done), total))
    print("  全文: %s" % txt_path)


if __name__ == "__main__":
    main()
