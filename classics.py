# -*- coding: utf-8 -*-
"""经典文本层：从 ref/ 下的公版古籍取条文，供分析层引用并标注出处。

已收录：
· 子平真诠（原本 + 辑注）
· 三命通会 时柱断语（经 bazi-1 整理，键为「甲日甲子」这种日干+日支+时支）
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "ref")

_CACHE = {}


def _read(name):
    if name in _CACHE:
        return _CACHE[name]
    p = os.path.join(REF, name)
    try:
        with io.open(p, "r", encoding="utf-8", errors="ignore") as f:
            _CACHE[name] = f.read()
    except Exception:
        _CACHE[name] = ""
    return _CACHE[name]


# ---------------- 三命通会 时柱断语 ----------------
def load_shizhu():
    """把 ref/sizi.py 里的 summarys 读出来（不 import，避免执行副作用）"""
    if "shizhu" in _CACHE:
        return _CACHE["shizhu"]
    p = os.path.join(REF, "sizi.py")
    txt = ""
    try:
        with io.open(p, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()
    except Exception:
        _CACHE["shizhu"] = {}
        return {}

    # 简单解析： '甲日甲子': '''...''',
    out = {}
    for m in re.finditer(r"'([^']{2,12})'\s*:\s*'''(.*?)'''", txt, re.S):
        key, body = m.group(1), m.group(2)
        out[key] = body.strip()
    _CACHE["shizhu"] = out
    return out


def shizhu_duan(day_gan, day_zhi, hour_gan, hour_zhi):
    """查时柱断语。键是「X日YZ」，YZ = 时柱干支。"""
    d = load_shizhu()
    key = "%s日%s%s" % (day_gan, hour_gan, hour_zhi)
    if key in d:
        return key, d[key]
    return None, ""


# ---------------- 子平真诠 ----------------
def ziping_chapters():
    """返回 [(章节名, 正文), ...]"""
    if "zp" in _CACHE:
        return _CACHE["zp"]
    t = _read("books_zipingzhenquan.md")
    parts = re.split(r"^#{2,4}\s+(.+)$", t, flags=re.M)
    out = []
    if len(parts) >= 3:
        for i in range(1, len(parts), 2):
            title = parts[i].strip()
            body = parts[i + 1].strip()
            if title and body:
                out.append((title, body))
    _CACHE["zp"] = out
    return out


def ziping_find(keyword):
    """在子平真诠里找含关键词的段落"""
    res = []
    for title, body in ziping_chapters():
        for para in re.split(r"\n\s*\n", body):
            if keyword in para:
                res.append((title, para.strip()))
    return res


# ---------------- 渊海子平 ----------------
def yuanhai_chapters():
    if "yh" in _CACHE:
        return _CACHE["yh"]
    t = _read("books_yuanhaiziping.md")
    parts = re.split(r"^#{2,3}\s+(.+)$", t, flags=re.M)
    out = []
    if len(parts) >= 3:
        for i in range(1, len(parts), 2):
            title, body = parts[i].strip(), parts[i + 1].strip()
            if title and body and title != "前言":
                out.append((title, body))
    _CACHE["yh"] = out
    return out


def yuanhai_find(keyword):
    res = []
    for title, body in yuanhai_chapters():
        for para in body.split("\n"):
            if keyword in para:
                res.append(("渊海子平·" + title, para.strip()))
    return res


# ---------------- 滴天髓 ----------------
def dts_chapters():
    if "dts" in _CACHE:
        return _CACHE["dts"]
    t = _read("books_ditiansui.md")
    parts = re.split(r"^##\s+(.+)$", t, flags=re.M)
    out = []
    if len(parts) >= 3:
        for i in range(1, len(parts), 2):
            title, body = parts[i].strip(), parts[i+1].strip()
            if title and body:
                out.append((title, body))
    _CACHE["dts"] = out
    return out


def gan_lun(day_gan):
    """滴天髓·天干论里该日干那一段。

    用原书十干的【开篇定句】定位（这些句子是固定的，不会串）：
    甲木参天 / 乙木虽柔 / 丙火猛烈 / 丁火柔中 / 戊土固重
    己土卑湿 / 庚金带煞 / 辛金软弱 / 壬水汪洋 / 癸水至弱
    """
    OPENER = {
        "甲": ("甲木参天", 600), "乙": ("乙木虽柔", 600),
        "丙": ("丙火猛烈", 600), "丁": ("丁火柔中", 600),
        "戊": ("戊土固重", 600), "己": ("己土卑湿", 600),
        "庚": ("庚金带煞", 700), "辛": ("辛金软弱", 600),
        "壬": ("壬水汪洋", 600), "癸": ("癸水至弱", 600),
    }
    if day_gan not in OPENER:
        return "", ""
    opener, span = OPENER[day_gan]

    t = _read("books_ditiansui.md").replace("\n", "")
    i = t.find(opener)
    if i < 0:
        return opener, ""

    # 在下一个十干定句处截断
    OPENERS = {
        "甲": "甲木参天", "乙": "乙木虽柔", "丙": "丙火猛烈", "丁": "丁火柔中",
        "戊": "戊土固重", "己": "己土卑湿", "庚": "庚金带煞", "辛": "辛金软弱",
        "壬": "壬水汪洋", "癸": "癸水至弱",
    }
    body = t[i:i + span + 200]
    for g2, op2 in OPENERS.items():
        if g2 == day_gan:
            continue
        k = body.find(op2, len(opener) + 2)
        if k > 0:
            body = body[:k]
    # 截到「地支论」为止（癸水后面接的是它）
    kz = body.find("地支论")
    if kz > 0:
        body = body[:kz]

    body = re.sub(r"#{2,}\s*", "", body).strip()
    # 去掉末尾粘着的下一个干名（如「...纳水乙木」）
    for nm in ("甲木", "乙木", "丙火", "丁火", "戊土", "己土",
               "庚金", "辛金", "壬水", "癸水"):
        if body.endswith(nm):
            body = body[:-len(nm)].rstrip()
    return opener, body


# ---------------- 格局判定 ----------------
# 月令本气 → 十神 → 格名
GE_NAMES = {
    "正官": "正官格", "七杀": "七杀格", "正财": "正财格", "偏财": "偏财格",
    "正印": "正印格", "偏印": "偏印格", "食神": "食神格", "伤官": "伤官格",
    "比肩": "建禄格", "劫财": "月刃格",
}


def judge_ge(day_gan, month_zhi, cang_list, shishen_fn):
    """按子平真诠「月令取用」的路数判格。

    规则（简化但合乎子平）：
    · 月支本气透出天干 → 以透出者为格
    · 本气未透 → 以月令本气十神为格（不透也成立，只是「不清」）
    · 比肩当令 → 建禄格；劫财当令 → 月刃格
    """
    if not cang_list:
        return "未知", "月支无藏干"
    benqi = cang_list[0]
    ss = shishen_fn(day_gan, benqi)
    name = GE_NAMES.get(ss, ss + "格")
    return name, "月令%s，本气%s（十神：%s）" % (month_zhi, benqi, ss)


def ge_explain(ge_name, limit=2):
    """从子平真诠里找这个格的论述"""
    kw = ge_name.replace("格", "")
    hits = ziping_find(kw)
    out = []
    for title, para in hits[:limit]:
        out.append((title, para))
    return out


# ---------------- 全文检索 ----------------
def search_all(keyword, limit=20):
    """在全部经典里检索关键词，返回 [(来源, 片段)]"""
    res = []
    for title, body in ziping_chapters():
        for para in re.split(r"\n\s*\n", body):
            if keyword in para:
                res.append(("子平真诠·" + title, para.strip()[:300]))
                if len(res) >= limit:
                    return res
    for title, body in dts_chapters():
        for para in body.split("\n"):
            if keyword in para:
                res.append(("滴天髓·" + title, para.strip()[:300]))
                if len(res) >= limit:
                    return res
    for src, para in yuanhai_find(keyword):
        res.append((src, para[:300]))
        if len(res) >= limit:
            return res
    d = load_shizhu()
    for k, v in d.items():
        if keyword in v:
            res.append(("三命通会·%s" % k, v[:300]))
            if len(res) >= limit:
                return res
    return res


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    d = load_shizhu()
    print("时柱断语条数:", len(d))
    ch = ziping_chapters()
    print("子平真诠章节数:", len(ch))
    for t, _ in ch[:6]:
        print("  ·", t)
    print()
    k, v = shizhu_duan("庚", "辰", "辛", "巳")
    print("查 庚日辛巳:", k)
    print(v[:300])


def search_shizhu(day_gan, keyword=None, limit=5):
    """只在【本日干】的时柱断语里找"""
    d = load_shizhu()
    res = []
    prefix = day_gan + "日"
    for k, v in d.items():
        if not k.startswith(prefix):
            continue
        if keyword and keyword not in v:
            continue
        res.append((k, v))
        if len(res) >= limit:
            break
    return res
