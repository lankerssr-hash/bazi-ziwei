# -*- coding: utf-8 -*-
"""盲派命例结构化：从 OCR 全文里切出「一造一断」的案例，建成可检索的库。

注意 OCR 的现实：扫描件的四柱经常被读乱（「乙巳」读成「乙己」），
所以这里不硬拼四柱，而是抽【干支 token 集合】做检索，原文整段保留。

产出：<项目目录>/cases_mangpai.jsonl
每一行：{book, chapter, pillars:[...], raw, text, has_case}
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mangpai as MP

OUT = os.path.join(HERE, "cases_mangpai.jsonl")
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
CASE_MARK = ("例1", "例2", "例3", "例一", "例二", "例三",
             "乾", "坤", "此造", "本造", "命主", "原注", "邢老师", "夏老师")


def tokens(text):
    """从一段文字里抽所有「干+支」的合法柱（滑动窗口，去重保序）"""
    out = []
    seen = set()
    for i in range(len(text) - 1):
        a, b = text[i], text[i + 1]
        if a in GAN and b in ZHI:
            gz = a + b
            if gz not in seen:
                seen.add(gz)
                out.append(gz)
    return out


def split_cases(body):
    """把一章切成若干案例段落。

    切点：出现「例N」「乾，」「坤，」这类开头时断一刀。
    """
    # 先在「例1」「例2」前面插分隔
    t = re.sub(r"(?=例[0-9一二三四五六七八九十]+\s*[，,、])", "\n@@CASE@@", body)
    t = re.sub(r"(?=[乾坤]\s*[，,、])", "\n@@CASE@@", t)
    parts = [x.strip() for x in t.split("@@CASE@@") if x.strip()]
    # 太短的并进上一段
    merged = []
    for p in parts:
        if merged and len(p) < 30:
            merged[-1] += "\n" + p
        else:
            merged.append(p)
    return merged


def build():
    chs = MP.chapters()
    print("来源章节: %d" % len(chs))
    n_case = 0
    n_total = 0
    with io.open(OUT, "w", encoding="utf-8") as f:
        for book, title, body in chs:
            for para in split_cases(body):
                p = para.strip()
                if len(p) < 40:
                    continue
                tk = tokens(p)
                has = any(k in p for k in CASE_MARK)
                # 柱太多 = 工具表格（纳音歌、六十甲子表），不是命例
                is_table = len(tk) > 12 or "纳音" in p[:80] or "六十甲子" in p[:80]
                rec = {
                    "book": book,
                    "chapter": title,
                    "pillars": tk,
                    "raw": "",
                    "text": p,
                    "has_case": has and not is_table,
                    "is_table": is_table,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_total += 1
                if has and len(tk) >= 2:
                    n_case += 1
    print("写出 %d 段，其中像真案例的 %d 段" % (n_total, n_case))
    print("→ %s  (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1048576))
    return n_total, n_case


def load():
    if not os.path.exists(OUT):
        return []
    out = []
    for line in io.open(OUT, encoding="utf-8"):
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def query(pillars, limit=5, need=2):
    """按四柱找最接近的案例。pillars: ['壬午','癸卯','甲申','壬申']"""
    want = set(x for x in pillars if len(x) == 2)
    if not want:
        return []
    scored = []
    for r in load():
        if r.get("is_table"):
            continue
        # 柱太多的段落也不要（正常命例最多十来柱）
        if len(r.get("pillars") or []) > 14:
            continue
        have = set(r.get("pillars") or [])
        hit = len(want & have)
        if hit < need:
            continue
        score = hit * 10
        if r.get("has_case"):
            score += 5
        if len(r.get("text", "")) > 200:
            score += 2
        npil = len(r.get("pillars") or [])
        if 3 <= npil <= 8:
            score += 4          # 几柱 = 典型的一造
        elif npil > 10:
            score -= 6          # 柱太多，可能就是表
        scored.append((score, hit, r))
    scored.sort(key=lambda x: (-x[0], -len(x[2].get("text", ""))))
    # 去重（同 chapter + 前 30 字）
    seen = set()
    out = []
    for score, hit, r in scored:
        k = (r.get("chapter"), r.get("text", "")[:30])
        if k in seen:
            continue
        seen.add(k)
        out.append((hit, r))
        if len(out) >= limit:
            break
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1 and sys.argv[1] == "query":
        pil = sys.argv[2].split()
        for hit, r in query(pil, limit=3):
            print("=" * 62)
            print("命中 %d 个干支 ｜ %s · %s" % (hit, r["book"][:20], r["chapter"]))
            print("抽到的柱:", " ".join(r["pillars"][:12]))
            print("-" * 62)
            print(r["text"][:600])
            print()
    else:
        build()
