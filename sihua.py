# -*- coding: utf-8 -*-
"""四化飞星：十天干四化 + 各宫飞出/飞入。

术语：
  · 生年四化 —— 由出生年干决定的四颗星（禄权科忌），已经显示在星曜上
  · 宫干四化 —— 每个宫位有自己的天干，那个天干会让四颗星化禄/权/科/忌
    这四颗星落在哪一宫，就叫「飞入那一宫」
  · 自化 —— 本宫的宫干，化的是本宫自己坐的星，叫自化
"""
import sys
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))

# 十天干四化（通行版）
SIHUA = {
    "甲": {"禄": "廉贞", "权": "破军", "科": "武曲", "忌": "太阳"},
    "乙": {"禄": "天机", "权": "天梁", "科": "紫微", "忌": "太阴"},
    "丙": {"禄": "天同", "权": "天机", "科": "文昌", "忌": "廉贞"},
    "丁": {"禄": "太阴", "权": "天同", "科": "天机", "忌": "巨门"},
    "戊": {"禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"},
    "己": {"禄": "武曲", "权": "贪狼", "科": "天梁", "忌": "文曲"},
    "庚": {"禄": "太阳", "权": "武曲", "科": "太阴", "忌": "天同"},
    "辛": {"禄": "巨门", "权": "太阳", "科": "文曲", "忌": "文昌"},
    "壬": {"禄": "天梁", "权": "紫微", "科": "左辅", "忌": "武曲"},
    "癸": {"禄": "破军", "权": "巨门", "科": "太阴", "忌": "贪狼"},
}

MUTAGENS = ("禄", "权", "科", "忌")


def _star_home(c, star):
    """这颗星在哪一宫（只看主星+辅星，杂曜里也有但先不算）"""
    for p in c["palaces"]:
        for s in p["major"] + p["minor"]:
            if s["name"] == star:
                return p["name"]
    return None


def _stars_in(c, palace_name):
    for p in c["palaces"]:
        if p["name"] == palace_name:
            return [s["name"] for s in p["major"] + p["minor"]]
    return []


def feixing(c):
    """返回每一宫的飞出四化 + 飞入四化

    结构：
    {
      "宫名": {
         "stem": "乙",
         "飞出": [{"mutagen":"禄","star":"天机","to":"疾厄","self":False}, ...],
         "飞入": [{"mutagen":"禄","star":"太阴","from":"夫妻"}, ...],
         "自化": ["禄", ...]
      }
    }
    """
    out = {}
    # 先算每宫的飞出
    for p in c["palaces"]:
        stem = p["stem"]
        table = SIHUA.get(stem, {})
        flies = []
        for mg in MUTAGENS:
            star = table.get(mg)
            if not star:
                continue
            home = _star_home(c, star)
            flies.append({
                "mutagen": mg,
                "star": star,
                "to": home or "（不在盘上）",
                "self": home == p["name"],
            })
        out[p["name"]] = {"stem": stem, "飞出": flies, "飞入": [], "自化": []}

    # 再反推飞入
    for pname, d in out.items():
        for f in d["飞出"]:
            tgt = f["to"]
            if tgt in out:
                out[tgt]["飞入"].append({
                    "mutagen": f["mutagen"],
                    "star": f["star"],
                    "from": pname,
                })
            if f["self"]:
                d["自化"].append(f["mutagen"])
    return out


def text_of(c, fx=None):
    """四化飞星的文字版（给界面和 AI）"""
    fx = fx or feixing(c)
    L = ["【四化飞星】"]
    L.append("  说明：每个宫位有自己的天干，那个天干会让四颗星分别化禄、权、科、忌。")
    L.append("  这四颗星落在哪一宫，就代表这一宫的事「往那一宫飞」。")
    L.append("  自化 = 本宫的宫干，化的正好是本宫自己坐的星。")
    L.append("")
    for p in c["palaces"]:
        nm = p["name"]
        d = fx[nm]
        L.append("  %-3s（%s%s）" % (nm, d["stem"], p["branch"]))
        segs = []
        for f in d["飞出"]:
            seg = "%s化%s → %s" % (f["star"], f["mutagen"], f["to"])
            if f["self"]:
                seg += "（自化）"
            segs.append(seg)
        L.append("       飞出：" + "　".join(segs) if segs else "       飞出：—")
        if d["飞入"]:
            segs2 = ["%s（%s）化%s入本宫" % (x["from"], fx[x["from"]]["stem"], x["mutagen"])
                     for x in d["飞入"]]
            L.append("       飞入：" + "　".join(segs2))
        else:
            L.append("       飞入：没有别的宫飞进来")
    return "\n".join(L)


def one_palace_text(c, name, fx=None):
    """单宫的四化文字（给点宫弹窗用）"""
    fx = fx or feixing(c)
    if name not in fx:
        return ""
    d = fx[name]
    L = []
    L.append("本宫宫干 %s：%s" % (d["stem"], SIHUA.get(d["stem"], {})))
    for f in d["飞出"]:
        tag = "（自化）" if f["self"] else ""
        L.append("  %s化%s → %s%s" % (f["star"], f["mutagen"], f["to"], tag))
    if d["飞入"]:
        for x in d["飞入"]:
            L.append("  %s（%s）化%s飞入本宫" % (x["from"], fx[x["from"]]["stem"], x["mutagen"]))
    return "\n".join(L)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import ziwei_chart as ZC

    c = ZC.chart("2002-03-17", 8, "女")
    print(text_of(c))
