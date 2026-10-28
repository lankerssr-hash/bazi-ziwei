# -*- coding: utf-8 -*-
"""八字分析 —— PySide6 界面"""
import io
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTextEdit, QTabWidget, QFrame, QSizePolicy,
)
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtCore import Qt

import bazi as BZ
import classics as CL
import tiaohou as TH
import ai_read as AI
import cases as CS

_DBG = _os.path.join(HERE, "_debug.log")


def _dbg(msg):
    """直接写文件，不靠 stdout"""
    try:
        import time as _t
        with io.open(_DBG, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (_t.strftime("%H:%M:%S"), msg))
    except Exception:
        pass

# ---------- 粉色系主题 ----------
PINK_BG = "#fdf4f9"      # 页面底色：极淡粉
PINK_CARD = "#ffffff"    # 卡片：纯白
PINK_LINE = "#f6d5e8"    # 边框：浅粉
PINK_MAIN = "#e84d8a"    # 主色：玫粉
PINK_DEEP = "#c2286a"    # 深一点的玫粉
PINK_SOFT = "#ffe3f0"    # 浅粉填充
TEXT_MAIN = "#3d2433"    # 正文：偏紫的深色
TEXT_SUB = "#9a7f90"     # 次要文字

WX_COLOR = {
    "木": "#3fae7a", "火": "#f2643f", "土": "#d09a5c",
    "金": "#b08cc4", "水": "#5b9bf0",
}


class PillarBox(QFrame):
    """一柱：天干 / 地支 / 藏干 / 十神"""

    def __init__(self, title: str, p: BZ.Pillar, is_day=False):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #ffffff,stop:1 #fff5fa);"
            "border:2px solid #f9d3e6;border-radius:16px;}"
            "QLabel{border:none;background:transparent;}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(2)

        cap = QLabel(title)
        cap.setAlignment(Qt.AlignCenter)
        cap.setStyleSheet("color:#6b7280;font-size:12px;")
        lay.addWidget(cap)

        g = QLabel(p.gan)
        g.setAlignment(Qt.AlignCenter)
        g.setFont(QFont("KaiTi", 30, QFont.Bold))
        g.setStyleSheet("color:%s;" % WX_COLOR.get(p.gan_wx, "#111"))
        lay.addWidget(g)

        z = QLabel(p.zhi)
        z.setAlignment(Qt.AlignCenter)
        z.setFont(QFont("KaiTi", 30, QFont.Bold))
        z.setStyleSheet("color:%s;" % WX_COLOR.get(p.zhi_wx, "#111"))
        lay.addWidget(z)

        ss = QLabel("日主" if is_day else p.gan_ss)
        ss.setAlignment(Qt.AlignCenter)
        ss.setStyleSheet("color:#111;font-size:12px;font-weight:600;")
        lay.addWidget(ss)

        cang = "、".join(p.cang) if p.cang else "—"
        cl = QLabel("藏 " + cang)
        cl.setAlignment(Qt.AlignCenter)
        cl.setStyleSheet("color:#6b7280;font-size:11px;")
        lay.addWidget(cl)

        cs = " ".join(p.cang_ss[:3]) if p.cang_ss else ""
        csl = QLabel(cs)
        csl.setAlignment(Qt.AlignCenter)
        csl.setWordWrap(True)
        csl.setStyleSheet("color:#9aa2ad;font-size:10px;")
        lay.addWidget(csl)


class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("✿ 八字分析 ✿")
        self.resize(1120, 800)
        self.setStyleSheet(
            "QWidget{background:%s;color:%s;}"
            "QLabel{background:transparent;}" % (PINK_BG, TEXT_MAIN))

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        # ---------- 输入 ----------
        box = QFrame()
        box.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #ffffff,stop:0.5 #fff8fc,stop:1 #ffeef7);"
            "border:2px solid #f9d3e6;border-radius:18px;}")
        g = QGridLayout(box)
        g.setContentsMargins(12, 10, 12, 10)
        g.setHorizontalSpacing(10)

        self.ed_name = QLineEdit("命主")
        self.ed_name.setMaximumWidth(110)
        self.cb_gender = QComboBox()
        self.cb_gender.addItems(["男", "女"])
        self.cb_gender.setMaximumWidth(70)

        self.sp_year = QSpinBox(); self.sp_year.setRange(1900, 2100); self.sp_year.setValue(1990)
        self.sp_month = QSpinBox(); self.sp_month.setRange(1, 12); self.sp_month.setValue(5)
        self.sp_day = QSpinBox(); self.sp_day.setRange(1, 31); self.sp_day.setValue(15)
        self.sp_hour = QSpinBox(); self.sp_hour.setRange(0, 23); self.sp_hour.setValue(10)
        self.sp_min = QSpinBox(); self.sp_min.setRange(0, 59); self.sp_min.setValue(30)
        for w in (self.sp_year, self.sp_month, self.sp_day, self.sp_hour, self.sp_min):
            w.setMaximumWidth(72)

        self.cb_city = QComboBox()
        self.cb_city.addItems([
            "深圳 114.06", "北京 116.41", "上海 121.47", "广州 113.26",
            "成都 104.07", "重庆 106.55", "杭州 120.16", "武汉 114.31",
            "西安 108.94", "哈尔滨 126.53", "乌鲁木齐 87.62", "拉萨 91.11",
            "香港 114.17", "台北 121.52", "新加坡 103.85", "东京 139.69",
        ])
        self.cb_city.setMaximumWidth(150)

        self.chk_true = QCheckBox("真太阳时")
        self.chk_true.setChecked(True)

        self.btn_ai = QPushButton("AI 解盘")
        self.btn_ai.setMinimumWidth(96)
        self.btn_ai.setEnabled(False)
        self.btn_ai.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #b06ab3,stop:1 #ec6fa8);color:#fff;border:none;"
            "border-radius:12px;padding:9px 18px;font-weight:600;}"
            "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #a05aa3,stop:1 #e05a98);}"
            "QPushButton:disabled{background:#f0dbe6;color:#c9b2c0;}")

        self.btn = QPushButton("排盘")
        self.btn.setMinimumWidth(96)
        self.btn.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #f06292,stop:1 #e84d8a);color:#fff;border:none;"
            "border-radius:12px;padding:9px 18px;font-weight:600;"
            "font-size:14px;}"
            "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #ec407a,stop:1 #d81b60);}")

        g.addWidget(self.btn_ai, 0, 7, 1, 1)
        g.addWidget(QLabel("姓名"), 0, 0)
        g.addWidget(self.ed_name, 0, 1)
        g.addWidget(QLabel("性别"), 0, 2)
        g.addWidget(self.cb_gender, 0, 3)
        g.addWidget(QLabel("出生地"), 0, 4)
        g.addWidget(self.cb_city, 0, 5)
        g.addWidget(self.chk_true, 0, 6)
        g.addWidget(self.btn, 1, 7, 1, 1)

        g.addWidget(QLabel("命例"), 2, 0)
        self.cb_case = QComboBox()
        self.cb_case.setMaximumWidth(320)
        self.cb_case.addItem("（新命例）", None)
        g.addWidget(self.cb_case, 2, 1, 1, 3)

        self.btn_save = QPushButton("保存命例")
        self.btn_save.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #66d9b5,stop:1 #3fae7a);color:#fff;border:none;"
            "border-radius:11px;padding:8px 14px;font-weight:600;}"
            "QPushButton:hover{background:#38a374;}")
        self.btn_del = QPushButton("删除")
        self.btn_del.setStyleSheet(
            "QPushButton{background:#b91c1c;color:#fff;border:none;"
            "border-radius:8px;padding:8px 14px;}")
        g.addWidget(self.btn_save, 2, 4)
        g.addWidget(self.btn_del, 2, 5)

        g.addWidget(QLabel("公历"), 1, 0)
        row = QHBoxLayout()
        for w in (self.sp_year, self.sp_month, self.sp_day):
            row.addWidget(w)
        row.addWidget(QLabel("时"))
        row.addWidget(self.sp_hour)
        row.addWidget(QLabel("分"))
        row.addWidget(self.sp_min)
        gg = QWidget(); gg.setLayout(row)
        g.addWidget(gg, 1, 1, 1, 6)

        root.addWidget(box)

        # ---------- 命盘 ----------
        self.panel = QFrame()
        self.panel.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #ffffff,stop:1 #fff3f9);"
            "border:2px solid #f9d3e6;border-radius:18px;}")
        pl = QVBoxLayout(self.panel)
        pl.setContentsMargins(12, 10, 12, 10)

        self.lbl_head = QLabel("✿ 填好左边，点「排盘」")
        self.lbl_head.setStyleSheet(
            "color:#c2286a;font-size:13.5px;font-weight:600;")
        pl.addWidget(self.lbl_head)

        self.pillars = QHBoxLayout()
        self.pillars.setSpacing(8)
        pl.addLayout(self.pillars)

        self.lbl_info = QLabel("")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet("color:#4b5563;font-size:12.5px;padding-top:6px;")
        pl.addWidget(self.lbl_info)

        root.addWidget(self.panel)

        # ---------- 分析 / 大运 ----------
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabWidget::pane{background:#fff;border:2px solid #f9d3e6;"
            "border-radius:16px;top:-2px;}"
            "QTabBar::tab{background:#ffe9f3;color:#b06a8e;padding:8px 20px;"
            "margin-right:3px;border-top-left-radius:12px;"
            "border-top-right-radius:12px;font-size:13px;}"
            "QTabBar::tab:selected{background:#fff;color:#c2286a;"
            "font-weight:600;border:2px solid #f9d3e6;border-bottom:none;}"
            "QTabBar::tab:hover{background:#ffd9ea;}")

        self.txt_an = QTextEdit(); self.txt_an.setReadOnly(True)
        self.txt_an.setFont(QFont("Microsoft YaHei", 11))
        self.txt_an.setStyleSheet("border:none;padding:12px;background:#ffffff;")
        self.tabs.addTab(self.txt_an, "分析")

        self.txt_dy = QTextEdit(); self.txt_dy.setReadOnly(True)
        self.txt_dy.setFont(QFont("Microsoft YaHei", 11))
        self.txt_dy.setStyleSheet("border:none;padding:12px;background:#ffffff;")
        self.tabs.addTab(self.txt_dy, "大运")

        # AI 分项按钮排
        sec_bar = QHBoxLayout()
        sec_bar.setSpacing(6)
        self.sec_btns = []
        for nm in ("总评", "性格", "事业", "财运", "感情", "配偶", "颜值", "健康", "大运"):
            b = QPushButton(nm)
            b.setStyleSheet(
                "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 #fff0f7,stop:1 #ffd9ea);color:#c2286a;"
                "border:1.5px solid #f7bfd9;border-radius:14px;"
                "padding:7px 16px;font-size:13px;font-weight:600;}"
                "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 #ffe3f0,stop:1 #ffc4de);border-color:#ec6fa8;}"
                "QPushButton:disabled{background:#fdf4f9;color:#d9c3d0;"
                "border-color:#f6e5ee;}")
            b.setEnabled(False)
            b.clicked.connect(lambda _=False, n=nm: self.run_ai_section(n))
            self.sec_btns.append(b)
            sec_bar.addWidget(b)
        sec_bar.addStretch(1)
        self.lbl_sec = QLabel("")
        self.lbl_sec.setStyleSheet("color:#6b7280;font-size:12px;")
        sec_bar.addWidget(self.lbl_sec)
        self.ai_panel = QWidget()
        vv = QVBoxLayout(self.ai_panel)
        vv.setContentsMargins(0, 0, 0, 0)
        vv.setSpacing(6)
        vv.addLayout(sec_bar)

        self.txt_ai = QTextEdit(); self.txt_ai.setReadOnly(True)
        self.txt_ai.setFont(QFont("Microsoft YaHei", 11))
        self.txt_ai.setStyleSheet("border:none;padding:12px;background:#ffffff;")
        vv.addWidget(self.txt_ai)
        self.tabs.addTab(self.ai_panel, "AI 解盘")

        self.txt_raw = QTextEdit(); self.txt_raw.setReadOnly(True)
        self.txt_raw.setFont(QFont("Consolas", 10))
        self.txt_raw.setStyleSheet("border:none;padding:12px;background:#fefbfd;")
        self.tabs.addTab(self.txt_raw, "原始数据")

        root.addWidget(self.tabs, 1)

        self.btn.clicked.connect(self.run)
        self.btn_ai.clicked.connect(self.run_ai)
        self.btn_save.clicked.connect(self.save_case)
        self.btn_del.clicked.connect(self.del_case)
        self.cb_case.currentIndexChanged.connect(self.load_case)
        self.cb_case.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cb_case.customContextMenuRequested.connect(self.case_menu)
        self.refresh_cases()

    def run(self):
        long_ = float(self.cb_city.currentText().split()[-1])
        dt = datetime(self.sp_year.value(), self.sp_month.value(),
                      self.sp_day.value(), self.sp_hour.value(),
                      self.sp_min.value())
        try:
            b = BZ.paipan(dt, self.cb_gender.currentText(), self.ed_name.text().strip() or "命主",
                          true_solar=self.chk_true.isChecked(), longitude=long_)
            a = BZ.analyze(b)
        except Exception as e:
            self.lbl_head.setText("排盘出错：%s" % e)
            return

        # 四柱
        while self.pillars.count():
            it = self.pillars.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for title, p, isd in (("年柱", b.year, False), ("月柱", b.month, False),
                              ("日柱", b.day, True), ("时柱", b.hour, False)):
            self.pillars.addWidget(PillarBox(title, p, isd))

        self.lbl_head.setText("　".join([
            b.name + "　" + b.gender,
            "四柱：%s %s %s %s" % (b.year.text(), b.month.text(),
                                   b.day.text(), b.hour.text()),
            "日主：%s（%s）" % (b.day.gan, a["日主五行"]),
            "强弱：%s" % a["强弱"],
        ]))

        cnt = a["五行"]
        self.lbl_info.setText(
            "农历：%s　｜　五行：木 %d　火 %d　土 %d　金 %d　水 %d　｜　喜 %s　忌 %s"
            % (b.lunar_text, cnt["木"], cnt["火"], cnt["土"], cnt["金"], cnt["水"],
               "".join(a["喜神"]), "".join(a["忌神"])))

        self._last = (b, a)
        self.btn_ai.setEnabled(True)
        for _b in getattr(self, "sec_btns", []):
            _b.setEnabled(True)
        self.txt_an.setPlainText(self.build_analysis(b, a) + self.build_classics(b, a))
        self.txt_dy.setPlainText(self.build_dayun(b))
        self.txt_raw.setPlainText(self.build_raw(b, a))

    def build_analysis(self, b, a):
        L = []
        L.append("【四柱】")
        for nm, p in (("年柱", b.year), ("月柱", b.month), ("日柱", b.day), ("时柱", b.hour)):
            L.append("  %s  %s%s   十神 %-4s   藏干 %s（%s）" % (
                nm, p.gan, p.zhi, p.gan_ss,
                "、".join(p.cang) or "—", "、".join(p.cang_ss) or "—"))
        L.append("")
        L.append("【日主强弱】")
        L.append("  日主 %s（%s），月令 %s" % (a["日主"], a["日主五行"], a["月令"]))
        L.append("  得令 %s　得地 %s　得生 %s　得助 %s　→ 合计 %d 分" % (
            "是" if a["得令"] else "否", "是" if a["得地"] else "否",
            "是" if a["得生"] else "否", "是" if a["得助"] else "否", a["得分"]))
        L.append("  → 判为【%s】（简易评分法，5 分以上偏强，3~4 中和，3 以下偏弱）"
                 % a["强弱"])
        L.append("")
        L.append("【五行分布】")
        for k in "木火土金水":
            n = a["五行"][k]
            pct = a["五行占比"][k]
            bar = "█" * int(pct / 5)
            L.append("  %s  %d 个  %5.1f%%  %s" % (k, n, pct, bar))
        L.append("")
        L.append("【喜用与忌讳】")
        L.append("  喜：%s" % "、".join(a["喜神"]))
        L.append("  忌：%s" % "、".join(a["忌神"]))
        L.append("  （按身强喜财官食伤、身弱喜印比的简化取法）")
        L.append("")
        L.append("【刑冲合】")
        L.append("  冲：%s" % ("、".join(a["冲"]) or "无"))
        L.append("  合：%s" % ("、".join(a["合"]) or "无"))
        L.append("  三合：%s" % ("、".join(a["三合"]) or "无"))
        L.append("")
        L.append("【起运】")
        L.append("  %s" % b.qiyun_desc)
        L.append("")
        L.append("【说明】")
        L.append("  · 年柱以立春换年，月柱以节气换月（不是农历初一）")
        L.append("  · 节气：前 %s ／ 后 %s" % (b.jieqi_prev, b.jieqi_next))
        for n in b.notes:
            L.append("  · " + n)
        return "\n".join(L)

    def refresh_cases(self):
        cur = self.cb_case.currentData()
        self.cb_case.blockSignals(True)
        self.cb_case.clear()
        self.cb_case.addItem("（新命例）", None)
        for i, c in enumerate(CS.all_cases()):
            label = "%s  %04d-%02d-%02d %02d:%02d  %s" % (
                c.get("name", "?"), c.get("year", 0), c.get("month", 0),
                c.get("day", 0), c.get("hour", 0), c.get("minute", 0),
                c.get("pillars", ""))
            self.cb_case.addItem(label, i)
        self.cb_case.blockSignals(False)
        if cur is not None:
            k = self.cb_case.findData(cur)
            if k >= 0:
                self.cb_case.setCurrentIndex(k)

    def case_menu(self, pos):
        """命例下拉的右键菜单"""
        from PySide6.QtWidgets import QMenu, QInputDialog, QMessageBox
        idx = self.cb_case.currentData()
        m = QMenu(self)
        if idx is not None:
            items = CS.all_cases()
            if 0 <= idx < len(items):
                c = items[idx]
                title = "%s  %04d-%02d-%02d %02d:%02d" % (
                    c.get("name", "?"), c.get("year", 0), c.get("month", 0),
                    c.get("day", 0), c.get("hour", 0), c.get("minute", 0))
                act_title = m.addAction("　" + title)
                act_title.setEnabled(False)
                m.addSeparator()
                a_del = m.addAction("删除这条命例")
                a_ren = m.addAction("重命名…")
                a_copy = m.addAction("复制四柱")
            else:
                a_del = a_ren = a_copy = None
        else:
            a_del = a_ren = a_copy = None
        m.addSeparator()
        a_ref = m.addAction("刷新列表")

        chosen = m.exec(self.cb_case.mapToGlobal(pos))
        if chosen is None:
            return

        if a_del is not None and chosen == a_del:
            items = CS.all_cases()
            c = items[idx]
            ok = QMessageBox.question(
                self, "确认删除",
                "删掉这条命例？\n\n%s  %04d-%02d-%02d %02d:%02d\n%s" % (
                    c.get("name", "?"), c.get("year", 0), c.get("month", 0),
                    c.get("day", 0), c.get("hour", 0), c.get("minute", 0),
                    c.get("pillars", "")),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ok == QMessageBox.Yes:
                CS.del_case(c.get("name"), c.get("year"), c.get("month"),
                            c.get("day"), c.get("hour"), c.get("minute"))
                self.refresh_cases()
                self.lbl_head.setText("已删除")
        elif a_ren is not None and chosen == a_ren:
            items = CS.all_cases()
            c = items[idx]
            new, ok = QInputDialog.getText(self, "重命名", "新的名字：",
                                           text=c.get("name", ""))
            if ok and new.strip():
                CS.add_case(new.strip(), c.get("gender"), c.get("year"),
                            c.get("month"), c.get("day"), c.get("hour"),
                            c.get("minute"),
                            longitude=c.get("longitude", 114.06),
                            true_solar=c.get("true_solar", True),
                            note=c.get("note", ""),
                            day_gz="", month_gz="", year_gz="", hour_gz="",
                            strength=c.get("strength", ""), ge=c.get("ge", ""))
                # 旧的删掉
                CS.del_case(c.get("name"), c.get("year"), c.get("month"),
                            c.get("day"), c.get("hour"), c.get("minute"))
                self.refresh_cases()
                self.lbl_head.setText("已重命名")
        elif a_copy is not None and chosen == a_copy:
            from PySide6.QtWidgets import QApplication as _QA
            items = CS.all_cases()
            _QA.clipboard().setText(items[idx].get("pillars", ""))
            self.lbl_head.setText("四柱已复制")
        elif chosen == a_ref:
            self.refresh_cases()

    def load_case(self):
        idx = self.cb_case.currentData()
        if idx is None:
            return
        items = CS.all_cases()
        if idx < 0 or idx >= len(items):
            return
        c = items[idx]
        self.ed_name.setText(c.get("name", "命主"))
        self.cb_gender.setCurrentText(c.get("gender", "男"))
        self.sp_year.setValue(c.get("year", 1990))
        self.sp_month.setValue(c.get("month", 1))
        self.sp_day.setValue(c.get("day", 1))
        self.sp_hour.setValue(c.get("hour", 0))
        self.sp_min.setValue(c.get("minute", 0))
        self.chk_true.setChecked(bool(c.get("true_solar", True)))
        self.run()

    def save_case(self):
        b = getattr(self, "_last", (None, None))[0]
        a = getattr(self, "_last", (None, None))[1]
        if not b:
            self.lbl_head.setText("先点「排盘」，再保存")
            return
        ge, _ = CL.judge_ge(b.day.gan, b.month.zhi, b.month.cang, BZ.shishen)
        n = CS.add_case(
            self.ed_name.text().strip() or "命主",
            self.cb_gender.currentText(),
            self.sp_year.value(), self.sp_month.value(),
            self.sp_day.value(), self.sp_hour.value(), self.sp_min.value(),
            longitude=float(self.cb_city.currentText().split()[-1]),
            true_solar=self.chk_true.isChecked(),
            day_gz=b.day.text(), month_gz=b.month.text(),
            year_gz=b.year.text(), hour_gz=b.hour.text(),
            strength=a["强弱"], ge=ge)
        self.refresh_cases()
        self.lbl_head.setText("已保存，命例库共 %d 条" % n)

    def del_case(self):
        idx = self.cb_case.currentData()
        if idx is None:
            self.lbl_head.setText("先在下拉里选一条命例")
            return
        items = CS.all_cases()
        if idx < 0 or idx >= len(items):
            return
        c = items[idx]
        CS.del_case(c.get("name"), c.get("year"), c.get("month"),
                    c.get("day"), c.get("hour"), c.get("minute"))
        self.refresh_cases()
        self.lbl_head.setText("已删除")

    def _poll_ai(self):
        """主线程轮询 AI 结果"""
        box = getattr(self, "_ai_box", None)
        if box is None:
            return
        self._ai_tick = getattr(self, "_ai_tick", 0) + 1
        if self._ai_tick % 10 == 1:
            _dbg("poll 第 %d 次 keys=%s" % (self._ai_tick, list(box.keys())))

        if "ok" in box:
            _dbg("poll 拿到结果 %d 字" % len(box["ok"]))
            self._ai_timer.stop()
            self.txt_ai.setPlainText(box["ok"])
            self.btn_ai.setEnabled(True)
            for _b in getattr(self, "sec_btns", []):
                _b.setEnabled(True)
            _bad = box.get("bad_clauses")
            if getattr(self, "_ai_section", None):
                self.lbl_sec.setText("「%s」完成%s" % (
                    self._ai_section,
                    ("　断句超标 %d 处" % _bad) if _bad and _bad > 0 else ""))
            self._ai_box = None
            return

        if "fail" in box:
            _dbg("poll 拿到失败: %s" % str(box["fail"])[:80])
            self._ai_timer.stop()
            self.txt_ai.setPlainText(
                "AI 解盘失败：\n\n" + str(box["fail"]) +
                "\n\n检查：8787 转发站是否在跑、key.txt 是否有效。")
            self.btn_ai.setEnabled(True)
            for _b in getattr(self, "sec_btns", []):
                _b.setEnabled(True)
            self._ai_box = None
            return

        # 超时 5 分钟
        if self._ai_tick > 600:
            _dbg("poll 超时")
            self._ai_timer.stop()
            self.txt_ai.setPlainText("AI 解盘超时（5 分钟没回）。"
                                     "\n\n检查 8787 转发站。")
            self.btn_ai.setEnabled(True)
            for _b in getattr(self, "sec_btns", []):
                _b.setEnabled(True)
            self._ai_box = None

    def run_ai_section(self, name):
        _dbg("section 点了: " + name)
        if not getattr(self, "_last", None):
            _dbg("section: _last 是空的")
            return
        b, a = self._last
        self.tabs.setCurrentWidget(self.ai_panel)
        for _b in self.sec_btns:
            _b.setEnabled(False)
        self.lbl_sec.setText("正在解「%s」…约 20~40 秒" % name)
        self.txt_ai.setPlainText("正在解「%s」……" % name)

        ge, why = CL.judge_ge(b.day.gan, b.month.zhi, b.month.cang, BZ.shishen)
        gk, gv = CL.gan_lun(b.day.gan)
        sk, sv = TH.tiaohou(b.day.gan, b.month.zhi)
        zhis = [("年", b.year.zhi), ("月", b.month.zhi),
                ("日", b.day.zhi), ("时", b.hour.zhi)]
        ss = TH.shensha(b.day.gan, zhis)
        rz = TH.rizhu_duan(b.day.text())
        kw = TH.kongwang(b.day.text())
        dy = "  ".join("%d~%d岁 %s" % (d["start_age"], d["end_age"], d["ganzhi"])
                       for d in b.dayun if d["ganzhi"])
        now_y = __import__("datetime").datetime.now().year
        ln = "  ".join("%d %s(%s)" % (y, gz, TH.shishen_of(b.day.gan, gz))
                       for y, gz in TH.liunian(now_y, 4))
        prompt = AI.build_user_prompt(b, a, ge, why, gk, gv, sk, sv, ss, rz, kw, dy, ln)

        self._ai_box = {}
        self._ai_section = name
        self._ai_tick = 0
        _dbg("section: 送请求 prompt %d 字" % len(prompt))
        AI.ask(prompt, None, None, box=self._ai_box,
               prompt=AI.section_prompt(name))
        _dbg("section: ask 已发起")

        from PySide6.QtCore import QTimer
        if getattr(self, "_ai_timer", None) is None:
            self._ai_timer = QTimer(self)
            self._ai_timer.setInterval(500)
            self._ai_timer.timeout.connect(self._poll_ai)
            _dbg("section: 创建定时器")
        self._ai_timer.start()
        _dbg("section: 定时器 active=%s" % self._ai_timer.isActive())

    def run_ai(self):
        if not getattr(self, "_last", None):
            return
        b, a = self._last
        self.btn_ai.setEnabled(False)
        self.tabs.setCurrentWidget(self.txt_ai)
        self.txt_ai.setPlainText("正在请求 AI 解盘……\n\n"
                                 "（走本机 8787 转发站，不需要梯子。约 30~90 秒）")

        ge, why = CL.judge_ge(b.day.gan, b.month.zhi, b.month.cang, BZ.shishen)
        gk, gv = CL.gan_lun(b.day.gan)
        sk, sv = TH.tiaohou(b.day.gan, b.month.zhi)
        zhis = [("年", b.year.zhi), ("月", b.month.zhi),
                ("日", b.day.zhi), ("时", b.hour.zhi)]
        ss = TH.shensha(b.day.gan, zhis)
        rz = TH.rizhu_duan(b.day.text())
        kw = TH.kongwang(b.day.text())

        dy = "  ".join("%d~%d岁 %s" % (d["start_age"], d["end_age"], d["ganzhi"])
                       for d in b.dayun if d["ganzhi"])
        now_y = __import__("datetime").datetime.now().year
        ln = "  ".join("%d %s(%s)" % (y, gz, TH.shishen_of(b.day.gan, gz))
                       for y, gz in TH.liunian(now_y, 4))

        txt = AI.build_user_prompt(b, a, ge, why, gk, gv, sk, sv, ss, rz, kw, dy, ln)

        # ★ 后台线程只往 box 里写，主线程用定时器取（Qt 不许跨线程碰控件）
        self._ai_box = {}
        AI.ask(txt, None, None, box=self._ai_box)
        self._ai_tick = 0

        from PySide6.QtCore import QTimer
        if getattr(self, "_ai_timer", None) is None:
            self._ai_timer = QTimer(self)
            self._ai_timer.setInterval(500)
            self._ai_timer.timeout.connect(self._poll_ai)
        self._ai_timer.start()

    def build_classics(self, b, a):
        L = []
        L.append("")
        L.append("=" * 52)
        L.append("【日主本性】出处：《滴天髓》天干论")
        gk, gv = CL.gan_lun(b.day.gan)
        if gv:
            L.append("  （%s）" % gk)
            L.append("")
            for x in range(0, len(gv), 60):
                L.append("  " + gv[x:x+60])
        else:
            L.append("  （未收）")

        L.append("")
        L.append("=" * 52)
        L.append("【神煞】")
        zhis = [("年", b.year.zhi), ("月", b.month.zhi),
                ("日", b.day.zhi), ("时", b.hour.zhi)]
        ss = TH.shensha(b.day.gan, zhis)
        if ss:
            for label, pos, target in ss:
                L.append("  %s —— 落在%s支（%s）" % (label, pos, target))
        else:
            L.append("  四柱地支里未见所录贵人（查了天乙/玉堂/文昌/天印/禄）")

        L.append("")
        L.append("【纳音】")
        for nm, p in (("年", b.year), ("月", b.month), ("日", b.day), ("时", b.hour)):
            L.append("  %s柱 %s → %s" % (nm, p.text(), TH.nayin_of(p.text())))

        L.append("")
        L.append("【日柱专论】%s" % b.day.text())
        rz = TH.rizhu_duan(b.day.text())
        L.append("  " + (rz if rz else "（未收）"))

        L.append("")
        L.append("【空亡】以日柱 %s 起旬" % b.day.text())
        kw = TH.kongwang(b.day.text())
        L.append("  空亡：%s" % ("、".join(kw) if kw else "—"))

        L.append("")
        L.append("=" * 52)
        L.append("【调候】出处：《穷通宝鉴》（徐乐吾评注本）")
        tk, tv = TH.tiaohou(b.day.gan, b.month.zhi)
        if tv:
            L.append("  查表键：%s（%s日生%s月）" % (tk, b.day.gan, b.month.zhi))
            L.append("")
            for line in tv.split("\n"):
                line = line.strip()
                if line:
                    L.append("  " + line[:130])
        else:
            L.append("  （此日干+月支组合未收）")

        L.append("")
        L.append("=" * 52)
        L.append("【格局】")
        ge, why = CL.judge_ge(b.day.gan, b.month.zhi, b.month.cang, BZ.shishen)
        L.append("  %s" % ge)
        L.append("  依据：%s" % why)
        hits = CL.ge_explain(ge)
        if hits:
            L.append("")
            L.append("  《子平真诠》相关论述：")
            for title, para in hits:
                L.append("  ▸ %s" % title)
                for line in para.split("\n"):
                    line = line.strip()
                    if line:
                        L.append("    " + line[:120])

        L.append("")
        L.append("=" * 52)
        L.append("【时柱断语】出处：《三命通会》")
        key, duan = CL.shizhu_duan(b.day.gan, b.day.zhi,
                                   b.hour.gan, b.hour.zhi)
        if duan:
            L.append("  查表键：%s" % key)
            L.append("")
            for line in duan.split("\n"):
                line = line.strip()
                if line:
                    L.append("  " + line)
        else:
            L.append("  （此日干+时柱组合在库中未收）")

        L.append("")
        L.append("=" * 52)
        L.append("【本日干其他时柱断语】出处：《三命通会》")
        kw = ge.replace("格", "")
        found = CL.search_shizhu(b.day.gan, None, limit=2)
        if found:
            for src, para in found:
                L.append("  ▸ %s" % src)
                for line in para.split("\n"):
                    line = line.strip()
                    if line:
                        L.append("    " + line[:120])
        else:
            L.append("  （未检索到直接相关段落）")

        L.append("")
        L.append("")
        L.append("=" * 52)
        L.append("【流年】未来 10 年（干支 + 十神）")
        now_y = __import__("datetime").datetime.now().year
        for y, gz in TH.liunian(now_y, 10):
            ss = TH.shishen_of(b.day.gan, gz)
            L.append("  %d  %s  %s" % (y, gz, ss))

        L.append("")
        L.append("【数据库】渊海子平 %d 章 · 子平真诠 %d 章 · 滴天髓 %d 篇 · "
                 "三命通会 %d 条 · 穷通宝鉴 %d 条"
                 % (len(CL.yuanhai_chapters()), len(CL.ziping_chapters()),
                    len(CL.dts_chapters()), len(CL.load_shizhu()),
                    len(TH.load_tiaohou())))
        return "\n".join(L)

    def build_dayun(self, b):
        if not b.dayun:
            return "（无大运数据）"
        L = ["【起运】%s" % b.qiyun_desc, ""]
        L.append("  年龄　　年份　　干支　　十神")
        L.append("  " + "-" * 40)
        for d in b.dayun:
            if not d["ganzhi"]:
                continue
            ss = BZ.shishen(b.day.gan, d["ganzhi"][0])
            L.append("  %2d~%2d 岁　%d　　%s　　%s" % (
                d["start_age"], d["end_age"], d["start_year"], d["ganzhi"], ss))
        return "\n".join(L)

    def build_raw(self, b, a):
        L = []
        L.append("公历：%s" % b.solar.strftime("%Y-%m-%d %H:%M:%S"))
        L.append("农历：%s" % b.lunar_text)
        L.append("真太阳时：%s（经度 %.2f）" % ("开" if b.true_solar else "关", b.longitude))
        L.append("")
        L.append("年柱 %s  十神 %s  藏干 %s" % (b.year.text(), b.year.gan_ss, b.year.cang))
        L.append("月柱 %s  十神 %s  藏干 %s" % (b.month.text(), b.month.gan_ss, b.month.cang))
        L.append("日柱 %s  日主 %s  藏干 %s" % (b.day.text(), b.day.gan, b.day.cang))
        L.append("时柱 %s  十神 %s  藏干 %s" % (b.hour.text(), b.hour.gan_ss, b.hour.cang))
        L.append("")
        L.append("节气：前 %s" % b.jieqi_prev)
        L.append("　　　后 %s" % b.jieqi_next)
        L.append("")
        L.append("五行：%s" % a["五行"])
        L.append("得分：%d　强弱：%s" % (a["得分"], a["强弱"]))
        L.append("喜：%s　忌：%s" % (a["喜神"], a["忌神"]))
        return "\n".join(L)


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    w = Main()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
