# -*- coding: utf-8 -*-
"""
About 插件 - 插件层
提供"关于"窗口，展示应用信息和作者署名
"""

from PyQt5.QtWidgets import QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from plugins.base import Plugin
from plugins.utils import FramelessDialog
from kernel.event_bus import Events
from plugins.common_styles import (
    COLOR_BG_SECONDARY, COLOR_BG_TERTIARY,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BORDER, COLOR_PRIMARY,
    FONT_SIZE_BODY,
    SPACING_SM,
    RADIUS_MD,
)


class AboutDialog(FramelessDialog):
    """关于窗口"""

    STYLESHEET = f"""
        QLabel {{
            color: {COLOR_TEXT_PRIMARY.name()};
        }}
        QPushButton {{
            background-color: {COLOR_BG_SECONDARY.name()};
            color: {COLOR_TEXT_PRIMARY.name()};
            border: 1px solid {COLOR_BORDER.name()};
            padding: {SPACING_SM}px 20px;
            border-radius: {RADIUS_MD}px;
            font-size: {FONT_SIZE_BODY}px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BG_TERTIARY.name()};
        }}
    """

    def __init__(self, version: str = "v3.3.0", parent=None):
        super().__init__(title="关于 WindowStatus", parent=parent)
        self.setFixedSize(420, 340)
        self.setStyleSheet(self.STYLESHEET)

        layout = self.content_layout
        layout.setSpacing(12)
        layout.setContentsMargins(30, 20, 30, 20)

        # 标题
        title = QLabel("WindowStatus")
        title.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 版本
        version_label = QLabel(version)
        version_label.setFont(QFont("Microsoft YaHei UI", 12))
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet(f"color: {COLOR_PRIMARY.name()};")
        layout.addWidget(version_label)

        # 描述
        desc = QLabel(
            "一款轻量的 Windows 窗口状态显示器\n"
            "参考 Discord/Steam 设计，实时显示当前活动窗口的分类状态"
        )
        desc.setFont(QFont("Microsoft YaHei UI", 10))
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY.name()};")
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
        author2.setStyleSheet(f"color: {COLOR_PRIMARY.name()};")
        layout.addWidget(author2)

        # GitHub 链接
        github_link = QLabel(
            f'<a href="https://github.com/qiuyuehu/WindowStatus"'
            f' style="color: {COLOR_PRIMARY.name()};">GitHub 仓库</a>'
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
        
        self._dialog = None
        self.event_bus.on(Events.SHOW_ABOUT, self._on_show_about)
        self.logger.info("About 插件已加载")

    def on_unload(self):
        """插件卸载"""
        self.event_bus.off(Events.SHOW_ABOUT, self._on_show_about)
        if self._dialog is not None:
            self._dialog.close()
            self._dialog = None
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
            # 防重复弹出：如果对话框已存在，则提升并激活
            if self._dialog is not None:
                self._dialog.raise_()
                self._dialog.activateWindow()
                return

            # 从配置读取版本号
            version = self.config.get("version", "v3.3.0")
            if not version.startswith("v"):
                version = f"v{version}"
            
            parent = self.main_window
            self._dialog = AboutDialog(version=version, parent=parent)
            self._dialog.exec_()
            self._dialog = None
        except Exception as e:
            self._dialog = None
            self.logger.error(f"About 插件: 显示关于窗口失败: {e}")


# 约定：PluginClass 变量指向插件类
PluginClass = AboutPlugin
