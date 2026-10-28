# -*- coding: utf-8 -*-
"""把 OCR 出来的 全文.txt 清洗、分章、入库。

用法：
    python ingest.py                 # 处理 ocr/ 下所有书
    python ingest.py <书名目录>       # 只处理一本
"""
import io
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
import os
import re
import sys

OCR_ROOT = _os.path.join(HERE, "ocr")
REF = _os.path.join(HERE, "ref")

天干 = "甲乙丙丁戊己庚辛壬癸"
地支 = "子丑寅卯辰巳午未申酉戌亥"

# OCR 常见混淆：只在天干位置修，避免误伤
FIX_RULES = [
    # 已 / 巳 当天干用 → 己
    (re.compile(r"已(?=[%s])" % 地支), "己"),
    (re.compile(r"巳(?=[%s][、，,\s]*(?:[%s]))" % (地支, 天干)), "己"),
    # 戌 ⇄ 戊
    (re.compile(r"戊(?=[%s])" % "戌"), "戊"),      # 保底不动
    (re.compile(r"戍"), "戌"),
    # 壬 / 王
    (re.compile(r"(?<=[、，,\s])王(?=[%s])" % 地支), "壬"),
    # 癸 / 葵
    (re.compile(r"葵(?=[%s])" % 地支), "癸"),
    # 未 / 末
    (re.compile(r"末(?=[、，,\s]*[%s])" % 天干), "未"),
]

# 章节标题候选
CH_PATTERNS = [
    re.compile(r"^第[一二三四五六七八九十百零〇\d]+[章讲节]\s*\S*"),
    re.compile(r"^[一二三四五六七八九十]+[、．.]\s*\S+"),
    re.compile(r"^【\S+】"),
]


def clean(text):
    t = text
    for pat, rep in FIX_RULES:
        t = pat.sub(rep, t)
    # 去掉每页重复的书眉/网址
    lines = []
    for ln in t.split("\n"):
        s = ln.strip()
        if not s:
            continue
        if re.match(r"^www\.", s, re.I):
            continue
        if re.match(r"^\d{1,3}$", s):        # 孤立页码
            continue
        lines.append(s)
    return "\n".join(lines)


def split_pages(raw):
    """按 ===== 第 N 页 ===== 切开"""
    parts = re.split(r"=====\s*第\s*(\d+)\s*页\s*=====", raw)
    pages = []
    if len(parts) >= 3:
        for i in range(1, len(parts), 2):
            pages.append((int(parts[i]), parts[i + 1]))
    else:
        pages.append((1, raw))
    return pages


def chapters(pages):
    """按标题行把页串成章节"""
    out = []
    cur_title = "开篇"
    cur = []

    def flush():
        if cur:
            body = "\n".join(cur).strip()
            if body:
                out.append((cur_title, body))

    for pno, text in pages:
        t = clean(text)
        for ln in t.split("\n"):
            s = ln.strip()
            is_head = any(p.match(s) for p in CH_PATTERNS) and len(s) <= 30
            if is_head:
                flush()
                cur_title = s
                cur = []
            else:
                cur.append(s)
    flush()
    return out


def ingest(book_dir):
    name = os.path.basename(book_dir)
    src = os.path.join(book_dir, "全文.txt")
    if not os.path.exists(src):
        print("  跳过（没有 全文.txt）:", name)
        return None

    raw = io.open(src, encoding="utf-8").read()
    pages = split_pages(raw)
    chs = chapters(pages)

    # 输出成 md
    lines = ["# " + name, "",
             "> 扫描件 OCR 自动生成，可能有识别错误。共 %d 页，切出 %d 节。"
             % (len(pages), len(chs)), ""]
    for title, body in chs:
        lines.append("## " + title)
        lines.append("")
        # 每 200 字断行
        for x in range(0, len(body), 200):
            lines.append(body[x:x + 200])
        lines.append("")

    dst = os.path.join(REF, "books_ocr_%s.md" % re.sub(r"\W+", "_", name)[:40])
    io.open(dst, "w", encoding="utf-8").write("\n".join(lines))

    total = sum(len(b) for _, b in chs)
    print("  √ %s" % name)
    print("     %d 页 → %d 节 → %d 字" % (len(pages), len(chs), total))
    print("     %s" % dst)
    return dst


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(REF, exist_ok=True)
    if len(sys.argv) > 1:
        dirs = [os.path.join(OCR_ROOT, sys.argv[1])]
    else:
        dirs = [os.path.join(OCR_ROOT, d) for d in os.listdir(OCR_ROOT)
                if os.path.isdir(os.path.join(OCR_ROOT, d))]
    for d in dirs:
        ingest(d)


if __name__ == "__main__":
    main()
