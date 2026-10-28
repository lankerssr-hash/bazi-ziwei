# -*- coding: utf-8 -*-
"""调候 + 神煞 + 流年。

调候：ref/yue.py 的 months 字典，键为「日干+月支」（如 '庚巳'），
      内容出自《穷通宝鉴》（徐乐吾评注本）。
神煞：ref/datas.py 的各表。
流年：按干支 60 甲子推。
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "ref")

_CACHE = {}

# ---------------- 调候 ----------------
_STEM_CH = {"甲": "jia", "乙": "yi", "丙": "bing", "丁": "ding", "戊": "wu",
            "己": "ji", "庚": "geng", "辛": "xin", "壬": "ren", "癸": "gui"}


def load_tiaohou():
    """解析 yue.py 的 months 字典 → {('甲','寅'): 正文}"""
    if "th" in _CACHE:
        return _CACHE["th"]
    txt = ""
    try:
        with io.open(os.path.join(REF, "yue.py"), "r", encoding="utf-8",
                     errors="ignore") as f:
            txt = f.read()
    except Exception:
        _CACHE["th"] = {}
        return {}

    i = txt.find("months")
    if i < 0:
        _CACHE["th"] = {}
        return {}
    body = txt[i:]

    # 变量定义（供 f-string 展开用）
    vars_ = {}
    for m in re.finditer(r"^([a-z]+_\d+)\s*=\s*'''(.*?)'''", body, re.S | re.M):
        vars_[m.group(1)] = m.group(2).strip()
    for m in re.finditer(r"^([a-z]+\d+)\s*=\s*'''(.*?)'''", body, re.S | re.M):
        vars_.setdefault(m.group(1), m.group(2).strip())

    out = {}

    # 形式一：'甲子': f'''...'''
    re1 = re.compile(r"'([\u4e00-\u9fff]{2})'\s*:\s*f?" + "'''" + r"(.*?)" + "'''",
                     re.S)
    for m in re1.finditer(body):
        key, val = m.group(1), m.group(2)
        val = re.sub(r"\{([a-z]+_?\d+)\}",
                     lambda mm: vars_.get(mm.group(1), ""), val)
        out[key] = val.strip()

    # 形式二：'己子': ji10_12,   （裸变量，没有三引号）
    re2 = re.compile(r"'([\u4e00-\u9fff]{2})'\s*:\s*([a-z]+_?\d+)\s*,")
    for m in re2.finditer(body):
        key, vn = m.group(1), m.group(2)
        if key in out and len(out[key]) > 30:
            continue
        v = vars_.get(vn, "")
        if v:
            out[key] = re.sub(r"\{([a-z]+_?\d+)\}",
                              lambda mm: vars_.get(mm.group(1), ""), v).strip()

    # 丢掉空壳（变量未定义，展开后没有内容）
    out = {k: v for k, v in out.items()
           if len(re.sub(r"\W", "", v)) > 12}
    _CACHE["th"] = out
    return out


def tiaohou(day_gan, month_zhi):
    """返回 (键, 正文)"""
    d = load_tiaohou()
    key = day_gan + month_zhi
    return key, d.get(key, "")


# ---------------- 神煞 ----------------
def _py_dict(name, file="datas.py"):
    """从 datas.py 提取某个顶层 dict 字面量（支持 = 两边任意空白）"""
    if name in _CACHE:
        return _CACHE[name]
    try:
        with io.open(os.path.join(REF, file), "r", encoding="utf-8",
                     errors="ignore") as f:
            txt = f.read()
    except Exception:
        _CACHE[name] = {}
        return {}

    # 用 \b 和 \s* 精确定位，避免 tianyin 命中 tianyis
    m = re.search(r"^" + re.escape(name) + r"\s*=\s*\{", txt, re.M)
    if not m:
        _CACHE[name] = {}
        return {}
    start = m.end() - 1
    depth = 0
    j = start
    while j < len(txt):
        if txt[j] == "{":
            depth += 1
        elif txt[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    lit = txt[start:j + 1]
    lit = re.sub(r"#[^\n]*", "", lit)
    try:
        val = eval(lit, {"__builtins__": {}}, {})
        if isinstance(val, dict):
            _CACHE[name] = val
            return val
    except Exception:
        pass
    _CACHE[name] = {}
    return {}


def tianyi(gz_or_zhi):
    """天乙贵人：以日干查"""
    d = _py_dict("tianyis")
    for k, v in d.items():
        if gz_or_zhi in (k, str(k)):
            return v
    return None


# ---------------- 流年 ----------------
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


def ganzhi_of_year(year):
    """公元年 → 干支（年柱以立春换，这里给的是该公历年大部分时间的年柱）"""
    idx = (year - 4) % 60
    return GAN[idx % 10] + ZHI[idx % 12]


def liunian(start_year, count=10):
    """从 start_year 起连续 count 年的流年"""
    out = []
    for y in range(start_year, start_year + count):
        out.append((y, ganzhi_of_year(y)))
    return out


def shishen_of(day_gan, gz):
    """流年干支对日主的十神"""
    sys_path = os.path.dirname(os.path.abspath(__file__))
    import sys
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)
    from bazi import shishen
    return shishen(day_gan, gz[0])


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    d = load_tiaohou()
    print("调候条目数:", len(d))
    for k in ("甲寅", "庚巳", "丙子", "壬午"):
        v = d.get(k, "")
        print()
        print("=== %s ===" % k)
        print(v[:400] if v else "（无）")
    print()
    print("流年测试:", liunian(2026, 5))


# ---------------- 神煞计算 ----------------
SHENSHA_DEF = [
    ("天乙贵人", "tianyis", "日干"),
    ("玉堂贵人", "yutangs", "日干"),
    ("文昌", "wenxing", "日干"),
    ("天印", "tianyin", "日干"),
]


def shensha(day_gan, zhis):
    """按日干查各类贵人，看四柱地支里有没有。
    zhis: [(柱名, 地支), ...]
    返回 [(神煞名, 落在哪柱), ...]"""
    out = []
    for label, table, _by in SHENSHA_DEF:
        d = _py_dict(table)
        target = d.get(day_gan)
        if not target:
            continue
        for pos, z in zhis:
            if z == target:
                out.append((label, pos, target))
    # 禄：日干的临官位
    lu = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
          "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
    t = lu.get(day_gan)
    if t:
        for pos, z in zhis:
            if z == t:
                out.append(("禄", pos, t))
    return out


def nayin_of(gz):
    """纳音：60 甲子表（键是 ('甲','子') 这种元组）"""
    if len(gz) < 2:
        return ""
    d = _py_dict("nayins")
    v = d.get((gz[0], gz[1]))
    return v if isinstance(v, str) else ""


def rizhu_duan(day_gz):
    """日柱专论（60 条）"""
    d = _py_dict("rizhus")
    return d.get(day_gz, "") if isinstance(d, dict) else ""


def kongwang(day_gz):
    """旬空（空亡）"""
    if len(day_gz) < 2:
        return ()
    d = _py_dict("empties")
    return d.get((day_gz[0], day_gz[1]), ())
