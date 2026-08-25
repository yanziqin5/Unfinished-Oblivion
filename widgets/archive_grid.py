"""
档案馆网格视图 —— 氛围升级版。
通栏搜索、字迹云按钮、遗忘统计、卡片状态/右键菜单。
文艺化文案。
"""
import time
import math

from PyQt5.QtCore import (
    Qt, QTimer, QSize, pyqtSignal, QRect, QEvent, QPropertyAnimation,
)
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QPixmap,
    QIcon, QPen,
)

from widgets.round_helper import paint_rounded_bg, RoundedMenu
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QGridLayout,
    QMenu, QAction, QMessageBox, QDialog, QDialogButtonBox,
    QGraphicsOpacityEffect,
)

from utils.constants import (
    SYSTEM_FONT, SERIF_FONT, TEXT_COLOR, HINT_TEXT_COLOR,
    BUTTON_BG, BUTTON_HOVER_BG, BUTTON_TEXT, CONTROL_RADIUS,
    PAPER_BG_HEX, STAGE_LABELS,
    DARK_BG, DARK_TEXT, DARK_HINT,
    DIALOG_BG_COLOR, DIALOG_BG_ALPHA,
    ARCHIVE_SEARCH_PLACEHOLDER, SLEEP_DAYS, SLEEP_HINT_TEXT,
    ARCHIVE_WORDCLOUD_TITLE, ARCHIVE_STATS_TITLE,
    ARCHIVE_EMPTY, ARCHIVE_CONFIRM_DELETE, ARCHIVE_CONFIRM_SEAL,
    PRINCE_LEVELS,
    ARCHIVE_CARD_TEXT, ARCHIVE_SEARCH_BG, ARCHIVE_SCROLLBAR_HANDLE,
    ARCHIVE_SLEEP_OVERLAY, ARCHIVE_DIALOG_BG, ARCHIVE_WORDCLOUD_WORD,
    ARCHIVE_STATS_SUBTITLE, ARCHIVE_CARD_AGED,
    ARCHIVE_BUTTON_TEXT, ARCHIVE_BUTTON_TEXT_DARK,
)
from utils.helpers import prince_level_text
from utils.db import db


class ArchiveGrid(QWidget):
    """档案馆网格主视图"""

    page_opened = pyqtSignal(int)
    page_deleted = pyqtSignal(int)
    toast_requested = pyqtSignal(str)
    new_page_requested = pyqtSignal()
    search_text = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark_mode: bool = False
        self._pages: list = []
        self._page_widgets: dict = {}  # page_id -> widget

        self._build_ui()

        # 搜索防抖
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._do_search)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 标题行 + 新建按钮
        header_layout = QHBoxLayout()
        title = QLabel("旧纸堆")
        title.setFont(QFont(SERIF_FONT, 18))
        title.setStyleSheet(f"color: {TEXT_COLOR};")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        # 醒目新建笔记按钮
        self.btn_new = QPushButton("＋ 写一篇新笔记")
        self.btn_new.setFixedHeight(36)
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new.clicked.connect(self.new_page_requested.emit)
        self.btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {BUTTON_BG};
                color: {BUTTON_TEXT};
                border: 1px solid rgba(160,148,130,0.50);
                border-radius: {CONTROL_RADIUS}px;
                font-family: "{SYSTEM_FONT}";
                font-size: 13px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {BUTTON_HOVER_BG};
                border: 1px solid rgba(160,148,130,0.65);
            }}
        """)
        header_layout.addWidget(self.btn_new)
        layout.addLayout(header_layout)

        # 搜索栏
        search_layout = QHBoxLayout()
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText(ARCHIVE_SEARCH_PLACEHOLDER)
        self.edit_search.textChanged.connect(self._on_search_changed)
        self.edit_search.setStyleSheet(f"""
            QLineEdit {{
                background: {ARCHIVE_SEARCH_BG};
                color: {ARCHIVE_CARD_TEXT};
                border: 1px solid rgba(196,186,168,0.35);
                border-radius: {CONTROL_RADIUS}px;
                padding: 8px 12px;
                font-family: "{SYSTEM_FONT}";
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(140,130,115,0.5);
            }}
        """)
        search_layout.addWidget(self.edit_search, 1)

        # 字迹云
        btn_cloud = QPushButton("字迹云")
        btn_cloud.setFixedSize(50, 32)
        btn_cloud.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cloud.clicked.connect(self._show_wordcloud)
        btn_cloud.setToolTip(ARCHIVE_WORDCLOUD_TITLE)
        search_layout.addWidget(btn_cloud)

        # 遗忘统计
        btn_stats = QPushButton("统计")
        btn_stats.setFixedSize(50, 32)
        btn_stats.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_stats.clicked.connect(self._show_stats)
        btn_stats.setToolTip(ARCHIVE_STATS_TITLE)
        search_layout.addWidget(btn_stats)

        layout.addLayout(search_layout)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                width: 4px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {ARCHIVE_SCROLLBAR_HANDLE};
                border-radius: 4px;
            }}
        """)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(10)
        scroll.setWidget(self.grid_widget)

        layout.addWidget(scroll, 1)

        # 底部统计
        self.label_bottom = QLabel("")
        self.label_bottom.setFont(QFont(SYSTEM_FONT, 9))
        self.label_bottom.setStyleSheet(f"color: {HINT_TEXT_COLOR};")
        self.label_bottom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_bottom)

        # 按钮样式
        btn_style = f"""
            QPushButton {{
                background: {BUTTON_BG};
                color: {BUTTON_TEXT};
                border: 1px solid rgba(160,148,130,0.35);
                border-radius: {CONTROL_RADIUS}px;
                font-family: "{SYSTEM_FONT}";
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {BUTTON_HOVER_BG};
                border: 1px solid rgba(160,148,130,0.55);
            }}
        """
        for btn in [btn_cloud, btn_stats]:
            btn.setStyleSheet(btn_style)

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self.update()

    def refresh(self):
        """重新加载页面列表。"""
        self._pages = db.list_pages(self.search_text)
        self._redraw_grid()

    def _on_search_changed(self, text: str):
        self.search_text = text
        self._search_timer.start()

    def _do_search(self):
        self._pages = db.list_pages(self.search_text)
        self._redraw_grid()

    def _redraw_grid(self):
        """重新绘制卡片网格。"""
        # 清空
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._page_widgets.clear()

        if not self._pages:
            empty_label = QLabel(ARCHIVE_EMPTY)
            empty_label.setFont(QFont(SERIF_FONT, 12))
            empty_label.setStyleSheet(f"color: {HINT_TEXT_COLOR};")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setWordWrap(True)
            self.grid_layout.addWidget(empty_label, 0, 0, 1, 4)
            self.label_bottom.setText("")
            return

        cols = max(1, (self.width() - 40) // 160)
        for i, page in enumerate(self._pages):
            card = self._make_card(page)
            row, col = divmod(i, cols)
            self.grid_layout.addWidget(card, row, col)
            self._page_widgets[page.page_id] = card

        # 底部趣味统计
        total_chars = sum(page.word_count or 0 for page in self._pages)
        self.label_bottom.setText(
            f"共 {len(self._pages)} 张旧纸  ·  {prince_level_text(total_chars)}"
        )

    def _make_card(self, page) -> QPushButton:
        """创建笔记卡片。"""
        btn = QPushButton()
        btn.setFixedSize(150, 100)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.page_opened.emit(page.page_id))
        btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos, p=page, b=btn: self._card_menu(pos, p, b))

        # 根据创建时间动态计算纸张阶段（随时间自然老化）
        from utils.constants import get_paper_stage
        current_paper = get_paper_stage(page.create_time, page.is_sealed) if page.create_time else "黄1"
        bg_hex = PAPER_BG_HEX.get(current_paper, "#F6F3E9")
        stage_label = STAGE_LABELS.get(current_paper, "黄1")

        age_days = (time.time() - page.create_time) / 86400 if page.create_time else 0
        freshness = max(0, 100 - int(age_days * 5))
        if page.is_sealed:
            freshness = 100

        # 视觉区分：衰老≥90%叠加泛黄滤镜
        if freshness <= 10 and not page.is_sealed:
            bg_hex = ARCHIVE_CARD_AGED  # 泛黄做旧色
            border_style = "1px solid rgba(200, 170, 100, 0.5)"
            sep = "将逝"
        elif page.is_sealed:
            # 封存笔记：叠加淡信封水印效果
            border_style = "2px dotted rgba(196, 186, 168, 0.5)"
            sep = "封存"
        else:
            border_style = "1px solid rgba(196,186,168,0.35)"
            sep = "遗" if freshness < 30 else "存" if freshness >= 70 else "淡"

        labels = []
        labels.append(f"◈ {page.title or '未命名'} ◈")
        labels.append(f"{stage_label} · {freshness}%")
        if page.is_sealed:
            labels.append("—— 已封存 ——")
        elif freshness <= 10:
            labels.append("—— 即将消散 ——")

        btn.setText("\n".join(labels))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_hex};
                border: {border_style};
                border-radius: 5px;
                color: {ARCHIVE_CARD_TEXT};
                font-family: "{SYSTEM_FONT}";
                font-size: 10px;
                text-align: center;
                padding: 8px;
            }}
            QPushButton:hover {{
                border: 1px solid rgba(140,130,115,0.6);
                background: {bg_hex};
            }}
        """)
        # "已沉睡"页面：很久未打开时，悬浮显示一行小字提示
        sleep_days = (time.time() - (page.last_open_time or page.create_time)) / 86400
        if not page.is_sealed and sleep_days >= SLEEP_DAYS:
            hint = QLabel(btn)
            hint.setText(SLEEP_HINT_TEXT)
            hint.setWordWrap(True)
            hint.setAlignment(Qt.AlignCenter)
            hint.setGeometry(QRect(6, 6, 138, 88))
            hint.setStyleSheet(f"""
                QLabel {{
                    background: {ARCHIVE_SLEEP_OVERLAY};
                    color: {ARCHIVE_DIALOG_BG};
                    font-family: "{SYSTEM_FONT}";
                    font-size: 9px;
                    border-radius: 5px;
                    padding: 8px;
                }}
            """)
            fx = QGraphicsOpacityEffect()
            fx.setOpacity(0.0)
            hint.setGraphicsEffect(fx)
            hint.hide()
            btn._sleep_hint = hint
            btn.installEventFilter(self)
        return btn

    def eventFilter(self, obj, event):
        hint = getattr(obj, '_sleep_hint', None)
        if hint is not None:
            et = event.type()
            if et == QEvent.Type.Enter:
                self._show_sleep_hint(hint)
                return False
            elif et == QEvent.Type.Leave:
                self._hide_sleep_hint(hint)
                return False
        return super().eventFilter(obj, event)

    def _show_sleep_hint(self, hint):
        if hint is None:
            return
        hint.show()
        fx = hint.graphicsEffect()
        anim = QPropertyAnimation(fx, b"opacity")
        anim.setDuration(250)
        anim.setStartValue(fx.opacity())
        anim.setEndValue(1.0)
        anim.start()
        hint._anim = anim   # 防止动画对象被回收

    def _hide_sleep_hint(self, hint):
        if hint is None:
            return
        fx = hint.graphicsEffect()
        anim = QPropertyAnimation(fx, b"opacity")
        anim.setDuration(200)
        anim.setStartValue(fx.opacity())
        anim.setEndValue(0.0)
        anim.finished.connect(lambda: hint.hide())
        anim.start()
        hint._anim = anim

    def _card_menu(self, pos, page, btn):
        """卡片右键菜单。pos 为按钮内局部坐标，需按按钮做全局映射。"""
        menu = RoundedMenu(self, self._dark_mode)
        menu.addAction("重新打开", lambda: self.page_opened.emit(page.page_id))
        menu.addSeparator()
        menu.addAction("重命名…", lambda: self._rename_page(page))
        menu.addAction("导出…", lambda: self._export_page(page))
        menu.addSeparator()
        if not page.is_sealed:
            menu.addAction("封存此页", lambda: self._seal_page(page))
        menu.addAction("删除此页", lambda: self._delete_page(page))
        menu.exec_(btn.mapToGlobal(pos))

    def _rename_page(self, page):
        from widgets.rounded_dialogs import input_dialog
        text = input_dialog(self, "重命名", "给这张纸取个名字：", page.title or "")
        if text:
            db.rename_page(page.page_id, text)
            self.refresh()

    def _export_page(self, page):
        # 打开该页后触发导出
        self.page_opened.emit(page.page_id)
        self.toast_requested.emit("请在新打开的页面中使用导出功能")

    def _seal_page(self, page):
        from widgets.rounded_dialogs import confirm_dialog
        if confirm_dialog(self, "封存确认", ARCHIVE_CONFIRM_SEAL):
            db.seal_page(page.page_id)
            self.refresh()

    def _delete_page(self, page):
        from widgets.rounded_dialogs import confirm_dialog
        if confirm_dialog(self, "归入遗忘", ARCHIVE_CONFIRM_DELETE):
            db.delete_page(page.page_id)
            self.page_deleted.emit(page.page_id)  # 通知主窗口同步当前页/画布/工具栏
            self.refresh()

    def _show_wordcloud(self):
        """显示字迹云弹窗。"""
        weights = db.wordcloud_weights(self.search_text)
        if not weights:
            self.toast_requested.emit("纸上尚无字迹。")
            return
        top = sorted(weights, key=lambda x: x[1], reverse=True)[:30]
        w = max(c for _, c in top)
        items = [(word, int(10 + (cnt / max(1, w)) * 30)) for word, cnt in top]
        dlg = WordCloudDialog(items, self._dark_mode, self)
        dlg.exec_()

    def _show_stats(self):
        """显示遗忘账单统计弹窗。"""
        total_lost = db.total_lost_words()
        pages = db.list_pages()
        total_pages = len(pages)
        total_alive = sum(
            len(db.get_alive_words(p.page_id)) for p in pages
        )
        total_revives = sum(db.total_revives_on_page(p.page_id) for p in pages)
        sealed_count = sum(1 for p in pages if p.is_sealed)
        dlg = StatsDialog(
            total_pages=total_pages,
            total_alive=total_alive,
            total_lost=total_lost,
            total_revives=total_revives,
            sealed_count=sealed_count,
            dark_mode=self._dark_mode,
            parent=self,
        )
        dlg.exec_()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._dark_mode:
            painter.fillRect(self.rect(), QColor(DARK_BG))
        else:
            # 偏深的暖砂色（#D4CAB6），比原先过亮的 (245,240,232)/(236,230,216) 沉稳不刺眼
            painter.fillRect(self.rect(), QColor(0xD4, 0xCA, 0xB6))
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pages:
            self._redraw_grid()


# ============================================================
# 弹窗类
# ============================================================

class WordCloudDialog(QDialog):
    """字迹云弹窗 —— 文字频率可视化，字频越高字号越大。"""

    def __init__(self, items, dark_mode=False, parent=None):
        super().__init__(parent)
        self._items = items
        self._dark_mode = dark_mode
        self.setWindowTitle("纸上字迹云")
        self.setFixedSize(480, 360)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("纸上字迹云")
        title.setFont(QFont(SERIF_FONT, 16))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {TEXT_COLOR}; margin-bottom: 8px;")
        layout.addWidget(title)

        # 字迹云展示区域
        cloud_widget = QWidget()
        cloud_widget.setMinimumHeight(240)
        cloud_widget.paintEvent = lambda e, w=cloud_widget: self._paint_cloud(w)
        cloud_widget._items = self._items  # 通过闭包传参，供 paintEvent 使用
        layout.addWidget(cloud_widget)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn_box.accepted.connect(self.accept)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("关闭")
        layout.addWidget(btn_box)

    def paintEvent(self, event):
        bg = DARK_BG if self._dark_mode else ARCHIVE_DIALOG_BG
        paint_rounded_bg(self, QColor(bg), 12, border=QColor(196, 186, 168, 110))

    def _paint_cloud(self, widget):
        p = QPainter(widget)
        p.fillRect(widget.rect(), QColor(DARK_BG if self._dark_mode else "#ECE6D8"))
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._items:
            p.end()
            return
        import random
        rng = random.Random(42)  # 固定种子保证一致性
        w, h = widget.width(), widget.height()
        for word, size in self._items:
            font = QFont(SERIF_FONT, max(10, min(size, 36)))
            p.setFont(font)
            c = QColor(ARCHIVE_WORDCLOUD_WORD)
            c.setAlpha(rng.randint(140, 220))
            p.setPen(c)
            fm = QFontMetrics(font)
            tw = fm.horizontalAdvance(word) + 8
            th = fm.height() + 4
            x = rng.randint(10, max(10, w - tw - 10))
            y = rng.randint(th, max(th + 10, h - 5))
            p.drawText(QRect(x, y - th, tw + 20, th + 10), Qt.AlignmentFlag.AlignLeft, word)
        p.end()


class StatsDialog(QDialog):
    """遗忘账单统计弹窗。"""

    def __init__(self, total_pages, total_alive, total_lost,
                 total_revives, sealed_count, dark_mode=False, parent=None):
        super().__init__(parent)
        self._total_pages = total_pages
        self._total_alive = total_alive
        self._total_lost = total_lost
        self._total_revives = total_revives
        self._sealed_count = sealed_count
        self._dark_mode = dark_mode
        self.setWindowTitle("遗忘账单")
        self.setFixedSize(400, 320)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)

        title = QLabel("遗忘账单")
        title.setFont(QFont(SERIF_FONT, 16))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {ARCHIVE_CARD_TEXT}; margin-bottom: 4px;")
        layout.addWidget(title)

        subtitle = QLabel("—— 在这张旧纸上的时间痕迹 ——")
        subtitle.setFont(QFont(SYSTEM_FONT, 9))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {ARCHIVE_STATS_SUBTITLE}; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        stats_text = (
            f"共 {self._total_pages} 张旧纸\n"
            f"{self._total_alive} 个词仍在呼吸\n"
            f"{self._total_lost} 个字已悄然消散\n"
            f"文字被凝视 {self._total_revives} 次\n"
            f"{self._sealed_count} 页已被封存定格"
        )
        label = QLabel(stats_text)
        label.setFont(QFont(SERIF_FONT, 12))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"color: {ARCHIVE_CARD_TEXT}; line-height: 1.8;")
        layout.addWidget(label)

        # 小王子换算
        prince_text = prince_level_text(self._total_lost)
        hint = QLabel(prince_text)
        hint.setFont(QFont(SYSTEM_FONT, 9))
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color: {ARCHIVE_STATS_SUBTITLE}; margin-top: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addStretch()

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn_box.accepted.connect(self.accept)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("知道啦")
        layout.addWidget(btn_box)

    def paintEvent(self, event):
        bg = DARK_BG if self._dark_mode else ARCHIVE_DIALOG_BG
        paint_rounded_bg(self, QColor(bg), 12, border=QColor(196, 186, 168, 110))
