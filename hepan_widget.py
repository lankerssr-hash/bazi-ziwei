# -*- coding: utf-8 -*-
"""合盘窗口：输入两个生日，出合盘指标 + AI 解读。"""
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QSpinBox, QCheckBox, QTextEdit, QFrame,
    QTabWidget, QApplication,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer

import bazi as BZ
import hepan as HP
import hepan_view as HV
import cases as CS
import ai_read as AI

PINK_BG = "#fdf4f9"
PINK_LINE = "#f6d5e8"
PINK_MAIN = "#e84d8a"
PINK_DEEP = "#c2286a"
TEXT_MAIN = "#3d2433"
TEXT_SUB = "#9a7f90"


class PersonBox(QFrame):
    """一个人的生日输入"""

    def __init__(self, title, gender="女"):
        super().__init__()
        self.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #ffffff,stop:1 #fff3f9);"
            "border:2px solid %s;border-radius:14px;}"
            "QLabel{background:transparent;}" % PINK_LINE)
        g = QGridLayout(self)
        g.setContentsMargins(10, 8, 10, 8)
        g.setHorizontalSpacing(8)

        t = QLabel(title)
        t.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        t.setStyleSheet("color:%s;" % PINK_DEEP)
        g.addWidget(t, 0, 0, 1, 4)

        self.ed_name = QLineEdit("人一" if "一" in title else "人二")
        self.ed_name.setMaximumWidth(110)
        self.cb_gender = QComboBox()
        self.cb_gender.addItems(["女", "男"])
        self.cb_gender.setCurrentText(gender)
        self.cb_gender.setMaximumWidth(66)

        self.sy = QSpinBox(); self.sy.setRange(1900, 2100); self.sy.setValue(2002)
        self.sm = QSpinBox(); self.sm.setRange(1, 12); self.sm.setValue(3)
        self.sd = QSpinBox(); self.sd.setRange(1, 31); self.sd.setValue(17)
        self.sh = QSpinBox(); self.sh.setRange(0, 23); self.sh.setValue(16)
        self.smi = QSpinBox(); self.smi.setRange(0, 59); self.smi.setValue(15)
        for w in (self.sy, self.sm, self.sd, self.sh, self.smi):
            w.setMaximumWidth(70)

        self.chk = QCheckBox("真太阳时")
        self.chk.setChecked(True)

        # 命例下拉
        g.addWidget(QLabel("命例"), 1, 0)
        self.cb_case = QComboBox()
        self.cb_case.addItem("（手动输入）", None)
        self.cb_case.setMinimumWidth(230)
        self.cb_case.currentIndexChanged.connect(self._pick_case)
        g.addWidget(self.cb_case, 1, 1, 1, 3)

        g.addWidget(QLabel("姓名"), 2, 0)
        g.addWidget(self.ed_name, 2, 1)
        g.addWidget(QLabel("性别"), 2, 2)
        g.addWidget(self.cb_gender, 2, 3)

        row = QHBoxLayout()
        row.setSpacing(5)
        for w in (self.sy, self.sm, self.sd):
            row.addWidget(w)
        row.addWidget(QLabel("时"))
        row.addWidget(self.sh)
        row.addWidget(QLabel("分"))
        row.addWidget(self.smi)
        row.addWidget(self.chk)
        w = QWidget(); w.setLayout(row)
        g.addWidget(w, 3, 0, 1, 4)

        self.lbl = QLabel("")
        self.lbl.setStyleSheet("color:%s;font-size:11.5px;" % TEXT_SUB)
        g.addWidget(self.lbl, 4, 0, 1, 4)

    def refresh_cases(self):
        cur = self.cb_case.currentData()
        self.cb_case.blockSignals(True)
        self.cb_case.clear()
        self.cb_case.addItem("（手动输入）", None)
        for i, c in enumerate(CS.all_cases()):
            self.cb_case.addItem(
                "%s %s  %04d-%02d-%02d %02d:%02d" % (
                    c.get("name", "?"), c.get("gender", ""),
                    c.get("year", 0), c.get("month", 0), c.get("day", 0),
                    c.get("hour", 0), c.get("minute", 0)), i)
        self.cb_case.blockSignals(False)
        if cur is not None:
            k = self.cb_case.findData(cur)
            if k >= 0:
                self.cb_case.setCurrentIndex(k)

    def _pick_case(self):
        idx = self.cb_case.currentData()
        if idx is None:
            return
        items = CS.all_cases()
        if not (0 <= idx < len(items)):
            return
        c = items[idx]
        dt = datetime(c.get("year", 2002), c.get("month", 1),
                      c.get("day", 1), c.get("hour", 0), c.get("minute", 0))
        self.set_value(c.get("name", "命主"), c.get("gender", "女"), dt,
                       bool(c.get("true_solar", True)))

    def value(self):
        return (self.ed_name.text().strip() or "命主",
                self.cb_gender.currentText(),
                datetime(self.sy.value(), self.sm.value(), self.sd.value(),
                         self.sh.value(), self.smi.value()),
                self.chk.isChecked())

    def set_value(self, name, gender, dt, true_solar=True):
        self.ed_name.setText(name)
        self.cb_gender.setCurrentText(gender)
        self.sy.setValue(dt.year)
        self.sm.setValue(dt.month)
        self.sd.setValue(dt.day)
        self.sh.setValue(dt.hour)
        self.smi.setValue(dt.minute)
        self.chk.setChecked(true_solar)


class HepanWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.Window)
        self.setWindowTitle("✿ 八字合盘 ✿")
        self.resize(1120, 900)
        self.setStyleSheet("QWidget{background:%s;color:%s;}"
                           "QLabel{background:transparent;}" % (PINK_BG, TEXT_MAIN))
        self._r = None
        self._box = None
        self._tick = 0
        self._timer = None

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # 两个人生日
        row = QHBoxLayout()
        row.setSpacing(8)
        self.p1 = PersonBox("人一", "女")
        self.p2 = PersonBox("人二", "男")
        row.addWidget(self.p1)
        row.addWidget(self.p2)
        root.addLayout(row)

        bar = QHBoxLayout()
        self.btn = QPushButton("算合盘")
        self.btn.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #f06292,stop:1 #e84d8a);color:#fff;border:none;"
            "border-radius:12px;padding:9px 22px;font-weight:600;}"
            "QPushButton:hover{background:#d81b60;}")
        self.btn_ai = QPushButton("AI 解读这段关系")
        self.btn_ai.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #b06ab3,stop:1 #ec6fa8);color:#fff;border:none;"
            "border-radius:12px;padding:9px 22px;font-weight:600;}"
            "QPushButton:hover{background:#a05aa3;}"
            "QPushButton:disabled{background:#efe2ea;color:#c9b2c0;}")
        self.btn_ai.setEnabled(False)
        self.lbl = QLabel("填两个生日，点「算合盘」")
        self.lbl.setStyleSheet("color:%s;font-size:12px;" % TEXT_SUB)
        self.cb_me = QComboBox()
        self.cb_me.addItems(["我是旁观者", "我是人一", "我是人二"])
        self.cb_me.setMinimumWidth(130)
        self.cb_me.setStyleSheet(
            "QComboBox{background:#fff;border:1.5px solid #f7bfd9;"
            "border-radius:10px;padding:5px 8px;color:#c2286a;}")
        bar.addWidget(QLabel("身份"))
        bar.addWidget(self.cb_me)
        bar.addWidget(self.btn)
        bar.addWidget(self.btn_ai)
        bar.addWidget(self.lbl, 1)
        root.addLayout(bar)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabWidget::pane{background:#fff;border:2px solid %s;"
            "border-radius:12px;top:-2px;}"
            "QTabBar::tab{background:#ffe9f3;color:#b06a8e;padding:7px 18px;"
            "margin-right:3px;border-top-left-radius:10px;"
            "border-top-right-radius:10px;font-size:12.5px;}"
            "QTabBar::tab:selected{background:#fff;color:%s;font-weight:600;"
            "border:2px solid %s;border-bottom:none;}" % (PINK_LINE, PINK_DEEP, PINK_LINE))

        self.txt = QTextEdit(); self.txt.setReadOnly(True)
        self.txt.setFont(QFont("Microsoft YaHei", 11))
        self.txt.setStyleSheet("border:none;padding:12px;background:#fff;")
        self.tabs.addTab(self.txt, "合盘指标")

        # ---- 视角页 ----
        self.pv = QWidget()
        pv = QVBoxLayout(self.pv)
        pv.setContentsMargins(8, 8, 8, 8)
        pv.setSpacing(6)
        bar2 = QHBoxLayout()
        bar2.setSpacing(8)
        self.cb_dir = QComboBox()
        self.cb_dir.addItems([
            "我看对方",
            "对方看我",
            "两个方向都写",
        ])
        self.cb_dir.setMinimumWidth(180)
        bar2.addWidget(QLabel("视角"))
        bar2.addWidget(self.cb_dir)
        self.btn_pv = QPushButton("从他/她的角度看对方")
        self.btn_pv.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #0e9f6e,stop:1 #0b7a54);color:#fff;border:none;"
            "border-radius:12px;padding:8px 20px;font-weight:600;}"
            "QPushButton:hover{background:#0b6b4a;}"
            "QPushButton:disabled{background:#e6efe9;color:#9fb3a8;}")
        self.btn_pv.setEnabled(False)
        self.lbl_pv = QLabel("先算合盘")
        self.lbl_pv.setStyleSheet("color:%s;font-size:11.5px;" % TEXT_SUB)
        bar2.addWidget(self.btn_pv)
        bar2.addWidget(self.lbl_pv, 1)
        pv.addLayout(bar2)
        self.txt_pv = QTextEdit()
        self.txt_pv.setReadOnly(True)
        self.txt_pv.setFont(QFont("Microsoft YaHei", 11))
        self.txt_pv.setStyleSheet("border:none;padding:12px;background:#fff;")
        pv.addWidget(self.txt_pv, 1)
        self.tabs.addTab(self.pv, "视角")

        self.txt_ai = QTextEdit(); self.txt_ai.setReadOnly(True)
        self.txt_ai.setFont(QFont("Microsoft YaHei", 11))
        self.txt_ai.setStyleSheet("border:none;padding:12px;background:#fff;")
        self.tabs.addTab(self.txt_ai, "AI 解读")

        root.addWidget(self.tabs, 1)

        self.p1.refresh_cases()
        self.p2.refresh_cases()

        self.btn.clicked.connect(self.run)
        self.btn_ai.clicked.connect(self.ask_ai)
        self.btn_pv.clicked.connect(self.run_pv)
        self.cb_me.currentIndexChanged.connect(self._re_render)

    def run(self):
        n1, g1, d1, ts1 = self.p1.value()
        n2, g2, d2, ts2 = self.p2.value()
        try:
            b1 = BZ.paipan(d1, g1, n1, true_solar=ts1, longitude=114.06)
            b2 = BZ.paipan(d2, g2, n2, true_solar=ts2, longitude=114.06)
        except Exception as e:
            self.txt.setPlainText("排盘失败：%s" % e)
            return
        self.b1, self.b2 = b1, b2
        # 选了身份就用「我／对方」当显示名，判定里的「我」才真的指你
        _t = self.cb_me.currentText()
        _n1, _n2 = b1.name, b2.name
        if _t.endswith("人二"):
            b1.name, b2.name = "对方", "我"
            r = HP.compute(b2, b1)
        elif _t.endswith("人一"):
            b1.name, b2.name = "我", "对方"
            r = HP.compute(b1, b2)
        else:
            r = HP.compute(b1, b2)
        # 算完把名字还回去，免得影响别的功能
        b1.name, b2.name = _n1, _n2
        self._r = r
        self.p1.lbl.setText("%s %s %s %s" % (b1.year.text(), b1.month.text(),
                                             b1.day.text(), b1.hour.text()))
        self.p2.lbl.setText("%s %s %s %s" % (b2.year.text(), b2.month.text(),
                                             b2.day.text(), b2.hour.text()))
        self.txt.setPlainText(self._render(r))
        self.btn_ai.setEnabled(True)
        self.btn_pv.setEnabled(True)
        self.lbl_pv.setText("可以了，选个方向")
        self.lbl.setText("粗估 %d / 100" % r["粗估"])

    def who(self):
        """返回 (我, 对方) 的 (名字, 盘)"""
        a = (self.p1.value(), getattr(self, "b1", None))
        b = (self.p2.value(), getattr(self, "b2", None))
        t = self.cb_me.currentText()
        if t.endswith("人二"):
            return b, a
        if t.endswith("人一"):
            return a, b
        return None, None

    def role_block(self):
        me, other = self.who()
        if me is None or me[1] is None or other[1] is None:
            return ("★ 称呼约定：这是旁观视角，提到两个人时用「人一」「人二」，"
                    "或者按性别用「他」「她」。\n")
        n_me = me[0][0]
        b_me = me[1]
        b_ot = other[1]
        pr = "她" if b_ot.gender == "女" else "他"
        return ("★★★★ 称呼约定（最重要，不许违反）★★★★\n"
                "★ 读这段话的人就是「%s」（%s命）。\n"
                "★ 所以全文用【「我」】指这个人，用【「对方」】指另一个人。\n"
                "★ 需要区分性别时，对方可以用「%s」，但主称呼一律用「对方」。\n"
                "★ 不许写成「他觉得你怎样」这种旁观转述，要像在跟本人说话。\n"
                "★ 也不许把两个人叫成「人一」「人二」。\n" % (
                    n_me, b_me.gender, pr))

    def run_pv(self):
        if not getattr(self, "b1", None):
            return
        self.tabs.setCurrentWidget(self.pv)
        d = self.cb_dir.currentText()
        me, other = self.who()
        if me is None:
            me, other = (self.p1.value(), self.b1), (self.p2.value(), self.b2)
        parts = []
        if d.startswith("我看对方"):
            parts.append(HV.perspective(me[1], other[1]))
        elif d.startswith("对方看我"):
            parts.append(HV.perspective(other[1], me[1]))
        else:
            parts.append(HV.perspective(me[1], other[1]))
            parts.append("")
            parts.append("=" * 40)
            parts.append("")
            parts.append(HV.perspective(other[1], me[1]))
        self.txt_pv.setPlainText("正在分析……")
        self.lbl_pv.setText("请求中")
        self.btn_pv.setEnabled(False)
        self._pvbox = {}
        self._pvtick = 0
        AI.ask("\n".join(parts), None, None, box=self._pvbox,
               prompt=AI.perspective_prompt())
        if getattr(self, "_pvtimer", None) is None:
            self._pvtimer = QTimer(self)
            self._pvtimer.setInterval(400)
            self._pvtimer.timeout.connect(self._poll_pv)
        self._pvtimer.start()

    def _poll_pv(self):
        box = getattr(self, "_pvbox", None)
        if box is None:
            return
        self._pvtick += 1
        if "ok" in box:
            self._pvtimer.stop()
            self.txt_pv.setPlainText(box["ok"])
            _b = box.get("bad_clauses")
            self.lbl_pv.setText("%d 字%s" % (
                len(box["ok"]), ("　断句超标 %d 处" % _b) if _b else ""))
            self.btn_pv.setEnabled(True)
            self._pvbox = None
        elif "fail" in box:
            self._pvtimer.stop()
            self.txt_pv.setPlainText("失败：\n\n" + str(box["fail"]))
            self.btn_pv.setEnabled(True)
            self._pvbox = None
        elif self._pvtick > 900:
            self._pvtimer.stop()
            self.txt_pv.setPlainText("超时。")
            self.btn_pv.setEnabled(True)
            self._pvbox = None

    def _render(self, r):
        L = []
        _t = self.cb_me.currentText()
        if _t.endswith("人二"):
            L.append("我：%s" % r["人一"])       # compute 时已把 b2 放在第一位
            L.append("对方：%s" % r["人二"])
        elif _t.endswith("人一"):
            L.append("我：%s" % r["人一"])
            L.append("对方：%s" % r["人二"])
        else:
            L.append("人一：%s" % r["人一"])
            L.append("人二：%s" % r["人二"])
        L.append("")
        L.append("═" * 50)
        for name, verdict, desc in r["细节"]:
            L.append("▸ %s" % name)
            L.append("   判定：%s" % verdict)
            L.append("   %s" % desc)
            L.append("")
        L.append("═" * 50)
        _t = self.cb_me.currentText()
        if _t.endswith("人二"):
            _a, _b = "我", "对方"
        elif _t.endswith("人一"):
            _a, _b = "我", "对方"
        else:
            _a, _b = "人一", "人二"
        if _t.endswith("人二"):
            # compute 时把 b2 放在第一位了，所以一/二 要反过来标
            _a, _b = "我", "对方"
        L.append("用神对照（这一层最关键）：")
        L.append("   %s  喜 %s    忌 %s" % (
            _a, "、".join(r["用神"]["一人喜"]), "、".join(r["用神"]["一人忌"])))
        L.append("   %s  喜 %s    忌 %s" % (
            _b, "、".join(r["用神"]["二人喜"]), "、".join(r["用神"]["二人忌"])))
        if r["用神"]["冲突"]:
            L.append("")
            L.append("   ★ 冲突：")
            for c in r["用神"]["冲突"]:
                L.append("     · " + c)
        if r["用神"]["共喜"]:
            L.append("")
            L.append("   ★ 共喜：")
            for c in r["用神"]["共喜"]:
                L.append("     · " + c)
        L.append("")
        L.append("═" * 50)
        L.append("粗估 %d / 100" % r["粗估"])
        L.append("   %s" % r["粗估说明"])
        return "\n".join(L)

    def _re_render(self):
        if getattr(self, "_r", None):
            self.txt.setPlainText(self._render(self._r))

    def ask_ai(self):
        if not self._r:
            return
        self.tabs.setCurrentWidget(self.txt_ai)
        self.btn_ai.setEnabled(False)
        self.txt_ai.setPlainText("正在解读……")
        self.lbl.setText("AI 解读中…")

        _rb = self.role_block() if hasattr(self, "role_block") else ""
        prompt = (_rb + HP.text_of(self._r)
                  + "\n\n两个人各自的八字摘要：\n"
                  + "人一：" + self._r["人一"] + "\n"
                  + "人二：" + self._r["人二"] + "\n")
        self._box = {}
        self._tick = 0
        AI.ask(prompt, None, None, box=self._box, prompt=AI.hepan_prompt())
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.setInterval(400)
            self._timer.timeout.connect(self._poll)
        self._timer.start()

    def _poll(self):
        box = self._box
        if box is None:
            return
        self._tick += 1
        if "ok" in box:
            self._timer.stop()
            self.txt_ai.setPlainText(box["ok"])
            self.lbl.setText("%d 字" % len(box["ok"]))
            self.btn_ai.setEnabled(True)
            self._box = None
        elif "fail" in box:
            self._timer.stop()
            self.txt_ai.setPlainText("解读失败：\n\n" + str(box["fail"]))
            self.btn_ai.setEnabled(True)
            self._box = None
        elif self._tick > 900:
            self._timer.stop()
            self.txt_ai.setPlainText("超时。检查 8787 转发站。")
            self._box = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    w = HepanWindow()
    w.show()
    sys.exit(app.exec())
