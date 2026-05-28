# -*- coding: utf-8 -*-
"""
Stats 统计窗口
从 main.py 独立出来，由 stats 插件自己管理
"""

from datetime import datetime
from typing import List, Tuple

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton
)

from plugins.utils import format_duration, format_timestamp


class StatsDialog(QDialog):
    """
    使用统计弹窗

    显示今日/本周/本月分类统计和时间线。
    数据由 StatsPlugin 提供，这里只负责渲染。
    """

    # 统一的深色主题样式
    STYLESHEET = """
        QDialog {
            background-color: #1a1a2e;
            color: white;
        }
        QTabWidget::pane {
            border: 1px solid #16213e;
            background-color: #1a1a2e;
        }
        QTabBar::tab {
            background-color: #16213e;
            color: white;
            padding: 8px 16px;
            border: 1px solid #0f3460;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background-color: #0f3460;
        }
        QTableWidget {
            background-color: #16213e;
            color: white;
            border: 1px solid #0f3460;
            gridline-color: #1a1a2e;
        }
        QHeaderView::section {
            background-color: #0f3460;
            color: white;
            padding: 5px;
            border: none;
        }
        QPushButton {
            background-color: #0f3460;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #1a4a8a;
        }
    """

    def __init__(self, stats_data: List[Tuple[str, int]],
                 timeline_data: List[Tuple],
                 week_stats: List[Tuple[str, int]],
                 month_stats: List[Tuple[str, int]],
                 parent=None):
        """
        Args:
            stats_data: [(分类, 总时长), ...]
            timeline_data: [(窗口标题, 进程名, 分类, 开始时间, 时长), ...]
            week_stats: [(分类, 总时长), ...]
            month_stats: [(分类, 总时长), ...]
        """
        super().__init__(parent)
        self.setWindowTitle("WindowStatus 使用统计")
        self.setFixedSize(600, 500)
        self.setStyleSheet(self.STYLESHEET)

        layout = QVBoxLayout()
        tabs = QTabWidget()

        # 今日统计
        tabs.addTab(self._create_stats_tab(stats_data), "今日统计")

        # 周统计
        tabs.addTab(self._create_stats_tab(week_stats), "本周统计")

        # 月统计
        tabs.addTab(self._create_stats_tab(month_stats), "本月统计")

        # 时间线
        tabs.addTab(self._create_timeline_tab(timeline_data), "时间线")

        layout.addWidget(tabs)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _create_stats_tab(self, stats_data: List[Tuple[str, int]]) -> QTableWidget:
        """创建今日统计标签页"""
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["分类", "时长", "占比"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)

        table.setRowCount(len(stats_data))
        total = sum(duration for _, duration in stats_data) or 1

        for row, (category, duration) in enumerate(stats_data):
            table.setItem(row, 0, QTableWidgetItem(category))
            table.setItem(row, 1, QTableWidgetItem(format_duration(duration)))
            table.setItem(row, 2, QTableWidgetItem(f"{duration / total * 100:.1f}%"))

        return table

    def _create_timeline_tab(self, timeline_data: List[Tuple]) -> QTableWidget:
        """创建时间线标签页"""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["时间", "窗口", "分类", "时长"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)

        table.setRowCount(len(timeline_data))

        for row, (title, process, category, start_time, duration) in enumerate(timeline_data):
            table.setItem(row, 0, QTableWidgetItem(format_timestamp(start_time)))
            table.setItem(row, 1, QTableWidgetItem(title[:30]))
            table.setItem(row, 2, QTableWidgetItem(category))
            table.setItem(row, 3, QTableWidgetItem(format_duration(duration)))

        return table
