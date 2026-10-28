# -*- coding: utf-8 -*-
"""合盘：加「从对方的角度看你」的双向视角。

命理依据：
① 用【视角人的日干】去论【对方的日干】是什么十神
   —— 这就是「在他眼里你是什么角色」
② 视角人的配偶星（女看官杀、男看财）在对方盘里旺不旺
   —— 这就是「你是不是他命里那一颗」
③ 视角人的夫妻宫（日支）与对方日支的关系
   —— 这就是「他这块地方，你贴不贴得上」
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bazi as BZ
import hepan as HP


def _ten_god(a_gan, b_gan):
    """以 a 的日干为基准，看 b 的日干是什么十神"""
    try:
        return BZ.shishen(a_gan, b_gan)
    except Exception:
        try:
            return BZ.shishen(a_gan, b_gan, None)
        except Exception:
            return "?"


def _spouse_star(a):
    """视角人的配偶星五行。
    女命看官杀 → 克我者为官杀 → 五行是 克日主 的那个
    男命看财 → 我克者为财 → 五行是 日主 克 的那个
    """
    g = a.day.gan
    w = BZ.GAN_WUXING[g]
    if a.gender == "女":
        # 克我者 = 官杀
        for k, v in HP.WX_KE.items():
            if v == w:
                return k, "官杀（正官/七杀）"
        return "", "官杀"
    else:
        return HP.WX_KE[w], "财星（正财/偏财）"


def perspective(b_self, b_other):
    """b_self = 视角人；b_other = 被看的人。返回一段文字"""
    a_self = BZ.analyze(b_self)
    a_other = BZ.analyze(b_other)

    L = []
    L.append("【视角：以「我」＝%s（%s命）的第一人称，看 %s】" % (
        b_self.name, b_self.gender, b_other.name))
    L.append("  ★ 代词：视角人＝我（%s，用「我」）；对方＝%s（%s，用「%s」）。"
             % ("女" if b_self.gender == "女" else "男",
                b_other.name, b_other.gender,
                "她" if b_other.gender == "女" else "他"))
    L.append("  ★ 下面所有内容，请用「我」自称，写「我对%s的感觉」「%s看我」这样的句子。"
             % ("她" if b_other.gender == "女" else "他",
                "她" if b_other.gender == "女" else "他"))
    L.append("  ★ 不许写成第三人称的旁观分析，要像本人在说心里话。")
    L.append("  %s：%s命，日主%s（%s），日支（夫妻宫）%s%s" % (
        b_self.name, b_self.gender, b_self.day.gan,
        BZ.GAN_WUXING[b_self.day.gan], b_self.day.gan, b_self.day.zhi))

    # ① 对方的日干，在视角人眼里是什么十神
    tg = _ten_god(b_self.day.gan, b_other.day.gan)
    L.append("  ① 角色：%s 的日干是 %s%s，在 %s 的日干（%s）眼里是【%s】" % (
        b_other.name, b_other.day.gan,
        BZ.GAN_WUXING[b_other.day.gan],
        b_self.name, b_self.day.gan, tg))
    L.append("     十神对照：正官/七杀=有压力、能管住自己；正财/偏财=想抓住、想留住；")
    L.append("     食神/伤官=有才华但压不住；正印/偏印=像靠山、像长辈；")
    L.append("     比肩/劫财=像同类、像兄弟，亲近也容易抢。")

    # ② 视角人的配偶星，在对方盘里旺不旺
    star_wx, star_name = _spouse_star(b_self)
    cnt = a_other["五行"].get(star_wx, 0)
    L.append("  ② 命中不命中：%s 是%s命，配偶星是%s（%s）" % (
        b_self.name, b_self.gender, star_name, star_wx or "—"))
    L.append("     而这颗星在 %s 的盘里有 %d 个（五行分布 %s）" % (
        b_other.name, cnt,
        "／".join("%s%d" % (k, v) for k, v in a_other["五行"].items())))
    if cnt >= 2:
        L.append("     结论：%s 身上有他/她要的那颗星，而且是够量的。" % b_other.name)
    elif cnt == 1:
        L.append("     结论：%s 身上有一颗，但不算旺盛，属于「有但需要养」。" % b_other.name)
    else:
        L.append("     结论：%s 盘里这颗星是全无的，"
                 "说明在 %s 的标准里，%s 不是那种一眼对味的类型。" % (
                     b_other.name, b_self.name, b_other.name))

    # ③ 夫妻宫关系
    kind, desc = HP._rel_zhi(b_self.day.zhi, b_other.day.zhi, "夫妻宫")
    L.append("  ③ 贴上不贴上：%s 的夫妻宫是 %s，%s 的日支是 %s，关系是【%s】" % (
        b_self.name, b_self.day.zhi, b_other.name, b_other.day.zhi, kind))
    L.append("     " + desc)

    # ④ 视角人的喜忌 vs 对方的五行
    xi = a_self["喜神"]
    ji = a_self["忌神"]
    other_wx = a_other["五行"]
    good = [x for x in xi if other_wx.get(x, 0) > 0]
    bad = [x for x in ji if other_wx.get(x, 0) > 0]
    L.append("  ④ 补不补：%s 喜 %s、忌 %s" % (
        b_self.name, "、".join(xi) or "—", "、".join(ji) or "—"))
    L.append("     %s 盘里有 %s，能补到喜用；也有 %s，会踩到忌神" % (
        b_other.name,
        "、".join(good) or "（没有喜用的五行）",
        "、".join(bad) or "（没有忌神的五行）"))

    return "\n".join(L)


def both(b1, b2):
    return (perspective(b1, b2), perspective(b2, b1))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    from datetime import datetime

    me = BZ.paipan(datetime(2002, 3, 17, 16, 15), "女", "我",
                   true_solar=True, longitude=114.06)
    he = BZ.paipan(datetime(1994, 5, 7, 6, 0), "男", "男·1994",
                   true_solar=True, longitude=114.06)
    print("=" * 62)
    print(perspective(me, he))
    print()
    print("=" * 62)
    print(perspective(he, me))
