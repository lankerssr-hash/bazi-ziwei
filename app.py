# -*- coding: utf-8 -*-
"""八字 + 紫微 双模块合并窗口。

左边：子平八字（复用 bazi_gui.Main，把它的输入行藏起来）
右边：紫微斗数（ziwei_widget.ZiweiPanel）
底部：八字 × 紫微 交叉分析
顶部：共用一个生日输入
"""
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox, QCheckBox,
    QTextEdit, QSplitter, QFrame,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer

import bazi as BZ
import classics as CL
import tiaohou as TH
import ai_read as AI
import ziwei_chart as ZW
import cases as CS
from bazi_gui import Main as BaziMain
from ziwei_widget import ZiweiPanel
from hepan_widget import HepanWindow

PINK_BG = "#fdf4f9"
PINK_LINE = "#f6d5e8"
PINK_MAIN = "#e84d8a"
PINK_DEEP = "#c2286a"
TEXT_MAIN = "#3d2433"
TEXT_SUB = "#9a7f90"


class CrossPanel(QWidget):
    """底部：交叉分析结果"""

    def __init__(self):
        super().__init__()
        self._box = None
        self._tick = 0
        self._timer = None
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(5)

        bar = QHBoxLayout()
        t = QLabel("★ 八字 × 紫微 交叉分析")
        t.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        t.setStyleSheet("color:%s;" % PINK_DEEP)
        bar.addWidget(t)
        self.lbl = QLabel("")
        self.lbl.setStyleSheet("color:%s;font-size:11.5px;" % TEXT_SUB)
        bar.addWidget(self.lbl, 1)
        self.btn_copy = QPushButton("复制")
        self.btn_copy.setStyleSheet(
            "QPushButton{background:#fff0f7;color:%s;border:1.5px solid #f7bfd9;"
            "border-radius:10px;padding:5px 14px;}" % PINK_DEEP)
        self.btn_copy.clicked.connect(self.do_copy)
        bar.addWidget(self.btn_copy)
        v.addLayout(bar)

        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setFont(QFont("Microsoft YaHei", 10.5))
        self.txt.setStyleSheet(
            "QTextEdit{background:#fff;border:2px solid %s;border-radius:12px;"
            "padding:10px;}" % PINK_LINE)
        self.txt.setPlainText(
            "点上面的「★ 交叉分析」——\n\n"
            "它会同时读八字盘和紫微盘，然后告诉你：\n"
            "① 两套都指向同一方向的有哪些（可信度最高）\n"
            "② 两套说法冲突的有哪些，为什么冲突\n"
            "③ 只在一套里出现的重要补充\n"
            "④ 综合结论：最强的优势、最该防的坑、未来三年")
        v.addWidget(self.txt, 1)

    def do_copy(self):
        QApplication.clipboard().setText(self.txt.toPlainText())
        self.lbl.setText("已复制")

    def start(self, prompt_text):
        self.txt.setPlainText("正在分析…… 约 10~20 秒")
        self.lbl.setText("请求中")
        self._box = {}
        self._tick = 0
        AI.ask(prompt_text, None, None, box=self._box,
               prompt=AI.cross_prompt())
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
            self.txt.setPlainText("交叉分析失败：\n\n" + str(box["fail"]))
            self.lbl.setText("失败")
            self._box = None
        elif self._tick > 1200:
            self._timer.stop()
            self.txt.setPlainText("超时。检查 8787 转发站。")
            self._box = None


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("✿ 八字 · 紫微 ✿")
        self.resize(1780, 1040)
        self.setStyleSheet("QWidget{background:%s;color:%s;}"
                           "QLabel{background:transparent;}"
                           % (PINK_BG, TEXT_MAIN))

        self.ziwei_data = None
        self.bazi = None
        self.an = None

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # ---------- 共用输入 ----------
        box = QFrame()
        box.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #ffffff,stop:0.5 #fff8fc,stop:1 #ffeef7);"
            "border:2px solid %s;border-radius:16px;}"
            "QLabel{background:transparent;}" % PINK_LINE)
        g = QGridLayout(box)
        g.setContentsMargins(12, 10, 12, 10)
        g.setHorizontalSpacing(10)

        self.ed_name = QLineEdit("命主")
        self.ed_name.setMaximumWidth(120)
        self.cb_gender = QComboBox()
        self.cb_gender.addItems(["女", "男"])
        self.cb_gender.setMaximumWidth(70)
        self.cb_city = QComboBox()
        for c in ("深圳 114.06", "北京 116.41", "上海 121.47", "广州 113.26",
                  "成都 104.07", "杭州 120.16", "武汉 114.31", "西安 108.94",
                  "香港 114.17", "台北 121.52"):
            self.cb_city.addItem(c)
        self.cb_city.setMaximumWidth(150)
        self.chk_true = QCheckBox("真太阳时")
        self.chk_true.setChecked(True)

        self.sp_y = QSpinBox(); self.sp_y.setRange(1900, 2100); self.sp_y.setValue(2002)
        self.sp_m = QSpinBox(); self.sp_m.setRange(1, 12); self.sp_m.setValue(3)
        self.sp_d = QSpinBox(); self.sp_d.setRange(1, 31); self.sp_d.setValue(17)
        self.sp_h = QSpinBox(); self.sp_h.setRange(0, 23); self.sp_h.setValue(16)
        self.sp_mi = QSpinBox(); self.sp_mi.setRange(0, 59); self.sp_mi.setValue(15)
        for w in (self.sp_y, self.sp_m, self.sp_d, self.sp_h, self.sp_mi):
            w.setMaximumWidth(74)

        self.btn_bazi = QPushButton("排八字")
        self.btn_ziwei = QPushButton("排紫微")
        self.btn_cross = QPushButton("★ 交叉分析")
        self.btn_bazi.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #f06292,stop:1 #e84d8a);color:#fff;border:none;"
            "border-radius:12px;padding:9px 18px;font-weight:600;}"
            "QPushButton:hover{background:#d81b60;}")
        self.btn_ziwei.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #b06ab3,stop:1 #8e5cab);color:#fff;border:none;"
            "border-radius:12px;padding:9px 18px;font-weight:600;}"
            "QPushButton:hover{background:#7c4a96;}")
        self.btn_cross.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #d97706,stop:1 #b45309);color:#fff;border:none;"
            "border-radius:12px;padding:9px 18px;font-weight:600;}"
            "QPushButton:hover{background:#92400e;}"
            "QPushButton:disabled{background:#e5e7eb;color:#9ca3af;}")

        self.lbl_state = QLabel("填好生日，先点「排八字」或「排紫微」")
        self.lbl_state.setStyleSheet("color:%s;font-size:12px;" % TEXT_SUB)

        g.addWidget(QLabel("姓名"), 0, 0)
        g.addWidget(self.ed_name, 0, 1)
        g.addWidget(QLabel("性别"), 0, 2)
        g.addWidget(self.cb_gender, 0, 3)
        g.addWidget(QLabel("出生地"), 0, 4)
        g.addWidget(self.cb_city, 0, 5)
        g.addWidget(self.chk_true, 0, 6)
        g.addWidget(self.btn_bazi, 0, 7)
        g.addWidget(self.btn_ziwei, 0, 8)
        g.addWidget(self.btn_cross, 0, 9)
        self.btn_hepan = QPushButton("合盘")
        self.btn_hepan.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #0e9f6e,stop:1 #0b7a54);color:#fff;border:none;"
            "border-radius:12px;padding:9px 18px;font-weight:600;}"
            "QPushButton:hover{background:#0b6b4a;}")
        g.addWidget(self.btn_hepan, 0, 10)

        g.addWidget(QLabel("公历"), 1, 0)
        row = QHBoxLayout()
        row.setSpacing(6)
        for w in (self.sp_y, self.sp_m, self.sp_d):
            row.addWidget(w)
        row.addWidget(QLabel("时"))
        row.addWidget(self.sp_h)
        row.addWidget(QLabel("分"))
        row.addWidget(self.sp_mi)
        gw = QWidget(); gw.setLayout(row)
        g.addWidget(gw, 1, 1, 1, 6)
        g.addWidget(self.lbl_state, 1, 7, 1, 3)

        # ---- 命例 ----
        g.addWidget(QLabel("命例"), 2, 0)
        self.cb_case = QComboBox()
        self.cb_case.setMinimumWidth(340)
        g.addWidget(self.cb_case, 2, 1, 1, 4)
        self.btn_save = QPushButton("保存命例")
        self.btn_del = QPushButton("删除")
        self.btn_save.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #66d9b5,stop:1 #3fae7a);color:#fff;border:none;"
            "border-radius:11px;padding:8px 16px;font-weight:600;}"
            "QPushButton:hover{background:#38a374;}")
        self.btn_del.setStyleSheet(
            "QPushButton{background:#b91c1c;color:#fff;border:none;"
            "border-radius:11px;padding:8px 16px;font-weight:600;}"
            "QPushButton:hover{background:#991b1b;}")
        g.addWidget(self.btn_save, 2, 5, 1, 2)
        g.addWidget(self.btn_del, 2, 7, 1, 1)

        root.addWidget(box)

        # ---------- 左右分栏 ----------
        self.bazi_panel = BaziMain()
        self.bazi_panel.setWindowTitle("八字")
        # 藏掉它自己的输入行（它有自己的排盘/解盘按钮，那些按钮在输入行里）
        lay = self.bazi_panel.layout()
        if lay and lay.count():
            first = lay.itemAt(0).widget()
            if first:
                first.hide()

        self.ziwei_panel = ZiweiPanel()

        self.split = QSplitter(Qt.Horizontal)
        self.split.addWidget(self.bazi_panel)
        self.split.addWidget(self.ziwei_panel)
        self.split.setSizes([880, 880])

        # ---------- 底部交叉 ----------
        self.cross = CrossPanel()

        vsplit = QSplitter(Qt.Vertical)
        vsplit.addWidget(self.split)
        vsplit.addWidget(self.cross)
        vsplit.setSizes([700, 300])
        root.addWidget(vsplit, 1)

        self.btn_bazi.clicked.connect(self.do_bazi)
        self.btn_ziwei.clicked.connect(self.do_ziwei)
        self.btn_cross.clicked.connect(self.do_cross)
        self.btn_hepan.clicked.connect(self.open_hepan)
        self.btn_save.clicked.connect(self.save_case)
        self.btn_del.clicked.connect(self.del_case)
        self.cb_case.currentIndexChanged.connect(self.load_case)
        self.cb_case.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cb_case.customContextMenuRequested.connect(self.case_menu)
        self.refresh_cases()
        self.btn_cross.setEnabled(False)

    # ---------- 命例 ----------
    def refresh_cases(self):
        cur = self.cb_case.currentData()
        self.cb_case.blockSignals(True)
        self.cb_case.clear()
        self.cb_case.addItem("（新命例）", None)
        for i, c in enumerate(CS.all_cases()):
            self.cb_case.addItem(
                "%s  %04d-%02d-%02d %02d:%02d  %s" % (
                    c.get("name", "?"), c.get("year", 0), c.get("month", 0),
                    c.get("day", 0), c.get("hour", 0), c.get("minute", 0),
                    c.get("pillars", "")), i)
        self.cb_case.blockSignals(False)
        if cur is not None:
            k = self.cb_case.findData(cur)
            if k >= 0:
                self.cb_case.setCurrentIndex(k)

    def load_case(self):
        idx = self.cb_case.currentData()
        if idx is None:
            return
        items = CS.all_cases()
        if not (0 <= idx < len(items)):
            return
        c = items[idx]
        self.ed_name.setText(c.get("name", "命主"))
        self.cb_gender.setCurrentText(c.get("gender", "女"))
        self.sp_y.setValue(c.get("year", 2002))
        self.sp_m.setValue(c.get("month", 1))
        self.sp_d.setValue(c.get("day", 1))
        self.sp_h.setValue(c.get("hour", 0))
        self.sp_mi.setValue(c.get("minute", 0))
        self.chk_true.setChecked(bool(c.get("true_solar", True)))
        # 载入后自动两边都排
        self.do_bazi()
        self.do_ziwei()

    def save_case(self):
        if not (self.bazi and self.bazi[0]):
            self.lbl_state.setText("先点「排八字」，再保存")
            return
        b, a = self.bazi
        ge, _ = CL.judge_ge(b.day.gan, b.month.zhi, b.month.cang, BZ.shishen)
        n = CS.add_case(
            self.ed_name.text().strip() or "命主",
            self.cb_gender.currentText(),
            self.sp_y.value(), self.sp_m.value(), self.sp_d.value(),
            self.sp_h.value(), self.sp_mi.value(),
            longitude=self._long(), true_solar=self.chk_true.isChecked(),
            day_gz=b.day.text(), month_gz=b.month.text(),
            year_gz=b.year.text(), hour_gz=b.hour.text(),
            strength=a["强弱"], ge=ge)
        self.refresh_cases()
        self.lbl_state.setText("已保存，命例库共 %d 条" % n)

    def del_case(self):
        idx = self.cb_case.currentData()
        if idx is None:
            self.lbl_state.setText("先在下拉里选一条")
            return
        items = CS.all_cases()
        if not (0 <= idx < len(items)):
            return
        c = items[idx]
        CS.del_case(c.get("name"), c.get("year"), c.get("month"),
                    c.get("day"), c.get("hour"), c.get("minute"))
        self.refresh_cases()
        self.lbl_state.setText("已删除")

    def case_menu(self, pos):
        from PySide6.QtWidgets import QMenu, QMessageBox
        idx = self.cb_case.currentData()
        m = QMenu(self)
        a_del = a_copy = None
        if idx is not None:
            items = CS.all_cases()
            if 0 <= idx < len(items):
                c = items[idx]
                t = m.addAction("　%s  %04d-%02d-%02d %02d:%02d" % (
                    c.get("name", "?"), c.get("year", 0), c.get("month", 0),
                    c.get("day", 0), c.get("hour", 0), c.get("minute", 0)))
                t.setEnabled(False)
                m.addSeparator()
                a_del = m.addAction("删除这条命例")
                a_copy = m.addAction("复制四柱")
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
                "删掉这条命例？\n\n%s  %04d-%02d-%02d %02d:%02d" % (
                    c.get("name", "?"), c.get("year", 0), c.get("month", 0),
                    c.get("day", 0), c.get("hour", 0), c.get("minute", 0)),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ok == QMessageBox.Yes:
                CS.del_case(c.get("name"), c.get("year"), c.get("month"),
                            c.get("day"), c.get("hour"), c.get("minute"))
                self.refresh_cases()
                self.lbl_state.setText("已删除")
        elif a_copy is not None and chosen == a_copy:
            items = CS.all_cases()
            QApplication.clipboard().setText(items[idx].get("pillars", ""))
            self.lbl_state.setText("四柱已复制")
        elif chosen == a_ref:
            self.refresh_cases()

    # ---------- 取值 ----------
    def _dt(self):
        return datetime(self.sp_y.value(), self.sp_m.value(),
                        self.sp_d.value(), self.sp_h.value(),
                        self.sp_mi.value())

    def _long(self):
        return float(self.cb_city.currentText().split()[-1])

    def _date_str(self):
        return "%04d-%02d-%02d" % (self.sp_y.value(), self.sp_m.value(),
                                   self.sp_d.value())

    # ---------- 排八字 ----------
    def do_bazi(self):
        m = self.bazi_panel
        m.ed_name.setText(self.ed_name.text())
        m.cb_gender.setCurrentText(self.cb_gender.currentText())
        m.sp_year.setValue(self.sp_y.value())
        m.sp_month.setValue(self.sp_m.value())
        m.sp_day.setValue(self.sp_d.value())
        m.sp_hour.setValue(self.sp_h.value())
        m.sp_min.setValue(self.sp_mi.value())
        m.chk_true.setChecked(self.chk_true.isChecked())
        m.cb_city.setCurrentText(self.cb_city.currentText())
        m.run()
        self.bazi = getattr(m, "_last", (None, None))
        self._refresh_state()

    # ---------- 排紫微 ----------
    def do_ziwei(self):
        ti = ZW.time_index_of(self.sp_h.value(), self.sp_mi.value())
        try:
            c = ZW.chart(self._date_str(), ti, self.cb_gender.currentText())
        except Exception as e:
            self.lbl_state.setText("紫微排盘失败：%s" % e)
            return
        self.ziwei_data = c
        self.ziwei_panel.set_chart(c)
        self._refresh_state()

    def _refresh_state(self):
        has_b = bool(self.bazi and self.bazi[0])
        has_z = bool(self.ziwei_data)
        self.btn_cross.setEnabled(has_b and has_z)
        parts = []
        if has_b:
            b = self.bazi[0]
            parts.append("八字 %s %s %s %s" % (b.year.text(), b.month.text(),
                                              b.day.text(), b.hour.text()))
        if has_z:
            parts.append("紫微 命宫%s%s" % (self.ziwei_data["soul_palace_stem"],
                                          self.ziwei_data["soul_palace_branch"]))
        if not parts:
            parts.append("还没排盘")
        elif not (has_b and has_z):
            parts.append("（两边都排了才能交叉分析）")
        self.lbl_state.setText("　｜　".join(parts))

    def open_hepan(self):
        """开合盘窗口，人一自动填当前生日"""
        if getattr(self, "_hepan_win", None) is None:
            self._hepan_win = HepanWindow()
        self._hepan_win.p1.set_value(
            self.ed_name.text() or "人一",
            self.cb_gender.currentText(),
            self._dt(), self.chk_true.isChecked())
        self._hepan_win.ziwei_data = getattr(self, "ziwei_data", None)
        self._hepan_win.show()
        self._hepan_win.raise_()
        self._hepan_win.activateWindow()

    # ---------- 交叉 ----------
    def do_cross(self):
        if not (self.bazi and self.bazi[0] and self.ziwei_data):
            return
        b, a = self.bazi
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
        now_y = datetime.now().year
        ln = "  ".join("%d %s(%s)" % (y, gz, TH.shishen_of(b.day.gan, gz))
                       for y, gz in TH.liunian(now_y, 4))

        bazi_txt = AI.build_user_prompt(b, a, ge, why, gk, gv, sk, sv,
                                        ss, rz, kw, dy, ln)
        ziwei_txt = ZW.full_text(self.ziwei_data)

        prompt = (
            "【出生】%s %s　%s\n\n"
            "========== 第一份：子平八字 ==========\n%s\n\n"
            "========== 第二份：紫微斗数 ==========\n%s\n"
            % (self.ed_name.text(), self._dt().strftime("%Y-%m-%d %H:%M"),
               self.cb_gender.currentText(), bazi_txt, ziwei_txt)
        )
        self.cross.start(prompt)


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    w = App()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
