# -*- coding: utf-8 -*-
"""PDF 读取工具：优先抽文字；扫描件自动渲染成图片，交给视觉读。

用法：
    python pdfread.py <文件.pdf>                # 自动：有文字就抽，没文字就渲染前几页
    python pdfread.py <文件.pdf> text           # 只抽文字
    python pdfread.py <文件.pdf> img 1 5        # 把第 1~5 页渲染成 PNG
    python pdfread.py <文件.pdf> info           # 只看信息（页数/是否扫描件）
"""
import io
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
import os
import sys

import pymupdf as fitz

OUT = _os.path.join(HERE, "pdf_out")


def info(path):
    doc = fitz.open(path)
    n = doc.page_count
    # 抽前 3 页看有多少字
    sample = ""
    for i in range(min(3, n)):
        sample += doc[i].get_text()
    chars = len(sample.strip())
    per_page = chars / max(1, min(3, n))
    kind = "有文字层（可直接抽）" if per_page > 100 else "扫描件（要渲染成图片）"
    print("文件: %s" % os.path.basename(path))
    print("  大小: %.2f MB" % (os.path.getsize(path) / 1024 / 1024))
    print("  页数: %d" % n)
    print("  前三页平均字数: %.0f" % per_page)
    print("  判定: %s" % kind)
    doc.close()
    return n, per_page


def get_text(path, start=1, end=None):
    doc = fitz.open(path)
    end = end or doc.page_count
    out = []
    for i in range(start - 1, min(end, doc.page_count)):
        t = doc[i].get_text()
        if t.strip():
            out.append("\n\n===== 第 %d 页 =====\n" % (i + 1) + t)
    doc.close()
    return "".join(out)


def render(path, start=1, end=None, zoom=2.0, prefix="p"):
    os.makedirs(OUT, exist_ok=True)
    doc = fitz.open(path)
    end = end or doc.page_count
    files = []
    mtx = fitz.Matrix(zoom, zoom)
    for i in range(start - 1, min(end, doc.page_count)):
        pix = doc[i].get_pixmap(matrix=mtx)
        f = os.path.join(OUT, "%s%04d.png" % (prefix, i + 1))
        pix.save(f)
        files.append(f)
    doc.close()
    return files


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print(__doc__)
        return
    path = sys.argv[1]
    if not os.path.exists(path):
        print("找不到文件:", path)
        return
    mode = sys.argv[2] if len(sys.argv) > 2 else "auto"

    if mode == "info":
        info(path)
        return

    if mode == "text":
        s, e = 1, None
        if len(sys.argv) > 4:
            s, e = int(sys.argv[3]), int(sys.argv[4])
        t = get_text(path, s, e)
        print("抽出 %d 字" % len(t))
        print(t[:3000])
        return

    if mode == "img":
        s = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        e = int(sys.argv[4]) if len(sys.argv) > 4 else s + 4
        files = render(path, s, e)
        print("渲染 %d 页：" % len(files))
        for f in files:
            print("  ", f)
        return

    # auto
    n, per_page = info(path)
    print()
    if per_page > 100:
        t = get_text(path)
        print("抽出 %d 字，前 1500 字：" % len(t))
        print(t[:1500])
    else:
        files = render(path, 1, min(5, n))
        print("扫描件，已渲染 %d 页：" % len(files))
        for f in files:
            print("  ", f)


if __name__ == "__main__":
    main()
