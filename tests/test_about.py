# -*- coding: utf-8 -*-
"""
About 插件单元测试
"""

import unittest
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.about.plugin import AboutPlugin


class TestAboutPlugin(unittest.TestCase):
    """测试 About 插件"""

    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_kernel.event_bus = MagicMock()
        self.mock_kernel.config = MagicMock()
        self.mock_kernel.logger = MagicMock()
        self.mock_kernel.plugin_manager = MagicMock()
        self.plugin = AboutPlugin(self.mock_kernel)

    def test_plugin_metadata(self):
        """插件元信息"""
        self.assertEqual(self.plugin.name, "about")
        self.assertEqual(self.plugin.version, "1.0.0")

    def test_on_load_registers_event(self):
        """on_load 注册 SHOW_ABOUT 事件"""
        self.plugin.on_load()
        self.mock_kernel.event_bus.on.assert_called_once()

    def test_on_unload_unregisters_event(self):
        """on_unload 注销 SHOW_ABOUT 事件"""
        self.plugin.on_load()
        self.plugin.on_unload()
        self.mock_kernel.event_bus.off.assert_called_once()

    def test_on_show_about_with_existing_dialog(self):
        """重复弹出时提升已有对话框"""
        mock_dialog = MagicMock()
        self.plugin._dialog = mock_dialog
        self.plugin._on_show_about()
        mock_dialog.raise_.assert_called_once()
        mock_dialog.activateWindow.assert_called_once()

    def test_on_show_about_clears_dialog_on_error(self):
        """弹窗出错时清理对话框引用"""
        self.mock_kernel.config.get.return_value = "v3.3.0"
        self.mock_kernel.main_window = None
        # exec_ 会抛异常（没有 QApplication），但 _dialog 应该被清理
        self.plugin._on_show_about()
        # 出错后 _dialog 应该被设为 None
        self.assertIsNone(self.plugin._dialog)


if __name__ == "__main__":
    unittest.main()
