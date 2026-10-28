# -*- coding: utf-8 -*-
"""紫微斗数模块：用 izthon 排盘，整理成结构化数据。

对外接口：
    chart(solar_str, time_index, gender) -> dict
    time_index_of(hour) -> int
"""
import sys

import izthon
from izthon.astro.astro import by_solar


# 12 时辰：0=子(23-1) 1=丑 ... 详见 CHINESE_TIME
def time_index_of(hour: int, minute: int = 0) -> int:
    """把小时换成时辰索引。
    子时 23:00~00:59 → 0；丑时 01:00~02:59 → 1 …… 亥时 21:00~22:59 → 11
    """
    h = hour
    if h == 23 or h == 0:
        return 0
    return ((h + 1) // 2) % 12


PALACE_ORDER = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                "迁移", "仆役", "官禄", "田宅", "福德", "父母"]


def _star(s):
    return {
        "name": getattr(s, "name", ""),
        "brightness": getattr(s, "brightness", "") or "",
        "mutagen": getattr(s, "mutagen", "") or "",
        "type": getattr(s, "type", "") or "",
    }


def chart(solar_str: str, time_index: int, gender: str) -> dict:
    """排盘。solar_str 形如 '2002-03-17'。"""
    r = by_solar(solar_str, time_index, gender)

    out = {
        "solar_date": r.solar_date,
        "lunar_date": r.lunar_date,
        "chinese_date": r.chinese_date,
        "time": r.time,
        "time_range": r.time_range,
        "sign": r.sign,
        "zodiac": r.zodiac,
        "soul": r.soul,                      # 命主
        "body": r.body,                      # 身主
        "five_elements_class": r.five_elements_class,
        "soul_palace_branch": r.earthly_branch_of_soul_palace,
        "body_palace_branch": r.earthly_branch_of_body_palace,
        "gender": r.gender,
        "palaces": [],
    }

    for p in r.palaces:
        if getattr(p, "name", "") == "命宫":
            out["soul_palace_stem"] = getattr(p, "heavenly_stem", "")
        dec = getattr(p, "decadal", None)
        rng = getattr(dec, "range", None) if dec else None
        out["palaces"].append({
            "name": getattr(p, "name", ""),
            "stem": getattr(p, "heavenly_stem", ""),
            "branch": getattr(p, "earthly_branch", ""),
            "is_soul": bool(getattr(p, "is_soul_palace", False)),
            "is_body": bool(getattr(p, "is_body_palace", False)),
            "decadal": ("%s~%s" % (rng[0], rng[-1])) if rng else "",
            "major": [_star(s) for s in getattr(p, "major_stars", [])],
            "minor": [_star(s) for s in getattr(p, "minor_stars", [])],
            "adj": [_star(s) for s in getattr(p, "adjective_stars", [])],
            "boshi": getattr(p, "boshi_12", "") or "",
            "changsheng": getattr(p, "changsheng_12", "") or "",
            "ages": list(getattr(p, "ages", []) or []),
        })
    return out


def palace(c, name):
    for p in c["palaces"]:
        if p["name"] == name:
            return p
    return None


def brief(c) -> str:
    """一句话摘要，给 AI 用"""
    L = []
    L.append("命主%s　身主%s　五行局%s" % (c["soul"], c["body"], c["five_elements_class"]))
    L.append("命宫%s%s　身宫%s" % (c["soul_palace_stem"], c["soul_palace_branch"],
                                  c["body_palace_branch"]))
    return "　".join(L)


def full_text(c) -> str:
    """完整盘面文字，喂给 AI"""
    L = []
    L.append("【紫微斗数】")
    L.append("  公历 %s　农历 %s　四柱 %s　%s（%s）　%s　生肖%s" % (
        c["solar_date"], c["lunar_date"], c["chinese_date"],
        c["time"], c["time_range"], c["sign"], c["zodiac"]))
    L.append("  命主 %s　身主 %s　五行局 %s　命宫 %s%s　身宫 %s" % (
        c["soul"], c["body"], c["five_elements_class"],
        c["soul_palace_stem"], c["soul_palace_branch"], c["body_palace_branch"]))
    tot_adj = sum(len(p["adj"]) for p in c["palaces"])
    L.append("  杂曜共 %d 个" % tot_adj)
    L.append("")
    for p in c["palaces"]:
        tag = "（命宫）" if p["is_soul"] else ("（身宫）" if p["is_body"] else "")
        L.append("  %-3s %s%s%s  大限%s" % (
            p["name"], p["stem"], p["branch"], tag, p["decadal"] or "—"))

        def fmt(lst):
            o = []
            for s in lst:
                x = s["name"]
                if s["brightness"]:
                    x += "(" + s["brightness"] + ")"
                if s["mutagen"]:
                    x += "[" + s["mutagen"] + "]"
                o.append(x)
            return " ".join(o) if o else "—"

        L.append("       主星：%s" % fmt(p["major"]))
        L.append("       辅星：%s" % fmt(p["minor"]))
        if p["adj"]:
            L.append("       杂曜：%s" % fmt(p["adj"]))
        tw = []
        if p.get("changsheng"):
            tw.append("长生十二神：" + p["changsheng"])
        if p.get("boshi"):
            tw.append("博士十二神：" + p["boshi"])
        if tw:
            L.append("       " + "　".join(tw))
    return "\n".join(L)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    c = chart("2002-03-17", 8, "女")
    print(brief(c))
    print()
    print(full_text(c))
