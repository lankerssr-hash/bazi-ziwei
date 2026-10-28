# -*- coding: utf-8 -*-
"""盲派取象：把一个八字直接映射到「具体干什么、靠什么吃饭」。

所有规则都能在段氏理象学原文里找到出处，注释里标了行号。

    x = xiang_of(b)       # 返回 {"命中": [...], "清单": "文字"}
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bazi as BZ
import tiaohou as TH

# ---- 十神取象（段氏原文多见）----
XIANG_SHISHEN = {
    "正印": "房子、门店、文书、证书、技术、靠山、母亲",
    "偏印": "偏门的技术、手艺、玄学、医药、非主流靠山",
    "正财": "正经的钱、商品、实物、妻子",
    "偏财": "流动的钱、生意、客户、偏房",
    "正官": "职务、编制、规章、丈夫",
    "七杀": "压力、竞争、权力、军警、手术",
    "食神": "手艺、产品、口福、安逸",
    "伤官": "技艺、表达、锋芒、创新",
    "比肩": "同辈、兄弟、合伙人",
    "劫财": "竞争者、抢、朋友",
}

# ---- 宫位取象 ----
XIANG_POS = {
    "年": "祖上、幼年、远方、根基",
    "月": "父母、兄弟、工作环境、单位",
    "日": "本人、配偶、身体",
    "时": "子女、晚年、下属、门户、店铺",
}


def _shen(day_gan, ganzhi):
    try:
        return TH.shishen_of(day_gan, ganzhi)
    except Exception:
        return ""


def xiang_of(b):
    """返回 (命中的规则列表, 清单文字)"""
    hits = []      # [(规则名, 依据, 结论)]
    dg = b.day.gan
    pil = [("年", b.year), ("月", b.month), ("日", b.day), ("时", b.hour)]
    shen = {}
    for pos, p in pil:
        shen[pos] = _shen(dg, p.text())

    # ① 时上带印 → 门店（段氏 4598）
    if "印" in shen.get("时", ""):
        hits.append(("时上带印",
                     "时柱天干是%s，是%s，时柱主门户" % (b.hour.gan, shen["时"]),
                     "主门店、店铺、挂牌经营。适合开店，或者做别人的代理"))
    # ② 财落门户 → 买卖（段氏 5660）
    if "财" in shen.get("时", ""):
        hits.append(("财落门户",
                     "时柱天干是%s，是%s，财落在门户上" % (b.hour.gan, shen["时"]),
                     "主做买卖、开门做生意，钱从门面上来"))
    # ③ 日主合财 → 求财之象（段氏 5658）
    day_gan = b.day.gan
    for pos, p in pil:
        if pos == "日":
            continue
        if (day_gan + p.gan) in __import__("hepan").TIANGAN_HE or \
           (p.gan + day_gan) in __import__("hepan").TIANGAN_HE:
            if "财" in shen.get(pos, ""):
                hits.append(("日主合财",
                             "日干%s与%s柱天干%s相合，而%s是%s" % (
                                 day_gan, pos, p.gan, shen[pos], shen[pos]),
                             "主求财之象，会主动去找钱，多半是自己做买卖"))
            else:
                hits.append(("日干逢合",
                             "日干%s与%s柱天干%s相合" % (day_gan, pos, p.gan),
                             "这一合会把这个宫位的事直接绑到本人身上"))
    # ④ 印主技术（段氏 5662）
    yin_pos = [pos for pos, s in shen.items() if "印" in s]
    if yin_pos:
        hits.append(("印主技术",
                     "%s柱带%s" % ("、".join(yin_pos),
                                 "、".join(shen[p] for p in yin_pos)),
                     "印除了房子门店，也主一技之长，本人多半有手艺"))
    # ⑤ 食伤生财 → 靠技艺求财
    shen_list = [s for s in shen.values() if s]
    if any("食" in s or "伤" in s for s in shen_list) and \
       any("财" in s for s in shen_list):
        hits.append(("食伤生财",
                     "盘里既有%s，又有%s" % (
                         "、".join(s for s in shen_list if "食" in s or "伤" in s),
                         "、".join(s for s in shen_list if "财" in s)),
                     "靠自己的手艺、产品、表达去换钱，不是靠关系"))
    # ⑥ 官印相生 → 体制
    if any("官" in s or "杀" in s for s in shen_list) and yin_pos:
        hits.append(("官印相生",
                     "盘里既有官杀又有印星", "适合体制内、有编制、有上级托底的地方"))
    # ⑦ 宾主：财在年月 = 别人的钱
    if any("财" in shen.get(p, "") for p in ("年", "月")):
        hits.append(("财在宾位",
                     "财星在年柱或月柱，属于宾位", "钱是别人的，适合做代理、打工、经手别人的货"))
    # ⑧ 神煞取象
    try:
        zhis = [("年", b.year.zhi), ("月", b.month.zhi),
                ("日", b.day.zhi), ("时", b.hour.zhi)]
        ss = TH.shensha(b.day.gan, zhis)
        names = [x[0] for x in ss]
        if "驿马" in names:
            hits.append(("驿马", "命中带驿马", "主跑动，适合外勤、销售、运输、出差多的活"))
        if "华盖" in names:
            hits.append(("华盖", "命中带华盖", "主孤高，适合技术、艺术、宗教、研究类"))
        if "羊刃" in names:
            hits.append(("羊刃", "命中带羊刃", "主硬气，适合军警、医刀、机械、竞技"))
    except Exception:
        pass
    # ⑨ 五行取象（段氏 5663：酉为西方，金主病人）
    wx = BZ.analyze(b)["五行"]
    top = max(wx, key=lambda k: wx[k]) if wx else ""
    WX_XIANG = {
        "木": "木主生长、教育、文化、纺织、木材、园林",
        "火": "火主文明、传播、能源、餐饮、光电、演艺",
        "土": "土主土地、房产、建筑、农业、仓储、中介",
        "金": "金主金属、机械、金融、器械、刀兵、汽车",
        "水": "水主流动、贸易、物流、水产、旅游、信息",
    }
    if top:
        hits.append(("五行取象",
                     "盘里%s最旺（%d 个）" % (top, wx[top]), WX_XIANG.get(top, "")))

    # 拼文字
    L = ["【盲派取象（这是断「具体干什么」用的，不是看格局）】"]
    L.append("  取象的逻辑：宫位定「哪一段人生」，十神定「什么东西」，")
    L.append("  组合起来就是「他靠什么吃饭、在哪开门」。")
    L.append("  十神本象：印＝房子门店文书技术；财＝钱商品；官杀＝职务压力；")
    L.append("  食伤＝技艺产品；比劫＝同辈竞争。")
    L.append("  宫位本象：年月是宾位（别人的东西）；日时是主位（自己的东西）；")
    L.append("  时柱＝门户、店铺、下属。")
    L.append("")
    for name, basis, concl in hits:
        L.append("  ▸ %s：%s → %s" % (name, basis, concl))
    if not hits:
        L.append("  ▸ 这套规则下没有明显命中的取象，说明职业特征不突出。")
    L.append("")
    L.append("  ★ 用法：上面每一条都是一个「象」，不是结论。")
    L.append("  ★ 几个象叠在一起才敢断；只有一个象的时候要说明这只是倾向。")

    # 逐柱十神，方便 AI 自己再取象
    L.append("")
    L.append("  逐柱十神（天干）：" + "　".join(
        "%s柱%s→%s" % (pos, p.gan, shen[pos] or "—") for pos, p in pil))
    return hits, "\n".join(L)


def block_for_prompt(b):
    try:
        return xiang_of(b)[1]
    except Exception as e:
        return "（取象跳过：%s）" % e


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    from datetime import datetime

    for who, g, dt in (
        ("我（女）", "女", datetime(2002, 3, 17, 16, 15)),
        ("94男", "男", datetime(1994, 5, 7, 6, 0)),
    ):
        b = BZ.paipan(dt, g, who, true_solar=True, longitude=114.06)
        print("=" * 64)
        print(who, b.year.text(), b.month.text(), b.day.text(), b.hour.text())
        print(block_for_prompt(b))
        print()
