# -*- coding: utf-8 -*-
"""
Overlay 插件 - 插件层
显示当前窗口分类状态的气泡
"""

from datetime import datetime
from typing import Optional

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPoint, QTimer, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont

from plugins.base import Plugin
from plugins.utils import format_duration, truncate_text
from kernel.event_bus import Events


class OverlayWidget(QWidget):
    """气泡控件"""

    # 窗口标志（不包含 Qt.Tool，避免在部分 Windows 版本上鼠标事件失效）
    WINDOW_FLAGS = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    # 气泡尺寸
    BUBBLE_WIDTH = 260
    BUBBLE_HEIGHT = 70
    BUBBLE_RADIUS = 20
    DOT_RADIUS = 3  # 小气泡半径（更小）

    def __init__(self, config: dict, on_close=None):
        super().__init__()
        self.config = config
        self._on_close = on_close  # 关闭事件回调

        # 窗口设置
        self.setWindowTitle("WindowStatus")
        self.setWindowFlags(self.WINDOW_FLAGS)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 额外空间给小气泡（上下都有）
        self.setFixedSize(self.BUBBLE_WIDTH + self.DOT_RADIUS, self.BUBBLE_HEIGHT + self.DOT_RADIUS * 2 + 2)

        # 颜色方案
        # 当前状态
        self.current_category = "其他"
        self.current_icon = "💻"
        self.current_color = QColor(149, 165, 166)
        self.current_title = ""
        self.current_process = ""
        self.current_start_time: Optional[datetime] = None
        
        # 小气泡方向（"down" 或 "up"）
        self.dot_direction = "down"
        
        # 颜色方案
        self.THEMES = {
            "dark": {
                "bg": QColor(26, 26, 46, 200),
                "title": QColor(255, 255, 255),
                "process": QColor(160, 160, 160),
                "duration": QColor(78, 205, 196),
                "category": QColor(120, 120, 120),
                "icon": QColor(255, 255, 255),
            },
            "light": {
                "bg": QColor(255, 255, 255, 220),
                "title": QColor(30, 30, 30),
                "process": QColor(100, 100, 100),
                "duration": QColor(0, 150, 136),
                "category": QColor(130, 130, 130),
                "icon": QColor(30, 30, 30),
            }
        }
        self.theme = "dark"  # 默认暗色

        # 时长更新定时器
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self._update_duration)
        self.duration_timer.start(1000)

        # TOPMOST 维护定时器（每 1 秒用 Win32 SetWindowPos 强制刷新置顶状态）
        # 解决 Windows 系统抢占 TOPMOST、浏览器/cmd 抢焦点后丢失置顶等问题
        self._topmost_timer = QTimer()
        self._topmost_timer.timeout.connect(self._maintain_topmost)
        self._topmost_timer.start(1000)

        # 应用透明度
        self.setWindowOpacity(config.get("opacity", 0.9))

        # 应用置顶状态
        if config.get("always_on_top", True):
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def paintEvent(self, event):
        """绘制气泡（圆角矩形 + 小气泡连接点）"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取当前主题颜色
        colors = self.THEMES.get(self.theme, self.THEMES["dark"])

        # 绘制大气泡（圆角矩形）
        bubble_rect = QRectF(0, 0, self.BUBBLE_WIDTH, self.BUBBLE_HEIGHT)
        path = QPainterPath()
        path.addRoundedRect(bubble_rect, self.BUBBLE_RADIUS, self.BUBBLE_RADIUS)
        painter.fillPath(path, colors["bg"])

        # 绘制小气泡（连接点）在大气泡底部
        dot_x = self.BUBBLE_WIDTH - 1  # 靠近右边
        dot_y = self.BUBBLE_HEIGHT + self.DOT_RADIUS + 1  # 大气泡底部
        painter.setBrush(colors["bg"])
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(dot_x, dot_y), self.DOT_RADIUS, self.DOT_RADIUS)

        # 绘制文字内容
        margin_left = 15
        margin_top = 10
        content_width = self.BUBBLE_WIDTH - margin_left * 2

        # 第一行：图标 + 标题
        icon_x = margin_left
        icon_y = margin_top + 16
        painter.setFont(QFont('Segoe UI Emoji', 14))
        painter.setPen(colors["icon"])
        painter.drawText(QRectF(icon_x, icon_y - 14, 20, 18), Qt.AlignCenter, self.current_icon)

        title_x = icon_x + 24
        title_y = icon_y
        painter.setFont(QFont('Microsoft YaHei UI', 10, QFont.Bold))
        painter.setPen(colors["title"])
        title_text = truncate_text(self.current_title, 18)
        painter.drawText(QRectF(title_x, title_y - 14, content_width - 24, 18), Qt.AlignLeft | Qt.AlignVCenter, title_text)

        # 第二行：进程名 + 时长
        process_y = title_y + 18
        painter.setFont(QFont('Microsoft YaHei UI', 8))
        painter.setPen(colors["process"])
        process_text = truncate_text(self.current_process, 12)
        painter.drawText(QRectF(margin_left, process_y - 10, 80, 14), Qt.AlignLeft | Qt.AlignVCenter, process_text)

        # 时长
        if self.current_start_time:
            duration = int((datetime.now() - self.current_start_time).total_seconds())
            duration_text = format_duration(duration)
            painter.setPen(colors["duration"])
            painter.drawText(QRectF(margin_left + 85, process_y - 10, 60, 14), Qt.AlignRight | Qt.AlignVCenter, duration_text)

        # 第三行：分类标签
        category_y = process_y + 16
        painter.setFont(QFont('Microsoft YaHei UI', 8))
        painter.setPen(colors["category"])
        painter.drawText(QRectF(margin_left, category_y - 10, content_width, 14), Qt.AlignLeft | Qt.AlignVCenter, self.current_category)

    def closeEvent(self, event):
        """关闭事件：委托给外部处理（用于最小化到托盘）"""
        if self._on_close:
            self._on_close(event)
        else:
            event.accept()

    # ---- 显示更新 ----

    def update_display(self, category: str, icon: str, color: tuple, title: str, process_name: str):
        """更新显示内容"""
        self.current_category = category
        self.current_icon = icon
        self.current_color = QColor(*color)
        self.current_title = title
        self.current_process = process_name
        self.current_start_time = datetime.now()

        # 触发重绘
        self.update()

    def _update_duration(self):
        """更新使用时长显示"""
        if self.current_start_time:
            # 触发重绘（时长在 paintEvent 中绘制）
            self.update()

    # ---- 属性设置 ----

    def set_opacity(self, opacity: float):
        """设置透明度"""
        self.setWindowOpacity(opacity)
        self.config["opacity"] = opacity

    def set_always_on_top(self, enabled: bool):
        """设置置顶（仅在状态变化时重建窗口）"""
        current = bool(self.windowFlags() & Qt.WindowStaysOnTopHint)
        if current == enabled:
            return

        if enabled:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
        self.config["always_on_top"] = enabled

        # 启停 TOPMOST 维护定时器
        if enabled:
            self._topmost_timer.start(1000)  # ★ 改成1秒，和桌宠一致
            self._maintain_topmost()  # 立即刷新一次
        else:
            self._topmost_timer.stop()

    def _maintain_topmost(self):
        """Win32 强制刷新 TOPMOST 状态（防止 Windows 系统抢占置顶）"""
        if not self.isVisible():
            return
        if not self.config.get("always_on_top", True):
            return
        try:
            import ctypes
            hwnd = int(self.winId())
            # HWND_TOPMOST = -1
            # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOOWNERZORDER = 0x0203
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0203)
        except OSError:
            pass


class OverlayPlugin(Plugin):
    """
    悬浮窗插件

    职责：
    - 监听 CATEGORY_MATCHED 事件
    - 更新悬浮窗显示
    - 支持拖拽、透明度设置、置顶、位置设置
    """

    name = "overlay"
    version = "1.2.0"
    description = "悬浮窗插件，显示当前窗口分类状态"

    def __init__(self, kernel):
        super().__init__(kernel)
        self.widget: Optional[OverlayWidget] = None
        self._force_quit = False

    def on_load(self):
        """插件加载"""
        

        # 创建悬浮窗
        self._create_widget()

        # 注册事件监听
        self.event_bus.on(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.on(Events.OPACITY_CHANGED, self._on_opacity_changed)
        self.event_bus.on(Events.TOGGLE_TOP, self._on_toggle_top)
        self.event_bus.on(Events.OVERLAY_SHOW, self._on_overlay_show)
        self.event_bus.on(Events.OVERLAY_HIDE, self._on_overlay_hide)
        self.event_bus.on(Events.OVERLAY_SET_THEME, self._on_set_theme)
        self.event_bus.on(Events.QUIT, self._on_quit)

        self.logger.info("Overlay 插件已加载")

    def on_unload(self):
        """插件卸载"""
        self.event_bus.off(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.off(Events.OPACITY_CHANGED, self._on_opacity_changed)
        self.event_bus.off(Events.TOGGLE_TOP, self._on_toggle_top)
        self.event_bus.off(Events.OVERLAY_SHOW, self._on_overlay_show)
        self.event_bus.off(Events.OVERLAY_HIDE, self._on_overlay_hide)
        self.event_bus.off(Events.OVERLAY_SET_THEME, self._on_set_theme)
        self.event_bus.off(Events.QUIT, self._on_quit)

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
            self.widget = OverlayWidget(
                config={
                    "opacity": self.config.get_opacity(),
                    "always_on_top": self.config.is_always_on_top()
                },
                on_close=self._on_widget_close
            )

            # 加载保存的主题配置
            saved_theme = self.config.get("theme", "dark")
            self.widget.theme = saved_theme

            # 先隐藏，恢复位置后再显示（避免闪到默认位置）
            self.widget.hide()

            # 恢复桌宠保存的气泡位置（如果有）
            saved_pos = self._kernel.config.get("desktop_pet.overlay_position")
            if saved_pos and "x" in saved_pos and "y" in saved_pos:
                self.widget.move(saved_pos["x"], saved_pos["y"])

            self.widget.show()
            self.logger.info("Overlay 插件: 悬浮窗已创建")
        except (RuntimeError, OSError) as e:
            self.logger.error(f"Overlay 插件: 创建悬浮窗失败: {e}")

    def set_position(self, position: str):
        """设置位置并通知其他插件"""
        self.config.set_position(position)
        
        # 通知其他插件Overlay位置变化
        if self.widget:
            self.event_bus.emit(
                Events.OVERLAY_POSITION_CHANGED,
                position=position,
                x=self.widget.pos().x(),
                y=self.widget.pos().y(),
                width=self.widget.width(),
                height=self.widget.height()
            )

    def _on_category_matched(self, category: str, icon: str, color: tuple, title: str, process_name: str, **kwargs):
        """处理分类匹配事件"""
        if self.widget and self.enabled:
            self.widget.update_display(category, icon, color, title, process_name)
            # 广播状态数据给其他插件（如桌面宠物）
            self.event_bus.emit(Events.OVERLAY_DATA_CHANGED,
                               icon=icon,
                               category=category,
                               title=title,
                               process_name=process_name)

    def _on_opacity_changed(self, opacity: float, **kwargs):
        """处理透明度变更事件"""
        if self.widget:
            self.widget.set_opacity(opacity)

    def _on_toggle_top(self, enabled: bool, **kwargs):
        """处理置顶切换事件"""
        if self.widget:
            self.widget.set_always_on_top(enabled)

    def _on_overlay_show(self, **kwargs):
        """处理显示Overlay事件"""
        self.show()

    def _on_overlay_hide(self, **kwargs):
        """处理隐藏Overlay事件"""
        self.hide()

    def _on_set_theme(self, **kwargs):
        """处理设置主题事件"""
        theme = kwargs.get("theme")
        if theme and self.widget:
            self.widget.theme = theme
            self.widget.update()
            self.logger.info(f"Overlay 插件: 主题已切换为 {theme}")

    def _on_widget_close(self, event):
        """处理悬浮窗关闭事件（最小化到托盘或真正关闭）"""
        if self._force_quit:
            # 真正退出
            event.accept()
            return
        if self.config.is_minimize_to_tray():
            # 最小化到托盘
            if self.widget:
                self.hide()
            event.ignore()
            self.logger.info("Overlay 插件: 已隐藏到托盘")
        else:
            # 正常关闭
            event.accept()

    def _on_quit(self, **kwargs):
        """处理退出事件：强制关闭悬浮窗"""
        self._force_quit = True
        if self.widget:
            self.widget.close()

    def show(self):
        """显示悬浮窗"""
        if self.widget:
            self.widget.show()
            self._win32_set_visible(True)

    def hide(self):
        """隐藏悬浮窗"""
        if self.widget:
            self.widget.hide()
            self._win32_set_visible(False)

    def _win32_set_visible(self, visible: bool):
        """Win32 API 控制窗口显隐（解决 Win11 任务栏残留问题）"""
        try:
            import ctypes
            hwnd = int(self.widget.winId())
            if visible:
                # 用 SetWindowPos 显示并强制 TOPMOST（ShowWindow 不保证维持置顶）
                # HWND_TOPMOST = -1, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW = 0x0001 | 0x0002 | 0x0040 = 0x0043
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0043)
            else:
                # 隐藏窗口：SW_HIDE = 0
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except OSError:
            pass


# 约定：PluginClass 变量指向插件类
PluginClass = OverlayPlugin
