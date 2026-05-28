# -*- coding: utf-8 -*-
"""
系统托盘插件 - 插件层
系统托盘图标和菜单
"""

from typing import Callable, Optional

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt


class TrayPlugin:
    """
    系统托盘插件
    
    提供系统托盘图标和右键菜单
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.tray: Optional[QSystemTrayIcon] = None
        self.menu: Optional[QMenu] = None
        
        # 回调函数
        self.on_show_overlay: Optional[Callable] = None
        self.on_hide_overlay: Optional[Callable] = None
        self.on_toggle_top: Optional[Callable] = None
        self.on_set_opacity: Optional[Callable] = None
        self.on_show_stats: Optional[Callable] = None
        self.on_show_settings: Optional[Callable] = None
        self.on_toggle_autostart: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None
        
        # 状态
        self.is_top_action: Optional[QAction] = None
        self.autostart_action: Optional[QAction] = None
    
    def create(self):
        """创建系统托盘"""
        self.tray = QSystemTrayIcon()
        
        # 创建图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(78, 205, 196))
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont('Arial', 16, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "W")
        painter.end()
        self.tray.setIcon(QIcon(pixmap))
        self.tray.setToolTip("WindowStatus - 窗口状态显示器")
        
        # 创建菜单
        self._create_menu()
        
        self.tray.show()
    
    def _create_menu(self):
        """创建菜单"""
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a2e;
                color: white;
                border: 1px solid #16213e;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #16213e;
            }
        """)
        
        # 显示/隐藏
        show_action = self.menu.addAction("显示悬浮窗")
        show_action.triggered.connect(lambda: self.on_show_overlay() if self.on_show_overlay else None)
        
        hide_action = self.menu.addAction("隐藏悬浮窗")
        hide_action.triggered.connect(lambda: self.on_hide_overlay() if self.on_hide_overlay else None)
        
        self.menu.addSeparator()
        
        # 置顶开关
        is_top = self.config.get("always_on_top", True)
        self.is_top_action = self.menu.addAction("取消置顶" if is_top else "置顶")
        self.is_top_action.triggered.connect(lambda: self.on_toggle_top() if self.on_toggle_top else None)
        
        self.menu.addSeparator()
        
        # 透明度
        opacity_menu = self.menu.addMenu("透明度")
        for value in [100, 90, 80, 70, 60, 50]:
            action = opacity_menu.addAction(f"{value}%")
            action.triggered.connect(
                lambda checked, v=value: self.on_set_opacity(v / 100) if self.on_set_opacity else None
            )
        
        self.menu.addSeparator()
        
        # 统计和设置
        stats_action = self.menu.addAction("使用统计")
        stats_action.triggered.connect(lambda: self.on_show_stats() if self.on_show_stats else None)
        
        settings_action = self.menu.addAction("设置")
        settings_action.triggered.connect(lambda: self.on_show_settings() if self.on_show_settings else None)
        
        self.menu.addSeparator()
        
        # 开机自启动
        self.autostart_action = self.menu.addAction("开机自启动")
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(self._is_autostart_enabled())
        self.autostart_action.triggered.connect(
            lambda checked: self.on_toggle_autostart(checked) if self.on_toggle_autostart else None
        )
        
        self.menu.addSeparator()
        
        # 退出
        quit_action = self.menu.addAction("退出")
        quit_action.triggered.connect(lambda: self.on_quit() if self.on_quit else None)
        
        self.tray.setContextMenu(self.menu)
    
    def _is_autostart_enabled(self) -> bool:
        """检查是否已启用开机自启动"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, "WindowStatus")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except:
            return False
    
    def update_top_state(self, is_top: bool):
        """更新置顶状态"""
        if self.is_top_action:
            self.is_top_action.setText("取消置顶" if is_top else "置顶")
    
    def update_autostart_state(self, enabled: bool):
        """更新自启动状态"""
        if self.autostart_action:
            self.autostart_action.setChecked(enabled)
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information):
        """显示托盘消息"""
        if self.tray:
            self.tray.showMessage(title, message, icon)
    
    def destroy(self):
        """销毁托盘"""
        if self.tray:
            self.tray.hide()
            self.tray = None