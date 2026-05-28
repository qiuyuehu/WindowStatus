# -*- coding: utf-8 -*-
"""
悬浮窗插件 - 插件层
显示当前窗口分类状态的悬浮窗
"""

from datetime import datetime
from typing import Optional, Callable

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont

from core.monitor import WindowInfo
from core.classifier import ClassificationResult


def format_duration(seconds: int) -> str:
    """格式化时长"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分钟"


class OverlayPlugin(QWidget):
    """
    悬浮窗插件
    
    显示当前窗口的分类、标题、进程名、使用时长
    支持拖拽、透明度设置、置顶
    """
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        
        # 窗口设置
        self.setWindowTitle("WindowStatus")
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 100)
        
        # 拖拽支持
        self.drag_position = QPoint()
        
        # 当前状态
        self.current_category = "其他"
        self.current_icon = "💻"
        self.current_color = QColor(149, 165, 166)
        self.current_title = ""
        self.current_process = ""
        self.current_start_time: Optional[datetime] = None
        
        # 创建界面
        self._create_ui()
        
        # 时长更新定时器
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self._update_duration)
        self.duration_timer.start(1000)
        
        # 应用透明度
        self.setWindowOpacity(config.get("opacity", 0.9))
    
    def _create_ui(self):
        """创建界面"""
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)
        
        # 左侧：分类图标
        self.icon_label = QLabel(self.current_icon)
        self.icon_label.setFont(QFont('Segoe UI Emoji', 24))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedWidth(50)
        layout.addWidget(self.icon_label)
        
        # 右侧：文字信息
        right_layout = QVBoxLayout()
        right_layout.setSpacing(2)
        
        # 分类名称
        self.category_label = QLabel(self.current_category)
        self.category_label.setFont(QFont('Microsoft YaHei UI', 12, QFont.Bold))
        self.category_label.setStyleSheet("color: white;")
        right_layout.addWidget(self.category_label)
        
        # 窗口标题
        self.title_label = QLabel("等待窗口切换...")
        self.title_label.setFont(QFont('Microsoft YaHei UI', 9))
        self.title_label.setStyleSheet("color: #b8b8b8;")
        self.title_label.setWordWrap(True)
        right_layout.addWidget(self.title_label)
        
        # 进程名
        self.process_label = QLabel("")
        self.process_label.setFont(QFont('Microsoft YaHei UI', 8))
        self.process_label.setStyleSheet("color: #808080;")
        right_layout.addWidget(self.process_label)
        
        # 使用时长
        self.duration_label = QLabel("")
        self.duration_label.setFont(QFont('Microsoft YaHei UI', 8))
        self.duration_label.setStyleSheet("color: #4ECDC4;")
        right_layout.addWidget(self.duration_label)
        
        layout.addLayout(right_layout, 1)
        self.setLayout(layout)
    
    def paintEvent(self, event):
        """绘制圆角背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addRoundedRect(5, 5, self.width() - 10, self.height() - 10, 15, 15)
        
        painter.fillPath(path, QColor(26, 26, 46, 220))
        
        pen = painter.pen()
        pen.setColor(self.current_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def update_window(self, window_info: WindowInfo, classification: ClassificationResult):
        """
        更新显示的窗口信息
        
        Args:
            window_info: 窗口信息
            classification: 分类结果
        """
        # 记录上一个活动的时长
        if self.current_start_time and self.current_title:
            duration = int((datetime.now() - self.current_start_time).total_seconds())
            # 这里可以触发回调来记录统计数据
        
        # 更新当前状态
        self.current_category = classification.category
        self.current_icon = classification.icon
        self.current_color = QColor(*classification.color)
        self.current_title = window_info.title
        self.current_process = window_info.process_name
        self.current_start_time = datetime.now()
        
        # 更新界面
        self.icon_label.setText(classification.icon)
        self.category_label.setText(classification.category)
        
        display_title = window_info.title
        if len(display_title) > 25:
            display_title = display_title[:22] + "..."
        self.title_label.setText(display_title)
        self.process_label.setText(window_info.process_name)
        
        self.update()
    
    def _update_duration(self):
        """更新使用时长显示"""
        if self.current_start_time:
            duration = int((datetime.now() - self.current_start_time).total_seconds())
            self.duration_label.setText(f"⏱ {format_duration(duration)}")
    
    def set_opacity(self, opacity: float):
        """设置透明度"""
        self.setWindowOpacity(opacity)
        self.config["opacity"] = opacity
    
    def set_always_on_top(self, enabled: bool):
        """设置置顶"""
        if enabled:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
        self.config["always_on_top"] = enabled