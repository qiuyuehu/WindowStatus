# -*- coding: utf-8 -*-
"""
WindowStatus — Windows 窗口状态显示器
Author: 衾衾 (Hermes Agent)

v3.0 - 完整插件化架构
- 事件总线驱动
- 插件动态加载
- 线程安全
"""

import sys
import os
from typing import Optional

from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt5.QtCore import Qt

from kernel.core import Kernel
from kernel.event_bus import Events


# 配置文件路径
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.WindowStatus')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
DB_FILE = os.path.join(CONFIG_DIR, 'data.db')
LOG_FILE = os.path.join(CONFIG_DIR, 'window_status.log')


class WindowStatusApp:
    """
    WindowStatus 主应用
    
    v3.0 架构：
    - 只负责组装 Kernel 和启动 Qt 应用
    - 所有业务逻辑由插件处理
    - 通过事件总线进行插件间通信
    """
    
    def __init__(self):
        # 初始化 Qt 应用
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # 初始化 Kernel
        self.kernel = Kernel(CONFIG_FILE, DB_FILE, LOG_FILE)
        self.kernel.set_qt_app(self.app)
        
        # 注册应用级事件处理
        self._register_app_events()
    
    def _register_app_events(self):
        """注册应用级事件处理"""
        # 退出事件
        self.kernel.event_bus.on(Events.QUIT, self._on_quit)
        
        # 显示统计窗口
        self.kernel.event_bus.on(Events.SHOW_STATS, self._on_show_stats)
        
        # 显示设置窗口
        self.kernel.event_bus.on(Events.SHOW_SETTINGS, self._on_show_settings)
        
        # 显示关于窗口
        self.kernel.event_bus.on(Events.SHOW_ABOUT, self._on_show_about)
    
    def start(self) -> int:
        """启动应用"""
        try:
            self.kernel.logger.info("WindowStatus 启动中...")
            
            # 启动 Kernel（加载插件）
            self.kernel.start()
            
            self.kernel.logger.info("WindowStatus 启动完成")
            
            # 运行 Qt 应用
            return self.app.exec_()
        
        except Exception as e:
            self.kernel.logger.exception(f"启动失败: {e}")
            QMessageBox.critical(None, "错误", f"启动失败: {e}")
            return 1
    
    def _on_quit(self, **kwargs):
        """处理退出事件"""
        try:
            self.kernel.logger.info("WindowStatus 退出中...")
            
            # 停止 Kernel
            self.kernel.stop()
            
            # 退出 Qt 应用
            self.app.quit()
        
        except Exception as e:
            self.kernel.logger.error(f"退出失败: {e}")
            self.app.quit()
    
    def _on_show_stats(self, **kwargs):
        """显示统计窗口"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
            from datetime import datetime
            
            # 获取 Stats 插件
            stats_plugin = self.kernel.plugin_manager.get_plugin("stats")
            if not stats_plugin:
                QMessageBox.information(None, "统计", "统计插件未加载")
                return
            
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
                        from plugins.stats.plugin import format_duration
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
                        from plugins.stats.plugin import format_duration
                        timeline_widget.setItem(i, 3, QTableWidgetItem(format_duration(dur)))
                    
                    tabs.addTab(timeline_widget, "时间线")
                    
                    layout.addWidget(tabs)
                    
                    close_btn = QPushButton("关闭")
                    close_btn.clicked.connect(self.close)
                    layout.addWidget(close_btn)
                    
                    self.setLayout(layout)
            
            dialog = StatsDialog(stats_plugin)
            dialog.exec_()
        
        except Exception as e:
            self.kernel.logger.error(f"显示统计失败: {e}")
    
    def _on_show_settings(self, **kwargs):
        """显示设置窗口"""
        QMessageBox.information(None, "设置", "设置功能开发中...")
    
    def _on_show_about(self, **kwargs):
        """显示关于窗口"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QFont
            
            class AboutDialog(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("关于 WindowStatus")
                    self.setFixedSize(400, 300)
                    self.setStyleSheet("""
                        QDialog { background-color: #1a1a2e; color: white; }
                        QLabel { color: white; }
                        QPushButton { 
                            background-color: #0f3460; color: white; 
                            border: none; padding: 8px 16px; 
                            border-radius: 4px;
                        }
                        QPushButton:hover { background-color: #1a4a8a; }
                    """)
                    
                    layout = QVBoxLayout()
                    layout.setSpacing(15)
                    
                    # 标题
                    title = QLabel("WindowStatus")
                    title.setFont(QFont('Microsoft YaHei UI', 20, QFont.Bold))
                    title.setAlignment(Qt.AlignCenter)
                    layout.addWidget(title)
                    
                    # 版本
                    version = QLabel("v3.0.0")
                    version.setFont(QFont('Microsoft YaHei UI', 12))
                    version.setAlignment(Qt.AlignCenter)
                    version.setStyleSheet("color: #4ECDC4;")
                    layout.addWidget(version)
                    
                    # 描述
                    desc = QLabel("一款轻量的 Windows 窗口状态显示器\n参考 Discord/Steam 设计，实时显示当前活动窗口的分类状态")
                    desc.setFont(QFont('Microsoft YaHei UI', 10))
                    desc.setAlignment(Qt.AlignCenter)
                    desc.setStyleSheet("color: #b8b8b8;")
                    layout.addWidget(desc)
                    
                    # 署名
                    layout.addSpacing(10)
                    
                    author1 = QLabel("作者：qiuyuehu")
                    author1.setFont(QFont('Microsoft YaHei UI', 10))
                    author1.setAlignment(Qt.AlignCenter)
                    layout.addWidget(author1)
                    
                    author2 = QLabel("开发与设计：衾衾 (Hermes Agent)")
                    author2.setFont(QFont('Microsoft YaHei UI', 10))
                    author2.setAlignment(Qt.AlignCenter)
                    author2.setStyleSheet("color: #4ECDC4;")
                    layout.addWidget(author2)
                    
                    # GitHub 链接
                    github_link = QLabel('<a href="https://github.com/qiuyuehu/WindowStatus" style="color: #4ECDC4;">GitHub 仓库</a>')
                    github_link.setFont(QFont('Microsoft YaHei UI', 10))
                    github_link.setAlignment(Qt.AlignCenter)
                    github_link.setOpenExternalLinks(True)
                    layout.addWidget(github_link)
                    
                    # 关闭按钮
                    layout.addSpacing(10)
                    close_btn = QPushButton("关闭")
                    close_btn.clicked.connect(self.close)
                    layout.addWidget(close_btn, alignment=Qt.AlignCenter)
                    
                    self.setLayout(layout)
            
            dialog = AboutDialog()
            dialog.exec_()
        
        except Exception as e:
            self.kernel.logger.error(f"显示关于窗口失败: {e}")


def main():
    """主函数"""
    app = WindowStatusApp()
    sys.exit(app.start())


if __name__ == '__main__':
    main()
