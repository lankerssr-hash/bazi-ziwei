# -*- coding: utf-8 -*-
"""补跑 OCR 失败的空白页：先删掉空条目，再重跑，最后重建全文。

用法： python retry_empty.py
"""
import io
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
import json
import os
import sys

OCR_ROOT = _os.path.join(HERE, "ocr")


def prune(jl):
    """读 jsonl，去掉空文本条目，重写"""
    keep = []
    dropped = []
    if not os.path.exists(jl):
        return 0
    for line in io.open(jl, encoding="utf-8"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("text", "").strip():
            keep.append(o)
        else:
            dropped.append(o["page"])
    with io.open(jl, "w", encoding="utf-8") as f:
        for o in keep:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    return len(dropped)


def rebuild(jl, txt):
    pages = {}
    for line in io.open(jl, encoding="utf-8"):
        try:
            o = json.loads(line)
            pages[o["page"]] = o["text"]
        except Exception:
            pass
    out = []
    for p in sorted(pages):
        if pages[p].strip():
            out.append("\n\n===== 第 %d 页 =====\n" % p + pages[p])
    io.open(txt, "w", encoding="utf-8").write("".join(out))
    return len(pages), sum(len(v) for v in pages.values())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    books = [d for d in os.listdir(OCR_ROOT)
             if os.path.isdir(os.path.join(OCR_ROOT, d))]
    for b in books:
        jl = os.path.join(OCR_ROOT, b, "pages.jsonl")
        txt = os.path.join(OCR_ROOT, b, "全文.txt")
        n = prune(jl)
        print("  %s：删掉 %d 个空页" % (b, n))


if __name__ == "__main__":
    main()
