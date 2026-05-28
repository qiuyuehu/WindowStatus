# -*- coding: utf-8 -*-
"""
WindowStatus — Windows 窗口状态显示器
Author: 衾衾 (Hermes Agent)

重构版本 v2.0
- 插件化架构
- 配置文件管理
- 日志系统
- 异常处理优化
"""

import sys
import os
from datetime import datetime
from typing import Optional

from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QInputDialog
from PyQt5.QtCore import QTimer

from core.config import Config
from core.logger import init_logger, get_logger
from core.monitor import WindowMonitor, WindowInfo
from core.classifier import Classifier, ClassificationResult
from plugins.overlay import OverlayPlugin
from plugins.tray import TrayPlugin
from plugins.stats import StatsPlugin


# 配置文件路径
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.WindowStatus')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
DB_FILE = os.path.join(CONFIG_DIR, 'data.db')
LOG_FILE = os.path.join(CONFIG_DIR, 'window_status.log')


class WindowStatusApp:
    """
    WindowStatus 主应用
    
    整合核心模块和插件模块
    """
    
    def __init__(self):
        # 初始化日志
        self.logger = init_logger(log_file=LOG_FILE, level="INFO")
        self.logger.info("WindowStatus 启动中...")
        
        # 初始化配置
        self.config = Config(CONFIG_FILE)
        self.logger.info(f"配置文件: {CONFIG_FILE}")
        
        # 初始化核心模块
        self.monitor = WindowMonitor()
        self.classifier = Classifier()
        self.classifier.load_categories(self.config.get_categories())
        
        # 初始化统计插件
        self.stats = StatsPlugin(DB_FILE)
        self.logger.info(f"数据库: {DB_FILE}")
        
        # 初始化 Qt 应用
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # 初始化插件
        self.overlay: Optional[OverlayPlugin] = None
        self.tray: Optional[TrayPlugin] = None
        
        # 窗口监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_window_change)
        
        # 当前活动记录
        self.current_window: Optional[WindowInfo] = None
        self.current_classification: Optional[ClassificationResult] = None
        self.current_start_time: Optional[datetime] = None
    
    def start(self):
        """启动应用"""
        try:
            # 创建悬浮窗插件
            if self.config.is_plugin_enabled("overlay"):
                self._create_overlay()
            
            # 创建系统托盘插件
            if self.config.is_plugin_enabled("tray"):
                self._create_tray()
            
            # 启动窗口监控
            self.monitor_timer.start(100)  # 100ms 检查一次
            self.logger.info("窗口监控已启动")
            
            self.logger.info("WindowStatus 启动完成")
            
            # 运行应用
            return self.app.exec_()
        
        except Exception as e:
            self.logger.exception(f"启动失败: {e}")
            QMessageBox.critical(None, "错误", f"启动失败: {e}")
            return 1
    
    def _create_overlay(self):
        """创建悬浮窗"""
        try:
            self.overlay = OverlayPlugin({
                "opacity": self.config.get_opacity(),
                "always_on_top": self.config.is_always_on_top()
            })
            self.overlay.show()
            self.logger.info("悬浮窗插件已加载")
        except Exception as e:
            self.logger.error(f"创建悬浮窗失败: {e}")
    
    def _create_tray(self):
        """创建系统托盘"""
        try:
            self.tray = TrayPlugin({
                "always_on_top": self.config.is_always_on_top()
            })
            
            # 设置回调
            self.tray.on_show_overlay = self._show_overlay
            self.tray.on_hide_overlay = self._hide_overlay
            self.tray.on_toggle_top = self._toggle_top
            self.tray.on_set_opacity = self._set_opacity
            self.tray.on_show_stats = self._show_stats
            self.tray.on_show_settings = self._show_settings
            self.tray.on_toggle_autostart = self._toggle_autostart
            self.tray.on_quit = self._quit
            
            self.tray.create()
            self.logger.info("系统托盘插件已加载")
        except Exception as e:
            self.logger.error(f"创建系统托盘失败: {e}")
    
    def _check_window_change(self):
        """检查窗口切换"""
        try:
            if self.monitor.check_window_change():
                new_window = self.monitor.get_last_window()
                if new_window:
                    self._on_window_change(new_window)
        except Exception as e:
            self.logger.error(f"检查窗口切换失败: {e}")
    
    def _on_window_change(self, new_window: WindowInfo):
        """窗口切换处理"""
        try:
            # 记录上一个活动的时长
            if self.current_start_time and self.current_window:
                duration = int((datetime.now() - self.current_start_time).total_seconds())
                if duration > 0 and self.current_classification:
                    self.stats.log_activity(
                        self.current_window.title,
                        self.current_window.process_name,
                        self.current_classification.category,
                        self.current_start_time,
                        duration
                    )
            
            # 分类新窗口
            classification = self.classifier.classify(new_window.title, new_window.process_name)
            
            # 更新当前状态
            self.current_window = new_window
            self.current_classification = classification
            self.current_start_time = datetime.now()
            
            # 更新悬浮窗
            if self.overlay:
                self.overlay.update_window(new_window, classification)
            
            self.logger.debug(f"窗口切换: {new_window.title} -> {classification.category}")
        
        except Exception as e:
            self.logger.error(f"处理窗口切换失败: {e}")
    
    def _show_overlay(self):
        """显示悬浮窗"""
        if self.overlay:
            self.overlay.show()
    
    def _hide_overlay(self):
        """隐藏悬浮窗"""
        if self.overlay:
            self.overlay.hide()
    
    def _toggle_top(self):
        """切换置顶状态"""
        try:
            current = self.config.is_always_on_top()
            new_state = not current
            self.config.set_always_on_top(new_state)
            
            if self.overlay:
                self.overlay.set_always_on_top(new_state)
            
            if self.tray:
                self.tray.update_top_state(new_state)
            
            self.logger.info(f"置顶状态: {new_state}")
        except Exception as e:
            self.logger.error(f"切换置顶失败: {e}")
    
    def _set_opacity(self, opacity: float):
        """设置透明度"""
        try:
            self.config.set_opacity(opacity)
            if self.overlay:
                self.overlay.set_opacity(opacity)
            self.logger.info(f"透明度: {opacity}")
        except Exception as e:
            self.logger.error(f"设置透明度失败: {e}")
    
    def _show_stats(self):
        """显示统计窗口"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
            
            class StatsDialog(QDialog):
                def __init__(self, stats_plugin, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("WindowStatus 使用统计")
                    self.setFixedSize(600, 500)
                    self.setStyleSheet("""
                        QDialog { background-color: #1a1a2e; color: white; }
                        QTabWidget::pane { border: 1px solid #16213e; background-color: #1a1a2e; }
                        QTabBar::tab { background-color: #16213e; color: white; padding: 8px 16px; border: 1px solid #0f3460; border-bottom: none; }
                        QTabBar::tab:selected { background-color: #0f3460; }
                        QTableWidget { background-color: #16213e; color: white; border: 1px solid #0f3460; }
                        QHeaderView::section { background-color: #0f3460; color: white; padding: 5px; }
                        QPushButton { background-color: #0f3460; color: white; border: none; padding: 8px 16px; }
                    """)
                    
                    layout = QVBoxLayout()
                    tabs = QTabWidget()
                    
                    # 今日统计
                    stats_widget = QTableWidget()
                    stats_widget.setColumnCount(3)
                    stats_widget.setHorizontalHeaderLabels(["分类", "时长", "占比"])
                    stats_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                    
                    stats_data = stats_plugin.get_today_stats()
                    stats_widget.setRowCount(len(stats_data))
                    total = sum(s[1] for s in stats_data) if stats_data else 1
                    
                    for i, (cat, dur) in enumerate(stats_data):
                        stats_widget.setItem(i, 0, QTableWidgetItem(cat))
                        from plugins.stats import format_duration
                        stats_widget.setItem(i, 1, QTableWidgetItem(format_duration(dur)))
                        stats_widget.setItem(i, 2, QTableWidgetItem(f"{dur/total*100:.1f}%"))
                    
                    tabs.addTab(stats_widget, "今日统计")
                    
                    # 时间线
                    timeline_widget = QTableWidget()
                    timeline_widget.setColumnCount(4)
                    timeline_widget.setHorizontalHeaderLabels(["时间", "窗口", "分类", "时长"])
                    timeline_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                    
                    timeline_data = stats_plugin.get_today_timeline()
                    timeline_widget.setRowCount(len(timeline_data))
                    
                    for i, (title, proc, cat, start, dur) in enumerate(timeline_data):
                        if isinstance(start, str):
                            start = datetime.fromisoformat(start)
                        timeline_widget.setItem(i, 0, QTableWidgetItem(start.strftime("%H:%M")))
                        timeline_widget.setItem(i, 1, QTableWidgetItem(title[:30]))
                        timeline_widget.setItem(i, 2, QTableWidgetItem(cat))
                        from plugins.stats import format_duration
                        timeline_widget.setItem(i, 3, QTableWidgetItem(format_duration(dur)))
                    
                    tabs.addTab(timeline_widget, "时间线")
                    
                    layout.addWidget(tabs)
                    
                    close_btn = QPushButton("关闭")
                    close_btn.clicked.connect(self.close)
                    layout.addWidget(close_btn)
                    
                    self.setLayout(layout)
            
            dialog = StatsDialog(self.stats)
            dialog.exec_()
        
        except Exception as e:
            self.logger.error(f"显示统计失败: {e}")
    
    def _show_settings(self):
        """显示设置窗口"""
        # 简化版设置，后续可以扩展
        QMessageBox.information(None, "设置", "设置功能开发中...")
    
    def _toggle_autostart(self, checked: bool):
        """切换开机自启动"""
        try:
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
                self.logger.info("已启用开机自启动")
            else:
                try:
                    winreg.DeleteValue(key, "WindowStatus")
                except FileNotFoundError:
                    pass
                self.logger.info("已禁用开机自启动")
            
            winreg.CloseKey(key)
            
            if self.tray:
                self.tray.update_autostart_state(checked)
        
        except Exception as e:
            self.logger.error(f"设置开机自启动失败: {e}")
            QMessageBox.warning(None, "错误", f"设置开机自启动失败: {e}")
    
    def _quit(self):
        """退出应用"""
        try:
            # 记录最后一个活动
            if self.current_start_time and self.current_window:
                duration = int((datetime.now() - self.current_start_time).total_seconds())
                if duration > 0 and self.current_classification:
                    self.stats.log_activity(
                        self.current_window.title,
                        self.current_window.process_name,
                        self.current_classification.category,
                        self.current_start_time,
                        duration
                    )
            
            # 关闭资源
            self.stats.close()
            if self.tray:
                self.tray.destroy()
            
            self.logger.info("WindowStatus 已退出")
            self.app.quit()
        
        except Exception as e:
            self.logger.error(f"退出失败: {e}")
            self.app.quit()


def main():
    """主函数"""
    app = WindowStatusApp()
    sys.exit(app.start())


if __name__ == '__main__':
    main()