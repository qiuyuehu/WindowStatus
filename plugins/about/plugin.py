# -*- coding: utf-8 -*-
"""
About 插件 - 插件层
提供"关于"窗口，展示应用信息和作者署名
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from plugins.base import Plugin
from kernel.event_bus import Events


class AboutDialog(QDialog):
    """关于窗口"""

    STYLESHEET = """
        QDialog {
            background-color: #1a1a2e;
            color: white;
        }
        QLabel {
            color: white;
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 WindowStatus")
        self.setFixedSize(400, 300)
        self.setStyleSheet(self.STYLESHEET)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 标题
        title = QLabel("WindowStatus")
        title.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 版本
        version = QLabel("v3.1.0")
        version.setFont(QFont("Microsoft YaHei UI", 12))
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #4ECDC4;")
        layout.addWidget(version)

        # 描述
        desc = QLabel(
            "一款轻量的 Windows 窗口状态显示器\n"
            "参考 Discord/Steam 设计，实时显示当前活动窗口的分类状态"
        )
        desc.setFont(QFont("Microsoft YaHei UI", 10))
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #b8b8b8;")
        layout.addWidget(desc)

        # 署名
        layout.addSpacing(10)

        author1 = QLabel("作者：qiuyuehu")
        author1.setFont(QFont("Microsoft YaHei UI", 10))
        author1.setAlignment(Qt.AlignCenter)
        layout.addWidget(author1)

        author2 = QLabel("开发与设计：衾衾 (Hermes Agent)")
        author2.setFont(QFont("Microsoft YaHei UI", 10))
        author2.setAlignment(Qt.AlignCenter)
        author2.setStyleSheet("color: #4ECDC4;")
        layout.addWidget(author2)

        # GitHub 链接
        github_link = QLabel(
            '<a href="https://github.com/qiuyuehu/WindowStatus"'
            ' style="color: #4ECDC4;">GitHub 仓库</a>'
        )
        github_link.setFont(QFont("Microsoft YaHei UI", 10))
        github_link.setAlignment(Qt.AlignCenter)
        github_link.setOpenExternalLinks(True)
        layout.addWidget(github_link)

        # 关闭按钮
        layout.addSpacing(10)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)


class AboutPlugin(Plugin):
    """
    关于窗口插件

    职责：
    - 监听 SHOW_ABOUT 事件
    - 展示应用信息和作者署名
    """

    name = "about"
    version = "1.0.0"
    description = "关于窗口插件，展示应用信息"

    def on_load(self):
        """插件加载"""
        self.logger = self.kernel.logger
        self.event_bus.on(Events.SHOW_ABOUT, self._on_show_about)
        self.logger.info("About 插件已加载")

    def on_unload(self):
        """插件卸载"""
        self.event_bus.off(Events.SHOW_ABOUT, self._on_show_about)
        self.logger.info("About 插件已卸载")

    def on_enable(self):
        """插件启用"""
        self.logger.info("About 插件已启用")

    def on_disable(self):
        """插件禁用"""
        self.logger.info("About 插件已禁用")

    def _on_show_about(self, **kwargs):
        """显示关于窗口"""
        try:
            dialog = AboutDialog()
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"About 插件: 显示关于窗口失败: {e}")


# 约定：PluginClass 变量指向插件类
PluginClass = AboutPlugin
