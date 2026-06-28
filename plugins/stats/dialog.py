# -*- coding: utf-8 -*-
"""
Stats 统计窗口 — Apple Screen Time 风格重写
从 main.py 独立出来，由 stats 插件自己管理
"""

from typing import List, Tuple, Dict, Callable, Optional

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QFont, QBrush, QPainterPath
)
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QWidget, QLabel,
    QSizePolicy, QMessageBox, QFileDialog
)

from plugins.utils import format_duration, format_timestamp, CustomTabBar, FramelessDialog
from plugins.common_styles import (
    COLOR_BG_PRIMARY, COLOR_BG_SECONDARY, COLOR_BG_TERTIARY,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_BORDER, COLOR_BORDER_SUBTLE, COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER, COLOR_PRIMARY_PRESSED,
    COLOR_ERROR,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_CAPTION,
    SPACING_SM, SPACING_MD, SPACING_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    oklch_to_qcolor,
)

# 默认图标（分类没有配置 icon 时使用）
DEFAULT_ICON = "❓"


# ── 暗色主题样式表 ──────────────────────────────────────────────

STYLESHEET = f"""
QDialog {{
    color: {COLOR_TEXT_PRIMARY.name()};
}}
QTabWidget::pane {{
    border: none;
    background-color: {COLOR_BG_PRIMARY.name()};
}}
QTableWidget {{
    background-color: {COLOR_BG_SECONDARY.name()};
    color: {COLOR_TEXT_PRIMARY.name()};
    border: none;
    gridline-color: {COLOR_BORDER_SUBTLE.name()};
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 4px 8px;
}}
QHeaderView::section {{
    background-color: #0f0f0f;
    color: {COLOR_TEXT_PRIMARY.name()};
    padding: 6px 8px;
    border: none;
    font-size: 12px;
}}
QPushButton {{
    background-color: {COLOR_BG_SECONDARY.name()};
    color: {COLOR_TEXT_PRIMARY.name()};
    border: 1px solid {COLOR_BORDER.name()};
    padding: {SPACING_SM}px {SPACING_LG}px;
    border-radius: {RADIUS_MD}px;
    font-size: {FONT_SIZE_BODY}px;
}}
QPushButton:hover {{
    background-color: {COLOR_BG_TERTIARY.name()};
}}
QPushButton#primary {{
    background-color: {COLOR_PRIMARY.name()};
    color: #fff;
    border: none;
}}
QPushButton#primary:hover {{
    background-color: {COLOR_PRIMARY_HOVER.name()};
}}
"""


# ── 摘要卡片 ────────────────────────────────────────────────────

class SummaryCard(QWidget):
    """顶部摘要卡片：总时长 / 最常用分类 / 和上期对比"""

    def __init__(self, total_seconds: int, top_category: str,
                 top_icon: str, top_percent: float,
                 compare_total: int,
                 total_label: str = "今日总时长",
                 compare_label: str = "vs 昨天",
                 compare_prefix: str = "比昨天",
                 parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)

        from PyQt5.QtWidgets import QGridLayout, QLayoutItem
        grid = QGridLayout(self)
        grid.setContentsMargins(32, 0, 32, 0)
        grid.setSpacing(0)

        # 副标题行（row 0）
        sub_style = (f"font-size: {FONT_SIZE_SUBTITLE}px; font-weight: bold;"
                     f" color: {COLOR_TEXT_SECONDARY.name()};")

        self._total_sub = QLabel(total_label)
        self._total_sub.setStyleSheet(sub_style)
        self._total_sub.setAlignment(Qt.AlignCenter)

        self._top_sub = QLabel("最常用分类")
        self._top_sub.setStyleSheet(sub_style)
        self._top_sub.setAlignment(Qt.AlignCenter)

        self._compare_sub = QLabel(compare_label)
        self._compare_sub.setStyleSheet(sub_style)
        self._compare_sub.setAlignment(Qt.AlignCenter)

        # 主数据行（row 1）
        val_style = (f"font-size: {FONT_SIZE_SUBTITLE}px;"
                     f" color: {COLOR_TEXT_PRIMARY.name()};")

        self._total_value = QLabel(format_duration(total_seconds))
        self._total_value.setStyleSheet(val_style)
        self._total_value.setAlignment(Qt.AlignCenter)

        if top_category:
            center_text = f"{top_icon} {top_category}  占 {top_percent:.0f}%"
        else:
            center_text = "暂无数据"
        self._top_value = QLabel(center_text)
        self._top_value.setStyleSheet(val_style)
        self._top_value.setAlignment(Qt.AlignCenter)

        if compare_total > 0 and total_seconds > 0:
            diff_pct = (total_seconds - compare_total) / compare_total * 100
            if diff_pct >= 0:
                compare_text = f"{compare_prefix}多 {diff_pct:.0f}%"
                color = COLOR_PRIMARY.name()
            else:
                compare_text = f"{compare_prefix}少 {abs(diff_pct):.0f}%"
                color = COLOR_ERROR.name()
        elif compare_total == 0 and total_seconds > 0:
            compare_text = "上期无数据"
            color = COLOR_TEXT_MUTED.name()
        elif total_seconds == 0:
            compare_text = "暂无数据"
            color = COLOR_TEXT_MUTED.name()
        else:
            compare_text = "无对比数据"
            color = COLOR_TEXT_MUTED.name()
        self._compare_value = QLabel(compare_text)
        self._compare_value.setStyleSheet(
            f"font-size: {FONT_SIZE_SUBTITLE}px; color: {color};")
        self._compare_value.setAlignment(Qt.AlignCenter)

        # 布局：row 0 = 副标题，row 1 = 主数据
        grid.addWidget(self._total_sub, 0, 0, Qt.AlignCenter)
        grid.addWidget(self._top_sub, 0, 1, Qt.AlignCenter)
        grid.addWidget(self._compare_sub, 0, 2, Qt.AlignCenter)
        grid.addWidget(self._total_value, 1, 0, Qt.AlignCenter)
        grid.addWidget(self._top_value, 1, 1, Qt.AlignCenter)
        grid.addWidget(self._compare_value, 1, 2, Qt.AlignCenter)

        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

    def paintEvent(self, event):
        """绘制卡片背景和分隔线"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(COLOR_BG_SECONDARY)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), RADIUS_LG, RADIUS_LG)

        # 三列之间的分隔线（与 grid 列边界对齐）
        painter.setPen(QPen(COLOR_BORDER, 1))
        w = self.width()
        h = self.height()
        margin_top = int(h * 0.15)
        margin_bottom = int(h * 0.15)
        # grid: left_margin=32, 3列等宽, spacing=0
        left_m = 32
        col_w = (w - 2 * left_m) / 3
        x1 = int(left_m + col_w)
        painter.drawLine(x1, margin_top, x1, h - margin_bottom)
        x2 = int(left_m + 2 * col_w)
        painter.drawLine(x2, margin_top, x2, h - margin_bottom)


# ── 环形图 ──────────────────────────────────────────────────────

class DonutChart(QWidget):
    """环形占比图，QPainter 自绘"""

    # 备用颜色（oklch 生成，分类没有配置颜色时使用）
    FALLBACK_COLORS = [
        oklch_to_qcolor(0.7, 0.15, 25),   # 红
        oklch_to_qcolor(0.7, 0.15, 70),   # 黄
        oklch_to_qcolor(0.7, 0.15, 145),  # 绿
        oklch_to_qcolor(0.7, 0.15, 230),  # 蓝
        oklch_to_qcolor(0.7, 0.15, 300),  # 紫
        oklch_to_qcolor(0.7, 0.15, 30),   # 橙
        oklch_to_qcolor(0.7, 0.15, 180),  # 青
        oklch_to_qcolor(0.7, 0.15, 340),  # 粉
    ]

    def __init__(self, data: List[Tuple[str, int]],
                 categories_config: Dict, parent=None):
        """
        Args:
            data: [(分类名, 时长秒数), ...]
            categories_config: {分类名: {"icon": "🎮", "color": [r,g,b], ...}, ...}
        """
        super().__init__(parent)
        self._data = data
        self._config = categories_config
        self.setFixedSize(180, 180)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 背景透明，不显示白色方块

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        total = sum(d for _, d in self._data)
        cx, cy = 90, 90  # 中心点
        outer_r = 75
        inner_r = 48
        gap_angle = 2  # 扇区间隙（度），小值更精致

        if total == 0 or not self._data:
            # 空数据：灰色空圆环
            pen = QPen(COLOR_BORDER, outer_r - inner_r)
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            mid_r = (outer_r + inner_r) / 2
            painter.drawEllipse(QPointF(cx, cy), mid_r, mid_r)
            # 中间文字
            painter.setPen(COLOR_TEXT_MUTED)
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(QRectF(0, 0, 180, 180),
                             Qt.AlignCenter, "暂无数据")
            return

        # 绘制每个扇区
        start_angle = 90 * 16  # 从 12 点方向开始（Qt 角度单位是 1/16 度）
        pen_width = outer_r - inner_r
        mid_r = (outer_r + inner_r) / 2

        for i, (category, duration) in enumerate(self._data):
            if duration <= 0:
                continue

            # 获取颜色
            cat_config = self._config.get(category, {})
            color_list = cat_config.get("color")
            if color_list and len(color_list) >= 3:
                color = QColor(*color_list[:3])
            else:
                color = self.FALLBACK_COLORS[i % len(self.FALLBACK_COLORS)]

            # 计算角度
            ratio = duration / total
            span_angle = int(ratio * 360 * 16)

            # 最后一个扇区不加间隙，避免浮点误差导致的缺口
            if i < len(self._data) - 1 and span_angle > gap_angle * 16:
                span_angle -= int(gap_angle * 16)

            pen = QPen(color, pen_width)
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            rect = QRectF(cx - mid_r, cy - mid_r, mid_r * 2, mid_r * 2)
            painter.drawArc(rect, start_angle, span_angle)
            start_angle += span_angle + int(gap_angle * 16)

        # 中间总时长
        painter.setPen(COLOR_TEXT_PRIMARY)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(0, 72, 180, 28),
                         Qt.AlignCenter, f"{total // 3600}:{(total % 3600) // 60:02d}:{total % 60:02d}")
        painter.setPen(COLOR_TEXT_SECONDARY)
        font.setPointSize(9)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(QRectF(0, 96, 180, 18),
                         Qt.AlignCenter, "总时长")


# ── 分类列表行 ──────────────────────────────────────────────────

class CategoryRow(QWidget):
    """单行分类：emoji + 名称 + 进度条 + 时长 + 百分比"""

    # 进度条最小宽度（像素），保证极小占比也能看到
    MIN_BAR_WIDTH = 4

    def __init__(self, icon: str, name: str, duration: int,
                 percent: float, color: QColor, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)

        self._icon = icon
        self._name = name
        self._duration = duration
        self._percent = percent
        self._color = color

        # 用 QLabel 做布局（不用 paintEvent 全部自绘，省事）
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(12)

        # emoji + 分类名
        name_label = QLabel(f"{icon}  {name}")
        name_label.setStyleSheet(
            f"font-size: {FONT_SIZE_BODY}px; color: {COLOR_TEXT_PRIMARY.name()};")
        name_label.setFixedWidth(60)
        name_label.setAlignment(Qt.AlignVCenter)

        # 进度条（用自绘 widget）
        self._bar = _ProgressBar(percent, color)
        self._bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._bar.setFixedHeight(8)

        # 时长
        dur_label = QLabel(format_duration(duration))
        dur_label.setStyleSheet(
            f"font-size: 12px; color: {COLOR_TEXT_SECONDARY.name()};")
        dur_label.setFixedWidth(70)
        dur_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 百分比
        if percent < 1 and percent > 0:
            pct_text = "< 1%"
        else:
            pct_text = f"{percent:.0f}%"
        pct_label = QLabel(pct_text)
        pct_label.setStyleSheet(
            f"font-size: 12px; color: {COLOR_TEXT_SECONDARY.name()};")
        pct_label.setFixedWidth(40)
        pct_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(name_label, alignment=Qt.AlignVCenter)
        layout.addWidget(self._bar, alignment=Qt.AlignVCenter)
        layout.addWidget(dur_label, alignment=Qt.AlignVCenter)
        layout.addWidget(pct_label, alignment=Qt.AlignVCenter)


class _ProgressBar(QWidget):
    """圆角进度条"""

    def __init__(self, percent: float, color: QColor, parent=None):
        super().__init__(parent)
        self._percent = max(0, min(100, percent))
        self._color = color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # 背景条
        painter.setBrush(COLOR_BG_TERTIARY)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, RADIUS_SM, RADIUS_SM)

        # 填充条
        if self._percent > 0:
            fill_w = max(RADIUS_SM, int(w * self._percent / 100))
            painter.setBrush(self._color)
            painter.drawRoundedRect(0, 0, fill_w, h, RADIUS_SM, RADIUS_SM)


# ── 主弹窗 ─────────────────────────────────────────────────────

def _paint_card_bg(widget, event):
    """绘制卡片背景（供 lambda 复用）"""
    painter = QPainter(widget)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(COLOR_BG_SECONDARY)
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(widget.rect(), RADIUS_LG, RADIUS_LG)


class StatsDialog(FramelessDialog):
    """
    使用统计弹窗 — Apple Screen Time 风格

    显示今日/本周/本月分类统计和时间线。
    数据由 StatsPlugin 提供，这里只负责渲染。
    """

    def __init__(self,
                 stats_data: List[Tuple[str, int]],
                 timeline_data: List[Tuple],
                 week_stats: List[Tuple[str, int]],
                 month_stats: List[Tuple[str, int]],
                 yesterday_stats: Optional[List[Tuple[str, int]]] = None,
                 last_week_stats: Optional[List[Tuple[str, int]]] = None,
                 last_month_stats: Optional[List[Tuple[str, int]]] = None,
                 categories_config: Optional[Dict] = None,
                 export_csv_fn: Optional[Callable] = None,
                 export_json_fn: Optional[Callable] = None,
                 parent=None):
        super().__init__(title="WindowStatus 使用统计", parent=parent)
        self.setFixedSize(750, 520)
        self.setStyleSheet(STYLESHEET)

        # 保存数据
        self._stats_data = stats_data
        self._timeline_data = timeline_data
        self._week_stats = week_stats
        self._month_stats = month_stats
        self._yesterday_stats = yesterday_stats or []
        self._last_week_stats = last_week_stats or []
        self._last_month_stats = last_month_stats or []
        self._categories_config = categories_config or {}
        self._export_csv_fn = export_csv_fn
        self._export_json_fn = export_json_fn

        # 计算对比基准总时长
        self._yesterday_total = sum(d for _, d in self._yesterday_stats)
        self._last_week_total = sum(d for _, d in self._last_week_stats)
        self._last_month_total = sum(d for _, d in self._last_month_stats)

        # 使用 FramelessDialog 的 content_layout
        main_layout = self.content_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab（使用自绘标签栏）
        tabs = QTabWidget()
        tabs.setTabBar(CustomTabBar())
        tabs.addTab(self._create_stats_tab(), "今日统计")
        tabs.addTab(self._create_stats_tab_generic(
            self._week_stats, self._last_week_stats,
            "本周总时长", "vs 上周", "比上周"), "本周统计")
        tabs.addTab(self._create_stats_tab_generic(
            self._month_stats, self._last_month_stats,
            "本月总时长", "vs 上月", "比上月"), "本月统计")
        tabs.addTab(self._create_timeline_tab(), "时间线")

        main_layout.addWidget(tabs)

        # 底部按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(16, 12, 16, 8)
        btn_layout.addStretch()

        if self._export_csv_fn:
            csv_btn = QPushButton("导出 CSV")
            csv_btn.clicked.connect(self._on_export_csv)
            btn_layout.addWidget(csv_btn)

        if self._export_json_fn:
            json_btn = QPushButton("导出 JSON")
            json_btn.clicked.connect(self._on_export_json)
            btn_layout.addWidget(json_btn)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        main_layout.addLayout(btn_layout)

    # ── 今日统计 tab（带摘要卡片 + 环形图 + 列表）───────────

    def _create_stats_tab(self) -> QWidget:
        """创建今日统计标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 计算摘要数据
        total_seconds = sum(d for _, d in self._stats_data)
        if self._stats_data:
            top_category = self._stats_data[0][0]
            top_duration = self._stats_data[0][1]
            top_percent = (top_duration / total_seconds * 100
                          if total_seconds > 0 else 0)
        else:
            top_category = ""
            top_duration = 0
            top_percent = 0

        top_icon = self._categories_config.get(
            top_category, {}).get("icon", "") or DEFAULT_ICON

        # 摘要卡片（16px 外边距，与 demo 一致）
        summary = SummaryCard(
            total_seconds, top_category, top_icon,
            top_percent, self._yesterday_total,
            total_label="今日总时长", compare_label="vs 昨天",
            compare_prefix="比昨天"
        )
        summary_container = QWidget()
        summary_layout = QVBoxLayout(summary_container)
        summary_layout.setContentsMargins(16, 16, 16, 0)
        summary_layout.setSpacing(0)
        summary_layout.addWidget(summary)
        layout.addWidget(summary_container)

        # 中间区域：环形图 + 列表
        mid_layout = QHBoxLayout()
        mid_layout.setContentsMargins(16, 16, 16, 16)
        mid_layout.setSpacing(16)

        # 左侧：环形图
        donut = DonutChart(self._stats_data, self._categories_config)
        mid_layout.addWidget(donut, 0)

        # 右侧：分类列表
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(8)

        for category, duration in self._stats_data:
            percent = (duration / total_seconds * 100
                       if total_seconds > 0 else 0)
            cat_config = self._categories_config.get(category, {})
            icon = cat_config.get("icon", "") or DEFAULT_ICON
            color_list = cat_config.get("color", [128, 128, 128])
            color = QColor(*color_list[:3]) if len(
                color_list) >= 3 else QColor(128, 128, 128)

            row = CategoryRow(icon, category, duration, percent, color)
            list_layout.addWidget(row)

        list_layout.addStretch()
        mid_layout.addWidget(list_container, 1)

        layout.addLayout(mid_layout, 1)
        return widget

    # ── 通用统计 tab（周/月，带摘要卡片 + 环形图 + 列表）──────────────

    def _create_stats_tab_generic(
            self, data: List[Tuple[str, int]],
            compare_data: Optional[List[Tuple[str, int]]] = None,
            total_label: str = "总时长",
            compare_label: str = "vs 上期",
            compare_prefix: str = "比上期") -> QWidget:
        """创建周/月统计标签页（带三列摘要卡片）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        total = sum(d for _, d in data)
        compare_total = sum(d for _, d in (compare_data or []))

        # 计算最常用分类
        if data:
            top_category = data[0][0]
            top_duration = data[0][1]
            top_percent = (top_duration / total * 100 if total > 0 else 0)
        else:
            top_category = ""
            top_duration = 0
            top_percent = 0
        top_icon = self._categories_config.get(
            top_category, {}).get("icon", "") or DEFAULT_ICON

        # 摘要卡片（三列：总时长 + 最常用分类 + vs 上期）
        summary = SummaryCard(
            total, top_category, top_icon,
            top_percent, compare_total,
            total_label=total_label, compare_label=compare_label,
            compare_prefix=compare_prefix
        )
        summary_container = QWidget()
        summary_layout = QVBoxLayout(summary_container)
        summary_layout.setContentsMargins(16, 16, 16, 0)
        summary_layout.setSpacing(0)
        summary_layout.addWidget(summary)
        layout.addWidget(summary_container)

        # 中间区域：环形图 + 列表
        mid_layout = QHBoxLayout()
        mid_layout.setContentsMargins(16, 16, 16, 16)
        mid_layout.setSpacing(16)

        donut = DonutChart(data, self._categories_config)
        mid_layout.addWidget(donut, 0)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(8)

        for category, duration in data:
            percent = (duration / total * 100 if total > 0 else 0)
            cat_config = self._categories_config.get(category, {})
            icon = cat_config.get("icon", "") or DEFAULT_ICON
            color_list = cat_config.get("color", [128, 128, 128])
            color = QColor(*color_list[:3]) if len(
                color_list) >= 3 else QColor(128, 128, 128)

            row = CategoryRow(icon, category, duration, percent, color)
            list_layout.addWidget(row)

        list_layout.addStretch()
        mid_layout.addWidget(list_container, 1)

        layout.addLayout(mid_layout, 1)
        return widget

    # ── 时间线 tab ──────────────────────────────────────────

    def _create_timeline_tab(self) -> QWidget:
        """创建时间线标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 摘要区域
        total_duration = sum(d[4] for d in self._timeline_data) if self._timeline_data else 0
        record_count = len(self._timeline_data)

        summary = QWidget()
        summary.setFixedHeight(90)
        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(16, 16, 16, 16)

        if record_count > 0:
            count_label = QLabel(f"{record_count} 条记录")
            count_label.setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_PRIMARY.name()};")
            summary_layout.addWidget(count_label)

            dur_label = QLabel(format_duration(total_duration))
            dur_label.setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_PRIMARY.name()}; margin-left: 24px;")
            summary_layout.addWidget(dur_label)
        else:
            empty_label = QLabel("暂无数据")
            empty_label.setStyleSheet(
                f"font-size: 14px; color: {COLOR_TEXT_MUTED.name()};")
            summary_layout.addWidget(empty_label)

        summary_layout.addStretch()
        summary.paintEvent = lambda e: _paint_card_bg(summary, e)
        layout.addWidget(summary)

        # 表格（16px 外边距，与 demo 一致）
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["时间", "窗口", "分类", "时长"])
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.verticalHeader().setVisible(False)

        table.setRowCount(len(self._timeline_data))

        for row_idx, (title, process, category,
                      start_time, duration) in enumerate(
                          self._timeline_data):
            time_item = QTableWidgetItem(
                format_timestamp(start_time))
            table.setItem(row_idx, 0, time_item)

            title_text = title[:35] if title else ""
            title_item = QTableWidgetItem(title_text)
            table.setItem(row_idx, 1, title_item)

            cat_config = self._categories_config.get(category, {})
            color_list = cat_config.get("color")
            icon = cat_config.get("icon", "") or DEFAULT_ICON
            cat_item = QTableWidgetItem(f"{icon} {category}")
            if color_list and len(color_list) >= 3:
                cat_item.setForeground(QColor(*color_list[:3]))
            table.setItem(row_idx, 2, cat_item)

            dur_item = QTableWidgetItem(format_duration(duration))
            table.setItem(row_idx, 3, dur_item)

        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(16, 0, 16, 16)
        table_layout.setSpacing(0)
        table_layout.addWidget(table)
        layout.addWidget(table_container)
        return widget

    # ── 导出回调 ────────────────────────────────────────────

    def _on_export_csv(self):
        """导出 CSV"""
        if not self._export_csv_fn:
            return
        try:
            path = self._export_csv_fn()
            QMessageBox.information(
                self, "导出成功",
                f"已导出到：\n{path}")
        except Exception as e:
            QMessageBox.warning(
                self, "导出失败", f"导出出错：\n{e}")

    def _on_export_json(self):
        """导出 JSON"""
        if not self._export_json_fn:
            return
        try:
            path = self._export_json_fn()
            QMessageBox.information(
                self, "导出成功",
                f"已导出到：\n{path}")
        except Exception as e:
            QMessageBox.warning(
                self, "导出失败", f"导出出错：\n{e}")
