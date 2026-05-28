# -*- coding: utf-8 -*-
"""
Tray 插件 - 插件层
系统托盘图标和菜单
"""

from typing import Optional

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt

from plugins.base import Plugin
from kernel.event_bus import Events


class TrayPlugin(Plugin):
    """
    系统托盘插件
    
    职责：
    - 提供系统托盘图标和右键菜单
    - 监听用户操作，通过事件总线发送事件
    """
    
    name = "tray"
    version = "1.0.0"
    description = "系统托盘插件，提供托盘图标和菜单"
    
    def __init__(self, kernel):
        super().__init__(kernel)
        
        self.tray: Optional[QSystemTrayIcon] = None
        self.menu: Optional[QMenu] = None
        
        # 状态
        self.is_top_action: Optional[QAction] = None
        self.autostart_action: Optional[QAction] = None
    
    def on_load(self):
        """插件加载"""
        self.logger = self.kernel.logger
        
        # 创建系统托盘
        self._create_tray()
        
        # 注册事件监听
        self.event_bus.on(Events.CATEGORY_MATCHED, self._on_category_matched)
        
        self.logger.info("Tray 插件已加载")
    
    def on_unload(self):
        """插件卸载"""
        # 注销事件监听
        self.event_bus.off(Events.CATEGORY_MATCHED, self._on_category_matched)
        
        # 销毁托盘
        self._destroy_tray()
        
        self.logger.info("Tray 插件已卸载")
    
    def on_enable(self):
        """插件启用"""
        if self.tray:
            self.tray.show()
        self.logger.info("Tray 插件已启用")
    
    def on_disable(self):
        """插件禁用"""
        if self.tray:
            self.tray.hide()
        self.logger.info("Tray 插件已禁用")
    
    def _create_tray(self):
        """创建系统托盘"""
        try:
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
            self.logger.info("Tray 插件: 系统托盘已创建")
        
        except Exception as e:
            self.logger.error(f"Tray 插件: 创建系统托盘失败: {e}")
    
    def _destroy_tray(self):
        """销毁系统托盘"""
        if self.tray:
            self.tray.hide()
            self.tray = None
    
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
        show_action.triggered.connect(lambda: self.event_bus.emit("overlay.show"))
        
        hide_action = self.menu.addAction("隐藏悬浮窗")
        hide_action.triggered.connect(lambda: self.event_bus.emit("overlay.hide"))
        
        self.menu.addSeparator()
        
        # 置顶开关
        is_top = self.config.is_always_on_top()
        self.is_top_action = self.menu.addAction("取消置顶" if is_top else "置顶")
        self.is_top_action.triggered.connect(lambda: self._toggle_top())
        
        self.menu.addSeparator()
        
        # 透明度
        opacity_menu = self.menu.addMenu("透明度")
        for value in [100, 90, 80, 70, 60, 50]:
            action = opacity_menu.addAction(f"{value}%")
            action.triggered.connect(
                lambda checked, v=value: self._set_opacity(v / 100)
            )
        
        self.menu.addSeparator()
        
        # 统计和设置
        stats_action = self.menu.addAction("使用统计")
        stats_action.triggered.connect(lambda: self.event_bus.emit(Events.SHOW_STATS))
        
        settings_action = self.menu.addAction("设置")
        settings_action.triggered.connect(lambda: self.event_bus.emit(Events.SHOW_SETTINGS))
        
        # 关于
        about_action = self.menu.addAction("关于")
        about_action.triggered.connect(lambda: self.event_bus.emit(Events.SHOW_ABOUT))
        
        self.menu.addSeparator()
        
        # 开机自启动
        self.autostart_action = self.menu.addAction("开机自启动")
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(self._is_autostart_enabled())
        self.autostart_action.triggered.connect(
            lambda checked: self._toggle_autostart(checked)
        )
        
        self.menu.addSeparator()
        
        # 退出
        quit_action = self.menu.addAction("退出")
        quit_action.triggered.connect(lambda: self.event_bus.emit(Events.QUIT))
        
        self.tray.setContextMenu(self.menu)
    
    def _toggle_top(self):
        """切换置顶状态"""
        current = self.config.is_always_on_top()
        new_state = not current
        self.config.set_always_on_top(new_state)
        
        # 发送置顶切换事件
        self.event_bus.emit(Events.TOGGLE_TOP, enabled=new_state)
        
        # 更新菜单文本
        if self.is_top_action:
            self.is_top_action.setText("取消置顶" if new_state else "置顶")
        
        self.logger.info(f"Tray 插件: 置顶状态: {new_state}")
    
    def _set_opacity(self, opacity: float):
        """设置透明度"""
        self.config.set_opacity(opacity)
        
        # 发送透明度变更事件
        self.event_bus.emit(Events.OPACITY_CHANGED, opacity=opacity)
        
        self.logger.info(f"Tray 插件: 透明度: {opacity}")
    
    def _toggle_autostart(self, checked: bool):
        """切换开机自启动"""
        try:
            import sys
            import os
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            
            if checked:
                if getattr(sys, 'frozen', False):
                    app_path = sys.executable
                else:
                    app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
                
                winreg.SetValueEx(key, "WindowStatus", 0, winreg.REG_SZ, app_path)
                self.logger.info("Tray 插件: 已启用开机自启动")
            else:
                try:
                    winreg.DeleteValue(key, "WindowStatus")
                except FileNotFoundError:
                    pass
                self.logger.info("Tray 插件: 已禁用开机自启动")
            
            winreg.CloseKey(key)
            
            # 更新菜单状态
            if self.autostart_action:
                self.autostart_action.setChecked(checked)
        
        except Exception as e:
            self.logger.error(f"Tray 插件: 设置开机自启动失败: {e}")
            QMessageBox.warning(None, "错误", f"设置开机自启动失败: {e}")
    
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
        except Exception:
            return False
    
    def _on_category_matched(self, **kwargs):
        """处理分类匹配事件，更新托盘提示"""
        if self.tray:
            category = kwargs.get('category', '其他')
            title = kwargs.get('title', '')
            process_name = kwargs.get('process_name', '')
            
            # 更新托盘提示
            tooltip = f"WindowStatus\n分类: {category}\n窗口: {title[:30]}\n进程: {process_name}"
            self.tray.setToolTip(tooltip)
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information):
        """显示托盘消息"""
        if self.tray:
            self.tray.showMessage(title, message, icon)
    
    def update_top_state(self, is_top: bool):
        """更新置顶状态"""
        if self.is_top_action:
            self.is_top_action.setText("取消置顶" if is_top else "置顶")
    
    def update_autostart_state(self, enabled: bool):
        """更新自启动状态"""
        if self.autostart_action:
            self.autostart_action.setChecked(enabled)


# 约定：PluginClass 变量指向插件类
PluginClass = TrayPlugin
