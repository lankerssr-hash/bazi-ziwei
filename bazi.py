# -*- coding: utf-8 -*-
"""八字排盘引擎 —— 只用 lunar_python + 标准库。

排盘规则：
· 年柱以【立春】换年（不是春节）
· 月柱以【节气】换月（不是农历月）
· 日柱按【真太阳时】还是北京时间，可选
· 大运：阳男阴女顺排，阴男阳女逆排；起运按出生到下一个节气的天数 ÷ 3
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from lunar_python import Solar, Lunar

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

# 五行
GAN_WUXING = dict(zip(GAN, "木木火火土土金金水水"))
ZHI_WUXING = dict(zip(ZHI, "水土木木土火火土金金土水"))

# 阴阳
GAN_YINYANG = {g: ("阳" if i % 2 == 0 else "阴") for i, g in enumerate(GAN)}
ZHI_YINYANG = {z: ("阳" if i % 2 == 0 else "阴") for i, z in enumerate(ZHI)}

# 地支藏干（本气、中气、余气）
ZHI_CANG = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "乙", "丁"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# 十神
def shishen(day_gan: str, other_gan: str) -> str:
    """以日干为我，求 other_gan 的十神"""
    me = GAN.index(day_gan)
    ot = GAN.index(other_gan)
    me_wx = GAN_WUXING[day_gan]
    ot_wx = GAN_WUXING[other_gan]
    same_yy = (me % 2) == (ot % 2)

    order = ["木", "火", "土", "金", "水"]
    mi, oi = order.index(me_wx), order.index(ot_wx)
    rel = (oi - mi) % 5

    if rel == 0:      # 同我：比肩 / 劫财
        return "比肩" if same_yy else "劫财"
    if rel == 1:      # 我生：食神 / 伤官
        return "食神" if same_yy else "伤官"
    if rel == 2:      # 我克：偏财 / 正财
        return "偏财" if same_yy else "正财"
    if rel == 3:      # 克我：七杀 / 正官
        return "七杀" if same_yy else "正官"
    return "偏印" if same_yy else "正印"


# 地支六冲 / 三合 / 六合
CHONG = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"),
         ("辰", "戌"), ("巳", "亥")]
LIUHE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
         "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
SANHE = {"申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金"}


@dataclass
class Pillar:
    gan: str
    zhi: str
    gan_wx: str = ""
    zhi_wx: str = ""
    gan_ss: str = ""          # 相对日干的十神
    cang: List[str] = field(default_factory=list)
    cang_ss: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.gan_wx = GAN_WUXING[self.gan]
        self.zhi_wx = ZHI_WUXING[self.zhi]
        self.cang = ZHI_CANG.get(self.zhi, [])

    def text(self) -> str:
        return self.gan + self.zhi


@dataclass
class Bazi:
    name: str
    gender: str            # 男 / 女
    solar: datetime
    true_solar: bool       # 是否用真太阳时修正
    longitude: float       # 出生地经度（真太阳时用）

    year: Pillar = None
    month: Pillar = None
    day: Pillar = None
    hour: Pillar = None

    lunar_text: str = ""
    jieqi_prev: str = ""
    jieqi_next: str = ""
    dayun: List[dict] = field(default_factory=list)
    qiyun_age: float = 0.0
    qiyun_desc: str = ""
    notes: List[str] = field(default_factory=list)

    def day_gan(self) -> str:
        return self.day.gan

    def all_pillars(self) -> List[Pillar]:
        return [self.year, self.month, self.day, self.hour]

    def wuxing_count(self) -> dict:
        """只算天干 + 地支本气（传统简易法）"""
        cnt = {k: 0 for k in "木火土金水"}
        for p in self.all_pillars():
            cnt[p.gan_wx] += 1
            if p.cang:
                cnt[GAN_WUXING[p.cang[0]]] += 1
        return cnt


def _true_solar_offset(longitude: float, tz: float = 8.0) -> float:
    """真太阳时的经度修正，单位：分钟（未含均时差）"""
    return (longitude - tz * 15.0) * 4.0


def paipan(solar: datetime, gender: str = "男", name: str = "命主",
           true_solar: bool = True, longitude: float = 114.06) -> Bazi:
    """排盘主函数。longitude 默认深圳 114.06E。"""
    notes = []
    dt = solar
    if true_solar:
        off = _true_solar_offset(longitude)
        dt = solar + __import__("datetime").timedelta(minutes=off)
        notes.append("真太阳时修正 %+.1f 分钟（经度 %.2fE）→ %s" %
                     (off, longitude, dt.strftime("%H:%M:%S")))

    s = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    l = s.getLunar()
    e = l.getEightChar()

    b = Bazi(name=name, gender=gender, solar=solar, true_solar=true_solar,
             longitude=longitude)
    b.lunar_text = l.toString()

    b.year = Pillar(e.getYearGan(), e.getYearZhi())
    b.month = Pillar(e.getMonthGan(), e.getMonthZhi())
    b.day = Pillar(e.getDayGan(), e.getDayZhi())
    b.hour = Pillar(e.getTimeGan(), e.getTimeZhi())

    # 十神（日柱天干对其它柱天干 + 藏干）
    for p in (b.year, b.month, b.day, b.hour):
        p.gan_ss = "日主" if p is b.day else shishen(b.day.gan, p.gan)
        p.cang_ss = [shishen(b.day.gan, g) for g in p.cang]

    # 节气
    try:
        prev_jq = l.getPrevJieQi(True)
        next_jq = l.getNextJieQi(True)
        b.jieqi_prev = "%s %s" % (prev_jq.getName(), prev_jq.getSolar().toYmdHms())
        b.jieqi_next = "%s %s" % (next_jq.getName(), next_jq.getSolar().toYmdHms())
    except Exception as ex:
        notes.append("节气读取失败：%s" % ex)

    # 大运
    try:
        yun = e.getYun(1 if gender == "男" else 0)
        sy, sm, sd, sh = (yun.getStartYear(), yun.getStartMonth(),
                          yun.getStartDay(), yun.getStartHour())
        b.qiyun_age = sy + sm / 12.0 + sd / 365.0 + sh / 8760.0
        b.qiyun_desc = "%d 岁 %d 个月 %d 天 起运（%s）" % (
            sy, sm, sd, "顺行" if yun.isForward() else "逆行")
        for d in yun.getDaYun()[:9]:
            if d.getGanZhi():
                b.dayun.append({
                    "index": d.getIndex(),
                    "start_age": d.getStartAge(),
                    "end_age": d.getEndAge(),
                    "start_year": d.getStartYear(),
                    "ganzhi": d.getGanZhi(),
                })
    except Exception as ex:
        notes.append("大运计算失败：%s" % ex)

    b.notes = notes
    return b


# ---------------- 分析层 ----------------

WX_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WX_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def analyze(b: Bazi) -> dict:
    """日主强弱 / 五行分布 / 格局 / 喜用神（简化版，传统子平路数）"""
    me = b.day.gan
    me_wx = GAN_WUXING[me]
    month_wx = b.month.zhi_wx

    cnt = b.wuxing_count()
    total = sum(cnt.values()) or 1

    # 得令 / 得地 / 得生 / 得助
    de_ling = (month_wx == me_wx) or (WX_SHENG[month_wx] == me_wx)
    de_di = any(WX_SHENG[p.zhi_wx] == me_wx or p.zhi_wx == me_wx
                for p in (b.year, b.day, b.hour))
    sheng_wo = [k for k, v in WX_SHENG.items() if v == me_wx][0]
    de_sheng = any(p.gan_wx == sheng_wo for p in (b.year, b.month, b.hour))
    de_zhu = any(p.gan_wx == me_wx for p in (b.year, b.month, b.hour))

    score = 0
    score += 3 if de_ling else 0
    score += 2 if de_di else 0
    score += 1 if de_sheng else 0
    score += 1 if de_zhu else 0

    # 五行占比修正
    share = cnt[me_wx] / total
    if share >= 0.35:
        score += 2
    elif share <= 0.15:
        score -= 1

    if score >= 5:
        strength = "偏强"
    elif score >= 3:
        strength = "中和"
    else:
        strength = "偏弱"

    # ---------------- 喜忌 ----------------
    # 原则：
    #   ① 盘里【一个都没有】的五行，不能当忌神（无形可忌）
    #   ② 身弱 → 忌克我、泄我（但只在它们确实存在且不弱时）
    #   ③ 身强 → 忌生我、同我
    #   ④ 中和 → 忌最旺的，喜最弱的
    cnt2 = dict(cnt)
    present = [k for k, v in cnt2.items() if v > 0]
    ke_me = [k for k, v in WX_KE.items() if v == me_wx][0]      # 克我的
    wo_ke = WX_KE[me_wx]                                        # 我克的
    wo_sheng = WX_SHENG[me_wx]                                  # 我生的
    sheng_me = [k for k, v in WX_SHENG.items() if v == me_wx][0]  # 生我的

    def top(n, pool=None):
        pool = pool or present
        if not pool:
            return []
        mx = max(cnt2[k] for k in pool)
        return [k for k in pool if cnt2[k] == mx][:n]

    def low(n, pool=None):
        pool = pool or present
        if not pool:
            return []
        mn = min(cnt2[k] for k in pool)
        return [k for k in pool if cnt2[k] == mn][:n]

    if strength == "偏弱":
        # 忌：克我、泄我里【存在的】
        ji = [k for k in (ke_me, wo_sheng, wo_ke) if cnt2[k] > 0]
        # 喜：生我、同我
        xi = [k for k in (sheng_me, me_wx)]
    elif strength == "偏强":
        # 忌：生我、同我
        ji = [k for k in (sheng_me, me_wx) if cnt2[k] > 0]
        # 喜：泄我、克我、我克
        xi = [k for k in (wo_sheng, wo_ke, ke_me) if cnt2[k] > 0 or k == wo_sheng]
    else:
        # 中和：忌最旺的，喜最弱的（且不能和忌重复）
        ji = top(2)
        xi = [k for k in low(2) if k not in ji] or low(1)

    # 兜底：喜忌不能有交集；忌神必须存在
    xi = [k for k in dict.fromkeys(xi) if k != me_wx or strength != "偏弱"]
    ji = [k for k in dict.fromkeys(ji) if k in present and k not in xi]
    xi = [k for k in xi if k not in ji] or [wo_sheng]
    xi = list(dict.fromkeys(xi))

    # 冲合
    zhis = [p.zhi for p in b.all_pillars()]
    chongs = []
    for a_, b_ in CHONG:
        if a_ in zhis and b_ in zhis:
            chongs.append("%s%s冲" % (a_, b_))
    hes = []
    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            if LIUHE.get(zhis[i]) == zhis[j]:
                hes.append("%s%s合" % (zhis[i], zhis[j]))
    sanhe = [k + "三合" + v for k, v in SANHE.items()
             if all(z in zhis for z in k)]

    return {
        "日主": me,
        "日主五行": me_wx,
        "月令": b.month.zhi + "（" + month_wx + "）",
        "得令": de_ling, "得地": de_di, "得生": de_sheng, "得助": de_zhu,
        "得分": score,
        "强弱": strength,
        "五行": cnt,
        "五行占比": {k: round(v / total * 100, 1) for k, v in cnt.items()},
        "喜神": xi, "忌神": ji,
        "冲": chongs, "合": hes, "三合": sanhe,
    }
