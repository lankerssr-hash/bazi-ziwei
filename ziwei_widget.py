# -*- coding: utf-8 -*-
"""紫微斗数面板：4×4 传统盘面 + AI 解盘。"""
import sys

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTextEdit, QTabWidget, QFrame, QSizePolicy, QApplication, QCheckBox,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer

import ziwei_chart as ZW
import sihua as SH
import ai_read as AI

# 粉色主题（跟八字那边统一）
PINK_BG = "#fdf4f9"
PINK_LINE = "#f6d5e8"
PINK_MAIN = "#e84d8a"
PINK_DEEP = "#c2286a"
TEXT_MAIN = "#3d2433"
TEXT_SUB = "#9a7f90"

BRIGHT_COLOR = {
    "庙": "#c2286a", "旺": "#e84d8a", "得": "#d97706",
    "利": "#7c5cae", "平": "#6b7280", "陷": "#9ca3af", "": "#6b7280",
}
MUTAGEN_COLOR = {
    "禄": "#0e9f6e", "权": "#2563eb", "科": "#7c3aed", "忌": "#b91c1c",
}

# 4×4 格子里每个地支的位置（row, col）
GRID_POS = {
    "巳": (0, 0), "午": (0, 1), "未": (0, 2), "申": (0, 3),
    "辰": (1, 0), "酉": (1, 3),
    "卯": (2, 0), "戌": (2, 3),
    "寅": (3, 0), "丑": (3, 1), "子": (3, 2), "亥": (3, 3),
}


class PalaceCell(QFrame):
    """一个宫格 —— 点一下会弹该宫的 AI 解读"""

    def __init__(self, p, on_click=None):
        super().__init__()
        self.palace = p
        self._on_click = on_click
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("点一下，单独解这个宫（%s）" % p.get("name", ""))
        is_soul = p.get("is_soul")
        is_body = p.get("is_body")
        border = "#e84d8a" if is_soul else ("#7c5cae" if is_body else "#f6d5e8")
        w = 2 if (is_soul or is_body) else 1
        self.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #ffffff,stop:1 #fff6fb);"
            "border:%dpx solid %s;border-radius:10px;}"
            "QLabel{border:none;background:transparent;}" % (w, border))
        self.setMinimumSize(150, 120)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(7, 6, 7, 6)
        lay.setSpacing(2)

        # 第一行：宫名 + 干支
        top = QHBoxLayout()
        nm = QLabel(p["name"])
        nm.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        nm.setStyleSheet("color:%s;" % (PINK_DEEP if is_soul else "#6b7280"))
        gz = QLabel(p["stem"] + p["branch"])
        gz.setFont(QFont("Microsoft YaHei", 9))
        gz.setStyleSheet("color:%s;" % TEXT_SUB)
        top.addWidget(nm)
        top.addStretch(1)
        top.addWidget(gz)
        lay.addLayout(top)

        # 主星（大）
        if p["major"]:
            for s in p["major"]:
                row = QHBoxLayout()
                row.setSpacing(3)
                n = QLabel(s["name"])
                n.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
                n.setStyleSheet("color:%s;" % BRIGHT_COLOR.get(s["brightness"], "#111"))
                row.addWidget(n)
                if s["brightness"]:
                    b = QLabel(s["brightness"])
                    b.setFont(QFont("Microsoft YaHei", 8))
                    b.setStyleSheet("color:%s;" % BRIGHT_COLOR.get(s["brightness"], "#999"))
                    row.addWidget(b)
                if s["mutagen"]:
                    h = QLabel(s["mutagen"])
                    h.setFont(QFont("Microsoft YaHei", 8, QFont.Bold))
                    h.setStyleSheet(
                        "color:#fff;background:%s;border-radius:4px;padding:0 3px;"
                        % MUTAGEN_COLOR.get(s["mutagen"], "#666"))
                    row.addWidget(h)
                row.addStretch(1)
                lay.addLayout(row)
        else:
            e = QLabel("（空宫）")
            e.setStyleSheet("color:#c9b2c0;font-size:10px;")
            lay.addWidget(e)

        # 辅星
        if p["minor"]:
            txt = []
            for s in p["minor"]:
                x = s["name"]
                if s["brightness"]:
                    x += s["brightness"]
                if s["mutagen"]:
                    x += "[" + s["mutagen"] + "]"
                txt.append(x)
            m = QLabel(" ".join(txt))
            m.setWordWrap(True)
            m.setStyleSheet("color:#8a6b7c;font-size:9.5px;")
            lay.addWidget(m)

        # 杂曜（小星）
        if p.get("adj"):
            names = [s["name"] for s in p["adj"]]
            a = QLabel(" ".join(names[:10]))
            a.setWordWrap(True)
            a.setStyleSheet("color:#b08aa0;font-size:9px;")
            a.setObjectName("adjrow")
            lay.addWidget(a)

        # 长生 / 博士 十二神
        tw = []
        if p.get("changsheng"):
            tw.append("长生·" + p["changsheng"])
        if p.get("boshi"):
            tw.append("博士·" + p["boshi"])
        if tw:
            w2 = QLabel("　".join(tw))
            w2.setStyleSheet("color:#c9a3b8;font-size:8.5px;")
            lay.addWidget(w2)

        # 大限
        if p["decadal"]:
            d = QLabel("大限 " + p["decadal"])
            d.setStyleSheet("color:#b06a8e;font-size:9px;")
            lay.addWidget(d)
        lay.addStretch(1)

    def trigger(self):
        """被点中（也方便测试直接调）"""
        if self._on_click:
            try:
                self._on_click(self.palace)
            except Exception as ex:
                print("[palace] 点击处理出错:", ex)

    def mousePressEvent(self, e):
        self.trigger()
        if e is not None:
            super().mousePressEvent(e)

    def enterEvent(self, e):
        self.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #fff5fa,stop:1 #ffe3f0);"
            "border:2px solid #ec6fa8;border-radius:10px;}"
            "QLabel{border:none;background:transparent;}")
        super().enterEvent(e)

    def leaveEvent(self, e):
        p = self.palace
        is_soul = p.get("is_soul")
        is_body = p.get("is_body")
        border = "#e84d8a" if is_soul else ("#7c5cae" if is_body else "#f6d5e8")
        w = 2 if (is_soul or is_body) else 1
        self.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #ffffff,stop:1 #fff6fb);"
            "border:%dpx solid %s;border-radius:10px;}"
            "QLabel{border:none;background:transparent;}" % (w, border))
        super().leaveEvent(e)


class ZiweiPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.c = None
        self._box = None
        self._tick = 0
        self._timer = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self.lbl_head = QLabel("紫微斗数 · 还没排盘")
        self.lbl_head.setStyleSheet(
            "color:%s;font-size:12.5px;font-weight:600;" % PINK_DEEP)
        root.addWidget(self.lbl_head)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabWidget::pane{background:#fff;border:2px solid %s;"
            "border-radius:12px;top:-2px;}"
            "QTabBar::tab{background:#ffe9f3;color:#b06a8e;padding:6px 14px;"
            "margin-right:3px;border-top-left-radius:10px;"
            "border-top-right-radius:10px;font-size:12px;}"
            "QTabBar::tab:selected{background:#fff;color:%s;font-weight:600;"
            "border:2px solid %s;border-bottom:none;}"
            % (PINK_LINE, PINK_DEEP, PINK_LINE))

        # 盘面
        self.gridw = QWidget()
        self.grid = QGridLayout(self.gridw)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.grid.setSpacing(6)
        self.center = None
        self.tabs.addTab(self.gridw, "命盘")

        # AI
        self.aw = QWidget()
        av = QVBoxLayout(self.aw)
        av.setContentsMargins(6, 6, 6, 6)
        av.setSpacing(6)
        bar = QHBoxLayout()
        bar.setSpacing(6)
        self.btns = []
        for nm in ("命格", "事业", "财帛", "感情", "相貌", "大限", "流年"):
            b = QPushButton(nm)
            b.setStyleSheet(
                "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 #fff0f7,stop:1 #ffd9ea);color:%s;"
                "border:1.5px solid #f7bfd9;border-radius:12px;"
                "padding:6px 14px;font-size:12.5px;font-weight:600;}"
                "QPushButton:hover{background:#ffc4de;}"
                "QPushButton:disabled{background:#fdf4f9;color:#d9c3d0;"
                "border-color:#f6e5ee;}" % PINK_DEEP)
            b.setEnabled(False)
            b.clicked.connect(lambda _=False, n=nm: self.ask(n))
            self.btns.append(b)
            bar.addWidget(b)
        bar.addStretch(1)
        self.lbl_ai = QLabel("")
        self.lbl_ai.setStyleSheet("color:%s;font-size:11.5px;" % TEXT_SUB)
        bar.addWidget(self.lbl_ai)
        av.addLayout(bar)
        self.txt_ai = QTextEdit()
        self.txt_ai.setReadOnly(True)
        self.txt_ai.setFont(QFont("Microsoft YaHei", 10.5))
        self.txt_ai.setStyleSheet("border:none;padding:10px;background:#fff;")
        av.addWidget(self.txt_ai, 1)
        self.tabs.addTab(self.aw, "AI 解盘")

        # 四化飞星
        self.txt_fx = QTextEdit()
        self.txt_fx.setReadOnly(True)
        self.txt_fx.setFont(QFont("Consolas", 9.5))
        self.txt_fx.setStyleSheet("border:none;padding:10px;background:#fefbfd;")
        self.tabs.addTab(self.txt_fx, "四化飞星")

        # 原始
        self.txt_raw = QTextEdit()
        self.txt_raw.setReadOnly(True)
        self.txt_raw.setFont(QFont("Consolas", 9.5))
        self.txt_raw.setStyleSheet("border:none;padding:10px;background:#fefbfd;")
        self.tabs.addTab(self.txt_raw, "原始数据")

        # 开关：显示小星
        bar = QHBoxLayout()
        self.chk_small = QCheckBox("显示小星（杂曜·十二神）")
        self.chk_small.setChecked(True)
        self.chk_small.setStyleSheet("QCheckBox{color:#9a7f90;font-size:11px;}")
        self.chk_small.toggled.connect(self.toggle_small)
        bar.addStretch(1)
        bar.addWidget(self.chk_small)
        root.addLayout(bar)

        root.addWidget(self.tabs, 1)

    # ---------- 排盘 ----------
    def set_chart(self, c):
        self.c = c
        self.lbl_head.setText(
            "紫微：%s　命宫%s%s　%s　%s" % (
                c["chinese_date"], c["soul_palace_stem"],
                c["soul_palace_branch"], c["five_elements_class"],
                c["time"]))
        self.txt_raw.setPlainText(ZW.full_text(c))
        self.fx = SH.feixing(c)
        self.txt_fx.setPlainText(SH.text_of(c, self.fx))
        self.build_grid(c)
        for b in self.btns:
            b.setEnabled(True)

    def toggle_small(self, on):
        """显隐小星：把带 adjrow 的标签和十二神标签藏起来"""
        for i in range(self.grid.count()):
            w = self.grid.itemAt(i).widget()
            if w is None:
                continue
            for lab in w.findChildren(QLabel):
                txt = lab.text()
                is_adj = lab.objectName() == "adjrow"
                is_12 = txt.startswith("长生·") or ("博士·" in txt)
                if is_adj or is_12:
                    lab.setVisible(bool(on))

    def build_grid(self, c):
        # 清空
        while self.grid.count():
            it = self.grid.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        cells = {}
        for p in c["palaces"]:
            br = p["branch"]
            if br in GRID_POS:
                cells[br] = p

        for br, p in cells.items():
            r, col = GRID_POS[br]
            self.grid.addWidget(PalaceCell(p, on_click=self.ask_palace),
                                 r, col)

        # 中央信息块
        mid = QFrame()
        mid.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #ffffff,stop:1 #ffeef7);"
            "border:2px solid %s;border-radius:14px;}"
            "QLabel{border:none;background:transparent;}" % PINK_LINE)
        mv = QVBoxLayout(mid)
        mv.setContentsMargins(10, 10, 10, 10)
        mv.setSpacing(4)
        t = QLabel(c["chinese_date"])
        t.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        t.setStyleSheet("color:%s;" % PINK_DEEP)
        t.setAlignment(Qt.AlignCenter)
        mv.addWidget(t)
        for line in (
            c["lunar_date"],
            c["time"] + "（" + c["time_range"] + "）",
            "命主 %s　身主 %s" % (c["soul"], c["body"]),
            "五行局 %s" % c["five_elements_class"],
            "命宫 %s%s　身宫 %s" % (c["soul_palace_stem"],
                                    c["soul_palace_branch"],
                                    c["body_palace_branch"]),
            "%s　生肖%s" % (c["sign"], c["zodiac"]),
        ):
            l = QLabel(line)
            l.setAlignment(Qt.AlignCenter)
            l.setStyleSheet("color:%s;font-size:11px;" % TEXT_SUB)
            mv.addWidget(l)
        mv.addStretch(1)
        self.grid.addWidget(mid, 1, 1, 2, 2)

        for i in range(4):
            self.grid.setRowStretch(i, 1)
            self.grid.setColumnStretch(i, 1)

    # ---------- AI ----------
    def ask(self, section):
        if not self.c:
            return
        self.tabs.setCurrentWidget(self.aw)
        for b in self.btns:
            b.setEnabled(False)
        self.lbl_ai.setText("正在解「%s」…" % section)
        self.txt_ai.setPlainText("正在解「%s」……" % section)

        prompt = (ZW.full_text(self.c)
                  + "\n\n" + SH.text_of(self.c, getattr(self, "fx", None)))
        self._box = {}
        self._tick = 0
        self._section = section
        AI.ask(prompt, None, None, box=self._box,
               prompt=AI.ziwei_prompt(section))

        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.setInterval(400)
            self._timer.timeout.connect(self._poll)
        self._timer.start()

    def ask_palace(self, p):
        """点宫 → 弹窗单独解这一宫"""
        if not self.c:
            return
        if getattr(self, "_popup", None) is None:
            self._popup = PalacePopup(self)
        self._popup.start(p, self.c)

    def _poll(self):
        box = self._box
        if box is None:
            return
        self._tick += 1
        if "ok" in box:
            self._timer.stop()
            self.txt_ai.setPlainText(box["ok"])
            for b in self.btns:
                b.setEnabled(True)
            self.lbl_ai.setText("「%s」完成" % getattr(self, "_section", ""))
            self._box = None
        elif "fail" in box:
            self._timer.stop()
            self.txt_ai.setPlainText("紫微解盘失败：\n\n" + str(box["fail"]))
            for b in self.btns:
                b.setEnabled(True)
            self._box = None
        elif self._tick > 900:
            self._timer.stop()
            self.txt_ai.setPlainText("超时（6 分钟）。检查 8787 转发站。")
            for b in self.btns:
                b.setEnabled(True)
            self._box = None


class PalacePopup(QWidget):
    """单宫解读弹窗"""

    def __init__(self, panel):
        super().__init__(None, Qt.Window)
        self.panel = panel
        self.resize(680, 620)
        self.setStyleSheet(
            "QWidget{background:%s;color:%s;}"
            "QLabel{background:transparent;}" % (PINK_BG, TEXT_MAIN))
        self._box = None
        self._tick = 0
        self._timer = None
        self._p = None

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(6)

        self.title = QLabel("宫位解读")
        self.title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.title.setStyleSheet("color:%s;" % PINK_DEEP)
        v.addWidget(self.title)

        self.sub = QLabel("")
        self.sub.setStyleSheet("color:%s;font-size:11.5px;" % TEXT_SUB)
        v.addWidget(self.sub)

        self.fxline = QLabel("")
        self.fxline.setWordWrap(True)
        self.fxline.setStyleSheet("color:#9a7f90;font-size:10.5px;")
        v.addWidget(self.fxline)

        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setFont(QFont("Microsoft YaHei", 10.5))
        self.txt.setStyleSheet(
            "QTextEdit{background:#fff;border:2px solid %s;border-radius:12px;"
            "padding:12px;}" % PINK_LINE)
        v.addWidget(self.txt, 1)

        bar = QHBoxLayout()
        self.btn_copy = QPushButton("复制")
        self.btn_copy.setStyleSheet(
            "QPushButton{background:#fff0f7;color:%s;"
            "border:1.5px solid #f7bfd9;border-radius:10px;padding:6px 16px;}"
            % PINK_DEEP)
        self.btn_copy.clicked.connect(self.do_copy)
        self.btn_again = QPushButton("再解一次")
        self.btn_again.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #b06ab3,stop:1 #ec6fa8);color:#fff;border:none;"
            "border-radius:10px;padding:6px 16px;}")
        self.btn_again.clicked.connect(lambda: self.start(self._p, self.panel.c))
        self.lbl = QLabel("")
        self.lbl.setStyleSheet("color:%s;font-size:11.5px;" % TEXT_SUB)
        btn_close = QPushButton("关闭")
        btn_close.setStyleSheet(
            "QPushButton{background:#26324a;color:#fff;border:none;"
            "border-radius:10px;padding:6px 16px;}")
        btn_close.clicked.connect(self.hide)
        bar.addWidget(self.btn_copy)
        bar.addWidget(self.btn_again)
        bar.addWidget(self.lbl, 1)
        bar.addWidget(btn_close)
        v.addLayout(bar)

    def start(self, p, c):
        if not p:
            return
        self._p = p
        self.setWindowTitle("✿ %s ✿" % p["name"])
        self.title.setText("%s　%s%s" % (p["name"], p["stem"], p["branch"]))
        stars = []
        for s2 in p["major"]:
            x = s2["name"]
            if s2["brightness"]:
                x += "(" + s2["brightness"] + ")"
            if s2["mutagen"]:
                x += "[" + s2["mutagen"] + "]"
            stars.append(x)
        self.sub.setText("主星：%s　｜　辅星：%s" % (
            " ".join(stars) or "空宫",
            " ".join(s2["name"] for s2 in p["minor"]) or "—"))
        try:
            _t = SH.one_palace_text(c, p["name"],
                                    getattr(self.panel, "fx", None))
            self.fxline.setText("本宫四化：" + (_t.replace("\n", "　") if _t else "—"))
        except Exception:
            self.fxline.setText("")
        self.txt.setPlainText("正在解「%s」……" % p["name"])
        self.lbl.setText("请求中")
        self.show()
        self.raise_()
        self.activateWindow()

        try:
            _fx = SH.one_palace_text(c, p["name"],
                                     getattr(self.panel, "fx", None))
        except Exception:
            _fx = ""
        prompt = (ZW.full_text(c)
                  + "\n\n" + SH.text_of(c, getattr(self.panel, "fx", None))
                  + "\n\n【本宫的四化飞星】\n" + (_fx or "（无）")
                  + "\n\n★★★★ 这次只解【%s】，别的宫一律不要展开讲。★★★★\n"
                  % p["name"])
        self._box = {}
        self._tick = 0
        AI.ask(prompt, None, None, box=self._box, prompt=AI.palace_prompt())
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
            self.txt.setPlainText(box["ok"])
            self.lbl.setText("%d 字" % len(box["ok"]))
            self._box = None
        elif "fail" in box:
            self._timer.stop()
            self.txt.setPlainText("解盘失败：\n\n" + str(box["fail"]))
            self.lbl.setText("失败")
            self._box = None
        elif self._tick > 600:
            self._timer.stop()
            self.txt.setPlainText("超时。检查 8787 转发站。")
            self._box = None

    def do_copy(self):
        QApplication.clipboard().setText(self.txt.toPlainText())
        self.lbl.setText("已复制")
