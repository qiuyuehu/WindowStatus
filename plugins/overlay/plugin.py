# -*- coding: utf-8 -*-
"""
Overlay 插件 - 插件层
显示当前窗口分类状态的悬浮窗
"""

from datetime import datetime
from typing import Optional

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont

from plugins.base import Plugin
from kernel.event_bus import Events


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


class OverlayWidget(QWidget):
    """悬浮窗控件"""
    
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
    
    def update_display(self, category: str, icon: str, color: tuple, title: str, process_name: str):
        """更新显示内容"""
        # 更新当前状态
        self.current_category = category
        self.current_icon = icon
        self.current_color = QColor(*color)
        self.current_title = title
        self.current_process = process_name
        self.current_start_time = datetime.now()
        
        # 更新界面
        self.icon_label.setText(icon)
        self.category_label.setText(category)
        
        display_title = title
        if len(display_title) > 25:
            display_title = display_title[:22] + "..."
        self.title_label.setText(display_title)
        self.process_label.setText(process_name)
        
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


class OverlayPlugin(Plugin):
    """
    悬浮窗插件
    
    职责：
    - 监听 CATEGORY_MATCHED 事件
    - 更新悬浮窗显示
    - 支持拖拽、透明度设置、置顶
    """
    
    name = "overlay"
    version = "1.0.0"
    description = "悬浮窗插件，显示当前窗口分类状态"
    
    def __init__(self, kernel):
        super().__init__(kernel)
        
        self.widget: Optional[OverlayWidget] = None
    
    def on_load(self):
        """插件加载"""
        self.logger = self.kernel.logger
        
        # 创建悬浮窗
        self._create_widget()
        
        # 注册事件监听
        self.event_bus.on(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.on(Events.OPACITY_CHANGED, self._on_opacity_changed)
        self.event_bus.on(Events.TOGGLE_TOP, self._on_toggle_top)
        
        self.logger.info("Overlay 插件已加载")
    
    def on_unload(self):
        """插件卸载"""
        # 注销事件监听
        self.event_bus.off(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.off(Events.OPACITY_CHANGED, self._on_opacity_changed)
        self.event_bus.off(Events.TOGGLE_TOP, self._on_toggle_top)
        
        # 销毁悬浮窗
        if self.widget:
            self.widget.close()
            self.widget = None
        
        self.logger.info("Overlay 插件已卸载")
    
    def on_enable(self):
        """插件启用"""
        if self.widget:
            self.widget.show()
        self.logger.info("Overlay 插件已启用")
    
    def on_disable(self):
        """插件禁用"""
        if self.widget:
            self.widget.hide()
        self.logger.info("Overlay 插件已禁用")
    
    def _create_widget(self):
        """创建悬浮窗"""
        try:
            self.widget = OverlayWidget({
                "opacity": self.config.get_opacity(),
                "always_on_top": self.config.is_always_on_top()
            })
            self.widget.show()
            self.logger.info("Overlay 插件: 悬浮窗已创建")
        except Exception as e:
            self.logger.error(f"Overlay 插件: 创建悬浮窗失败: {e}")
    
    def _on_category_matched(self, category: str, icon: str, color: tuple, title: str, process_name: str, **kwargs):
        """处理分类匹配事件"""
        self.logger.debug(f"Overlay 插件: 收到事件 [{category}] {title[:20]}")
        if self.widget and self.enabled:
            self.widget.update_display(category, icon, color, title, process_name)
            self.logger.debug(f"Overlay 插件: 界面已更新 [{category}]")
        else:
            self.logger.warning(f"Overlay 插件: 无法更新 widget={self.widget is not None} enabled={self.enabled}")
    
    def _on_opacity_changed(self, opacity: float, **kwargs):
        """处理透明度变更事件"""
        if self.widget:
            self.widget.set_opacity(opacity)
    
    def _on_toggle_top(self, enabled: bool, **kwargs):
        """处理置顶切换事件"""
        if self.widget:
            self.widget.set_always_on_top(enabled)
    
    def show(self):
        """显示悬浮窗"""
        if self.widget:
            self.widget.show()
    
    def hide(self):
        """隐藏悬浮窗"""
        if self.widget:
            self.widget.hide()


# 约定：PluginClass 变量指向插件类
PluginClass = OverlayPlugin
