# -*- coding: utf-8 -*-
"""八字合盘：两造对比。

看四层：
① 日干关系（五合 / 相冲 / 相生 / 同类 / 相克）
② 夫妻宫（日支）关系（六合 / 六冲 / 相害 / 相刑 / 无关）
③ 五行互补（一方缺的五行，对方有没有）
④ 用神互补（一方的喜用，是否落进对方的忌神）

另外统计：年支关系、地支全体合冲数、三合局。
"""
import sys

HERE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
sys.path.insert(0, HERE)

import bazi as BZ

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

TIANGAN_HE = {"甲己", "乙庚", "丙辛", "丁壬", "戊癸"}
TIANGAN_CHONG = {"甲庚", "乙辛", "丙壬", "丁癸"}

ZHI_HE = {"子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未"}
ZHI_CHONG = {"子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥"}
ZHI_HAI = {"子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌"}
ZHI_XING = {"寅巳", "巳申", "寅申", "丑戌", "戌未", "丑未", "子卯"}
SANHE = {"申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金"}

WX_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WX_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _pair(a, b, table):
    return (a + b) in table or (b + a) in table


def _rel_gan(g1, g2):
    """两个天干的关系"""
    if g1 == g2:
        return "同类", "两个都是%s，同类，理解为脾气相近、容易共鸣也容易互不相让。" % g1
    if _pair(g1, g2, TIANGAN_HE):
        return "天干五合", "%s%s相合，传统叫「夫妻之合」，是日干关系里最好的一种。" % (g1, g2)
    if _pair(g1, g2, TIANGAN_CHONG):
        return "天干相冲", "%s%s相冲，性子容易顶牛，说话方式容易互相硌。" % (g1, g2)
    w1, w2 = BZ.GAN_WUXING[g1], BZ.GAN_WUXING[g2]
    if WX_SHENG[w1] == w2:
        return "我生你", "%s（%s）生%s（%s），一方的付出能落到另一方身上。" % (g1, w1, g2, w2)
    if WX_SHENG[w2] == w1:
        return "你生我", "%s（%s）生%s（%s），反过来，是另一方在供养这段关系。" % (g2, w2, g1, w1)
    if WX_KE[w1] == w2:
        return "我克你", "%s（%s）克%s（%s），一方的控制欲容易压到另一方身上。" % (g1, w1, g2, w2)
    if WX_KE[w2] == w1:
        return "你克我", "%s（%s）克%s（%s），反过来，是另一方被压。" % (g2, w2, g1, w1)
    return "无直接关系", "两个天干没有直接的生克合冲。"


def _zhi_kinds(z1, z2):
    """一支对之间可能同时有多种关系，全部列出来"""
    k = []
    if _pair(z1, z2, ZHI_HE):
        k.append("合")
    if _pair(z1, z2, ZHI_CHONG):
        k.append("冲")
    if _pair(z1, z2, ZHI_HAI):
        k.append("害")
    if _pair(z1, z2, ZHI_XING):
        k.append("刑")
    return k


def _rel_zhi(z1, z2, label="日支"):
    if z1 == z2:
        return "同支（伏吟）", "两个人%s都是%s，叫伏吟，等于同一个问题会重复出现。" % (label, z1)

    k = _zhi_kinds(z1, z2)
    if not k:
        return "无关", "%s%s没有合冲害刑，属于中性。" % (z1, z2)

    # ★ 多重关系要说清，尤其「合中带刑」
    if len(k) == 1:
        t = k[0]
        m = {
            "合": ("六合", "%s%s六合，%s相合，是最直接的贴近感。" % (z1, z2, label)),
            "冲": ("六冲", "%s%s六冲，%s相冲，是摩擦最明显的一种。" % (z1, z2, label)),
            "害": ("相害", "%s%s相害，%s相害，属于暗里的消耗，不吵但会累。" % (z1, z2, label)),
            "刑": ("相刑", "%s%s相刑，%s相刑，容易在具体事情上互相磨。" % (z1, z2, label)),
        }
        return m[t]

    # 两种以上
    t = "合中带" + "".join(x for x in k if x != "合") if "合" in k else "带" + "".join(k)
    name_map = {"合": "合", "冲": "冲", "害": "害", "刑": "刑"}
    parts = []
    if "合" in k:
        parts.append("%s%s六合，是最直接的贴近感" % (z1, z2))
    if "刑" in k:
        parts.append("%s%s还相刑，靠近了就容易互相磨" % (z1, z2))
    if "冲" in k:
        parts.append("%s%s还相冲，摩擦会明显" % (z1, z2))
    if "害" in k:
        parts.append("%s%s还相害，是暗里的消耗" % (z1, z2))
    desc = "%s的关系是「%s」：%s。合中带刑这种结构，传统说法叫「越亲越磨」。" % (
        label, t, "；".join(parts))
    if "合" not in k:
        desc = "%s的关系是「%s」：%s。" % (label, t, "；".join(parts))
    return t, desc


def compute(b1, b2):
    """b1, b2 都是 bazi.Bazi 对象"""
    a1 = BZ.analyze(b1)
    a2 = BZ.analyze(b2)

    out = {
        "人一": "%s（%s）%s %s %s %s" % (
            b1.name, b1.gender, b1.year.text(), b1.month.text(),
            b1.day.text(), b1.hour.text()),
        "人二": "%s（%s）%s %s %s %s" % (
            b2.name, b2.gender, b2.year.text(), b2.month.text(),
            b2.day.text(), b2.hour.text()),
        "细节": [],
    }

    # ① 日干
    t1, d1 = _rel_gan(b1.day.gan, b2.day.gan)
    out["日干关系"] = t1
    out["细节"].append(("日干（两个人本命的底色）", t1, d1))

    # ② 夫妻宫
    t2, d2 = _rel_zhi(b1.day.zhi, b2.day.zhi, "夫妻宫")
    out["夫妻宫关系"] = t2
    out["细节"].append(("夫妻宫（日支）", t2, d2))

    # ③ 年支（生肖）
    t3, d3 = _rel_zhi(b1.year.zhi, b2.year.zhi, "年支")
    out["年支关系"] = t3
    out["细节"].append(("年支（生肖层面）", t3, d3))

    # ③b 年柱：天合地合 / 天克地冲
    g1, g2 = b1.year.gan, b2.year.gan
    z1y, z2y = b1.year.zhi, b2.year.zhi
    gan_he = _pair(g1, g2, TIANGAN_HE)
    gan_ke = (WX_KE.get(BZ.GAN_WUXING[g1]) == BZ.GAN_WUXING[g2] or
              WX_KE.get(BZ.GAN_WUXING[g2]) == BZ.GAN_WUXING[g1])
    zhi_he = _pair(z1y, z2y, ZHI_HE)
    zhi_chong = _pair(z1y, z2y, ZHI_CHONG)
    if gan_he and zhi_he:
        t, d = "天合地合", ("年柱%s%s与%s%s天合地合，传统叫「天地鸳鸯」，"
                          "是年柱关系里最好的。" % (g1, z1y, g2, z2y))
    elif gan_ke and zhi_chong:
        t, d = "天克地冲", ("年柱%s%s与%s%s天克地冲，传统认为这是年柱关系里最凶的一种。"
                          % (g1, z1y, g2, z2y))
    elif zhi_chong:
        t, d = "年支相冲", ("年柱%s%s与%s%s地冲，属相层面是犯冲的。" % (g1, z1y, g2, z2y))
    elif zhi_he:
        t, d = "年支相合", ("年柱%s%s与%s%s地合，属相层面是合的。" % (g1, z1y, g2, z2y))
    else:
        t, d = "无特殊", ("年柱%s%s与%s%s没有天合地合，也没有天克地冲。" % (g1, z1y, g2, z2y))
    out["年柱关系"] = t
    out["细节"].append(("年柱关系（天合地合 / 天克地冲）", t, d))

    # ③c 年柱纳音
    try:
        import tiaohou as TH
        n1 = TH.nayin_of(b1.year.text())
        n2 = TH.nayin_of(b2.year.text())
    except Exception:
        n1 = n2 = ""
    if n1 and n2:
        w1 = n1[-1] if n1[-1] in "金木水火土" else ""
        w2 = n2[-1] if n2[-1] in "金木水火土" else ""
        if w1 and w2:
            if w1 == w2:
                tt, dd = "纳音相同", ("两人年柱纳音都是%s，民间说法是「双%s夫妻」，"
                                    "同性相扶，属吉。" % (n1, w1))
            elif WX_SHENG[w1] == w2 or WX_SHENG[w2] == w1:
                tt, dd = "纳音相生", ("一人纳音%s、一人纳音%s，相生，属吉。" % (n1, n2))
            elif WX_KE[w1] == w2 or WX_KE[w2] == w1:
                tt, dd = "纳音相克", ("一人纳音%s、一人纳音%s，相克，民间认为不吉。" % (n1, n2))
            else:
                tt, dd = "纳音无关", "两人纳音%s与%s没有生克。" % (n1, n2)
            out["纳音"] = tt
            out["细节"].append(("年柱纳音", tt, dd))

    # ③d 阴阳
    YANG_GAN = "甲丙戊庚壬"
    y1 = g1 in YANG_GAN
    y2 = g2 in YANG_GAN
    if b1.gender == "男":
        duo = "男阳女阴" if (y1 and not y2) else ("男阴女阳" if (not y1 and y2) else
                                                  ("双阳" if (y1 and y2) else "双阴"))
    else:
        duo = "男阳女阴" if (y2 and not y1) else ("男阴女阳" if (not y2 and y1) else
                                                  ("双阳" if (y1 and y2) else "双阴"))
    dmap = {
        "男阳女阴": ("男阳女阴", "男的年干属阳、女的属阴，传统认为是顺的配合。"),
        "男阴女阳": ("男阴女阳", "男的属阴、女的属阳，传统认为女方偏要强，"
                              "★ 这是古代性别观，不是命理必然。"),
        "双阳": ("双阳", "两人年干都属阳，传统认为女方事业心强，"
                        "★ 同样是古代观念，看的时候打折。"),
        "双阴": ("双阴", "两人年干都属阴，传统没有特别的说法。"),
    }
    tt, dd = dmap[duo]
    out["阴阳"] = tt
    out["细节"].append(("阴阳配（年干）", tt, dd))

    # ④ 五行互补
    c1, c2 = a1["五行"], a2["五行"]
    lack1 = [k for k, v in c1.items() if v == 0]
    lack2 = [k for k, v in c2.items() if v == 0]
    fill1 = [k for k in lack1 if c2.get(k, 0) > 0]
    fill2 = [k for k in lack2 if c1.get(k, 0) > 0]
    out["五行互补"] = {
        "一方缺": lack1, "二方缺": lack2,
        "二方能补一方": fill1, "一方能补二方": fill2,
    }
    if fill1 or fill2:
        desc = []
        if fill1:
            desc.append("%s缺%s，%s有，能补上" % (b1.name, "、".join(fill1) or "无",
                                              b2.name))
        if fill2:
            desc.append("%s缺%s，%s有，能补上" % (b2.name, "、".join(fill2) or "无",
                                              b1.name))
        out["细节"].append(("五行互补", "有互补", "；".join(desc) + "。"))
    else:
        out["细节"].append(("五行互补", "互补不明显",
                            "双方缺的东西对方也没有，各缺各的。"))

    # ⑤ 用神互补（关键）
    xi1 = set(a1["喜神"])
    xi2 = set(a2["喜神"])
    ji1 = set(a1["忌神"])
    ji2 = set(a2["忌神"])
    conflict = []
    for x in xi1:
        if x in ji2:
            conflict.append("%s的喜用「%s」正好是%s的忌神" % (b1.name, x, b2.name))
    for x in xi2:
        if x in ji1:
            conflict.append("%s的喜用「%s」正好是%s的忌神" % (b2.name, x, b1.name))
    support = []
    for x in xi1 & xi2:
        support.append("双方都以「%s」为喜" % x)
    out["用神"] = {"冲突": conflict, "共喜": support,
                   "一人喜": a1["喜神"], "二人喜": a2["喜神"],
                   "一人忌": a1["忌神"], "二人忌": a2["忌神"]}
    if conflict:
        out["细节"].append(("用神互补（最关键的一层）", "有冲突",
                            "；".join(conflict) + "。这意味着一个人最需要的东西，"
                            "恰好是另一个人最怕的东西。"))
    elif support:
        out["细节"].append(("用神互补（最关键的一层）", "共喜",
                            "；".join(support) + "，方向一致，相处时不太会互相拖。"))
    else:
        out["细节"].append(("用神互补（最关键的一层）", "各走各的",
                            "喜用不重合也不冲突，互不干扰。"))

    # ⑤b 克夫 / 克妻
    def _ke_spouse(b, an):
        """女命看官星被伤，男命看财星被劫。四柱天干 + 地支藏干一起数。"""
        import tiaohou as _TH
        cnt = {}
        for p in (b.year, b.month, b.day, b.hour):
            # 天干
            try:
                shen = _TH.shishen_of(b.day.gan, p.text())
                cnt[shen] = cnt.get(shen, 0) + 1
            except Exception:
                pass
            # 地支藏干
            for cg in BZ.ZHI_CANG.get(p.zhi, []):
                try:
                    shen = _TH.shishen_of(b.day.gan, cg + "子")
                    cnt[shen] = cnt.get(shen, 0) + 1
                except Exception:
                    pass
        if not cnt:
            return None
        if b.gender == "女":
            guan = cnt.get("正官", 0) + cnt.get("七杀", 0)
            shang = cnt.get("伤官", 0) + cnt.get("食神", 0)
            if guan == 0:
                return ("官星全无",
                        "这个女命盘里官星（正官+七杀）一个都没有，"
                        "传统说法是「夫星不显」，感情来得晚或者要靠人介绍。")
            if shang >= 3 and shang > guan:
                return ("伤官见官（克夫结构）",
                        "这个女命伤官食神共 %d 个，官星只有 %d 个，"
                        "传统叫「伤官见官」，古书说这类人容易看不上丈夫、"
                        "嘴上不饶人。★ 现代看就是「表达欲强、不肯将就」。" % (shang, guan))
            return None
        else:
            cai = cnt.get("正财", 0) + cnt.get("偏财", 0)
            jie = cnt.get("比肩", 0) + cnt.get("劫财", 0)
            if cai == 0:
                return ("财星全无",
                        "这个男命盘里财星（正财+偏财）一个都没有，"
                        "传统说法是「妻星不显」，妻缘来得晚。")
            if jie >= 3 and jie > cai:
                return ("比劫夺财（克妻结构）",
                        "这个男命比肩劫财共 %d 个，财星只有 %d 个，"
                        "传统叫「比劫夺财」，古书说这类人容易留不住妻、"
                        "或者总有人跟他抢。★ 现代看就是「太在意自己的圈子」。" % (jie, cai))
            return None

    k1 = _ke_spouse(b1, a1)
    k2 = _ke_spouse(b2, a2)
    for who, kk in ((b1, k1), (b2, k2)):
        if kk:
            out["细节"].append(("克夫克妻（%s）" % who.name, kk[0], kk[1]))
    if not k1 and not k2:
        out["细节"].append(("克夫克妻", "两边都没有明显硬伤",
                            "两个人的官星、财星都没被劫被伤，"
                            "传统说的「克夫」「克妻」结构都不成立。"))

    # ⑥ 全体地支合冲统计
    z1 = [p.zhi for p in (b1.year, b1.month, b1.day, b1.hour)]
    z2 = [p.zhi for p in (b2.year, b2.month, b2.day, b2.hour)]
    he_n, chong_n, hai_n, xing_n = 0, 0, 0, 0
    detail = []
    # ★ 一对地支可能同时有多种关系，不能 elif 短路
    for x in z1:
        for y in z2:
            if x == y:
                continue
            k = _zhi_kinds(x, y)
            if not k:
                continue
            tag = ""
            if "合" in k:
                he_n += 1
                tag += "合"
            if "冲" in k:
                chong_n += 1
                tag += "冲"
            if "害" in k:
                hai_n += 1
                tag += "害"
            if "刑" in k:
                xing_n += 1
                tag += "刑"
            detail.append(x + y + tag)
    out["地支统计"] = {"合": he_n, "冲": chong_n, "害": hai_n, "刑": xing_n,
                       "明细": detail}
    out["细节"].append((
        "四柱地支整体", "%d 合 / %d 冲" % (he_n, chong_n),
        "八对地支之间，合 %d 处、冲 %d 处、害 %d 处、刑 %d 处。%s"
        % (he_n, chong_n, hai_n, xing_n,
           "（" + "、".join(detail[:8]) + "）" if detail else "")))

    # ⑦ 三合局（双方地支合起来能不能成局）
    allz = z1 + z2
    san = []
    for k, v in SANHE.items():
        if all(c in allz for c in k):
            san.append("%s三合%s" % (k, v))
    out["三合"] = san
    if san:
        out["细节"].append(("合起来成局", "、".join(san),
                            "两个人的地支凑在一起能成局，说明有共同的事能一起干。"))

    # 粗估倾向（不是命定，只是把上面几层汇总）
    score = 50
    score += {"天干五合": 18, "同类": 4, "我生你": 8, "你生我": 8,
              "我克你": -8, "你克我": -8, "天干相冲": -12,
              "无直接关系": 0}.get(t1, 0)
    _t2map = {"六合": 18, "同支（伏吟）": -4, "六冲": -15, "相害": -8,
              "相刑": -8, "无关": 0}
    if t2 in _t2map:
        score += _t2map[t2]
    elif "合" in t2:
        score += 12          # 合中带刑：给合的分，但因为带刑少给
    else:
        score -= 6
    score += (len(fill1) + len(fill2)) * 4
    score -= len(conflict) * 18
    score += len(support) * 6
    score += min(he_n, 4) * 2 - min(chong_n, 4) * 3
    score += len(san) * 5

    # 新增五层按传统权重计入
    score += {"天合地合": 14, "年支相合": 5, "无特殊": 0,
              "年支相冲": -6, "天克地冲": -16}.get(out.get("年柱关系"), 0)
    score += {"纳音相生": 6, "纳音相同": 5, "纳音无关": 0,
              "纳音相克": -6}.get(out.get("纳音"), 0)
    score += {"男阳女阴": 5, "男阴女阳": -3, "双阳": -3,
              "双阴": 0}.get(out.get("阴阳"), 0)
    # 克夫克妻是硬伤，扣得最狠
    for who_name, kk in ((b1.name, k1), (b2.name, k2)):
        if kk:
            if "结构" in kk[0]:
                score -= 10
            elif "全无" in kk[0]:
                score -= 3

    score = max(5, min(95, score))
    out["粗估"] = score
    out["粗估说明"] = ("这只是把上面几层加权汇总的一个数，"
                       "不是命定，也不是结论，看下面的逐条说明才算数。")
    return out


def text_of(r):
    """给 AI 和界面用的文字版"""
    L = []
    L.append("【合盘】")
    L.append("  人一：%s" % r["人一"])
    L.append("  人二：%s" % r["人二"])
    L.append("")
    L.append("  ★ 代词规定：提到「人一」一律用「%s」；提到「人二」一律用「%s」。"
             % ("她" if "女" in r["人一"][:12] else "他",
                "她" if "女" in r["人二"][:12] else "他"))
    L.append("  ★ 不许出现「ta」「TA」「他/她」这类写法。")
    L.append("")
    for name, verdict, desc in r["细节"]:
        L.append("  ▸ %s → %s" % (name, verdict))
        L.append("     %s" % desc)
    L.append("")
    L.append("  用神对照：")
    L.append("    人一 喜 %s 忌 %s" % ("、".join(r["用神"]["一人喜"]),
                                      "、".join(r["用神"]["一人忌"])))
    L.append("    人二 喜 %s 忌 %s" % ("、".join(r["用神"]["二人喜"]),
                                      "、".join(r["用神"]["二人忌"])))
    L.append("")
    L.append("  粗估：%d / 100（%s）" % (r["粗估"], r["粗估说明"]))
    return "\n".join(L)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    from datetime import datetime

    b1 = BZ.paipan(datetime(2002, 3, 17, 16, 15), "女", "我",
                   true_solar=True, longitude=114.06)
    b2 = BZ.paipan(datetime(1994, 5, 7, 6, 0), "男", "男·1994",
                   true_solar=True, longitude=114.06)
    r = compute(b1, b2)
    print(text_of(r))
