# -*- coding: utf-8 -*-
"""把两本盲派书接进检索：按四柱干支找最相关的段落。

盲派书的写法是「某造：甲戌 己巳 癸巳 乙卯……断语」，
所以检索的核心是【四柱干支命中数】。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import classics as CL

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


def _md_files():
    d = os.path.join(HERE, "ref")
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in os.listdir(d)
            if f.startswith("books_ocr_") and f.endswith(".md")]


def chapters():
    """所有盲派书的章节 → [(来源, 标题, 正文)]"""
    if "mp" in CL._CACHE:
        return CL._CACHE["mp"]
    out = []
    for p in _md_files():
        src = os.path.basename(p).replace("books_ocr_", "").replace(".md", "")
        try:
            t = io.open(p, encoding="utf-8").read()
        except Exception:
            continue
        parts = re.split(r"^#{2,3}\s+(.+)$", t, flags=re.M)
        if len(parts) >= 3:
            for i in range(1, len(parts), 2):
                title, body = parts[i].strip(), parts[i + 1].strip()
                if body:
                    out.append((src, title, body))
        elif t.strip():
            out.append((src, "全文", t))
    CL._CACHE["mp"] = out
    return out


def _paras(body):
    """把正文切成段（按空行或每 300 字）"""
    ps = [x.strip() for x in re.split(r"\n\s*\n", body) if x.strip()]
    if len(ps) <= 1:
        # 没有空行就硬切
        ps = [body[i:i + 400] for i in range(0, len(body), 400)]
    return ps


def search_pillars(pillars, limit=4, min_hits=2):
    """pillars: ['甲戌','己巳','癸巳','乙卯'] 这种

    给每段打分：命中几个干支。命中 >= min_hits 才收。
    返回 [(来源, 标题, 片段, 命中数)]
    """
    want = [p for p in pillars if len(p) >= 2]
    if not want:
        return []
    # 工具性段落（纳音歌、速查表之类），命中再多也没用
    USELESS = ("纳音歌", "六十甲子", "速查", "口诀表", "目录", "序言")
    # 真案例的标志
    CASE_HINT = ("例1", "例2", "例3", "例一", "乾造", "坤造", "乾：", "坤：",
                 "乾，", "坤，", "岁运", "大运", "此造", "本造", "命主")

    hits = []
    for src, title, body in chapters():
        for para in _paras(body):
            if len(para) < 40:
                continue
            n = sum(1 for gz in want if gz in para)
            if n < min_hits:
                continue
            score = n * 2
            if any(k in para for k in CASE_HINT):
                score += 4
            if any(k in title for k in USELESS):
                score -= 20
            if any(k in para[:60] for k in USELESS):
                score -= 20
            # 只有干支堆砌没有断语的，降权
            if len(para) < 120:
                score -= 3
            hits.append((src, title, para, n, score))
    hits.sort(key=lambda x: (-x[4], -x[3], len(x[2])))

    # 重新打包成 4 元组
    hits = [(a, b, c, d) for a, b, c, d, _ in hits]
    hits2 = hits
    # 去重（相似片段只留一条）
    seen = set()
    out = []
    for src, title, para, n in hits2:
        key = para[:40]
        if key in seen:
            continue
        seen.add(key)
        out.append((src, title, para, n))
        if len(out) >= limit:
            break
    return out


def search_keyword(kw, limit=6):
    """按关键词搜盲派书"""
    out = []
    for src, title, body in chapters():
        for para in _paras(body):
            if kw in para and len(para) >= 30:
                out.append((src, title, para))
                if len(out) >= limit:
                    return out
    return out


def block_for_prompt(pillars, limit=3, maxchars=1600):
    """给 AI 用：把命中的盲派段落拼成一段文字

    优先用结构化案例库（cases_mangpai.jsonl，按干支 token 打分），
    没有库或查不到再退回按子串找。
    """
    hits = []
    try:
        import cases_mangpai as CM     # 延迟导入，避开循环
        for hit, rec in CM.query(pillars, limit=limit):
            hits.append((rec["book"][:28], rec["chapter"], rec["text"], hit))
    except Exception:
        hits = []

    if not hits:
        hits = search_pillars(pillars, limit=limit)
    if not hits:
        return ""
    L = [
        "================ 盲派案例材料 ================",
        "★ 下面是从两本盲派实战书里，按这个人的四柱检索出来的相近命例。",
        "★ 这些比古书具体得多，说的是「什么组合 → 出什么事」。",
        "★ 你必须做两件事：",
        "  ① 如果案例里的情况和这个命盘对得上，直接引用，并注明「盲派案例里」；",
        "  ② 如果对不上，也要说明「盲派案例里没有对应的」，不许装作没有这回事。",
        "★ 不许把它们当古书条文用，它们是别人的真实命例。",
        "",
        "【检索结果】",
    ]
    used = 0
    for src, title, para, n in hits:
        piece = para.strip()
        if used + len(piece) > maxchars:
            piece = piece[:maxchars - used]
        if not piece:
            break
        L.append("")
        L.append("▸ 出自《%s》· %s（命中 %d 个干支）" % (src, title, n))
        L.append(piece)
        used += len(piece)
        if used >= maxchars:
            break
    return "\n".join(L)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ch = chapters()
    print("盲派章节总数:", len(ch))
    from collections import Counter
    c = Counter(s for s, _, _ in ch)
    for k, v in c.items():
        print("  %-46s %d 节" % (k, v))
    print()
    # 用他的盘试
    print("=== 检索 壬午 癸卯 甲申 壬申 ===")
    r = search_pillars(["壬午", "癸卯", "甲申", "壬申"], limit=3)
    for src, title, para, n in r:
        print()
        print("▸ %s · %s （命中 %d）" % (src, title, n))
        print("  " + para[:200].replace("\n", " "))
    print()
    print("=== 关键词：化忌 ===")
    for src, title, para in search_keyword("做功", limit=2):
        print("▸ %s · %s" % (src, title))
        print("  " + para[:150].replace("\n", " "))
