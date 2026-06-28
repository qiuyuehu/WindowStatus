# -*- coding: utf-8 -*-
"""
Tray 插件单元测试
"""

import unittest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.tray.plugin import TrayPlugin


class TestTrayPluginInit(unittest.TestCase):
    """测试 Tray 插件初始化"""

    @patch('plugins.tray.plugin.QSystemTrayIcon')
    @patch('plugins.tray.plugin.QMenu')
    def test_plugin_metadata(self, mock_menu, mock_tray):
        """插件元信息"""
        mock_kernel = MagicMock()
        mock_kernel.event_bus = MagicMock()
        mock_kernel.config = MagicMock()
        mock_kernel.config.is_always_on_top.return_value = True
        mock_kernel.config.get.return_value = 0.9
        mock_kernel.config.is_minimize_to_tray.return_value = True
        mock_kernel.logger = MagicMock()
        plugin = TrayPlugin(mock_kernel)
        self.assertEqual(plugin.name, "tray")
        self.assertEqual(plugin.version, "1.0.0")

    @patch('plugins.tray.plugin.QSystemTrayIcon')
    @patch('plugins.tray.plugin.QMenu')
    def test_on_load_registers_events(self, mock_menu, mock_tray):
        """on_load 注册事件监听"""
        mock_kernel = MagicMock()
        mock_kernel.event_bus = MagicMock()
        mock_kernel.config = MagicMock()
        mock_kernel.config.is_always_on_top.return_value = True
        mock_kernel.config.get.return_value = 0.9
        mock_kernel.config.is_minimize_to_tray.return_value = True
        mock_kernel.logger = MagicMock()
        plugin = TrayPlugin(mock_kernel)
        plugin.on_load()
        mock_kernel.event_bus.on.assert_called()

    @patch('plugins.tray.plugin.QSystemTrayIcon')
    @patch('plugins.tray.plugin.QMenu')
    def test_on_unload_unregisters_events(self, mock_menu, mock_tray):
        """on_unload 注销事件监听"""
        mock_kernel = MagicMock()
        mock_kernel.event_bus = MagicMock()
        mock_kernel.config = MagicMock()
        mock_kernel.config.is_always_on_top.return_value = True
        mock_kernel.config.get.return_value = 0.9
        mock_kernel.config.is_minimize_to_tray.return_value = True
        mock_kernel.logger = MagicMock()
        plugin = TrayPlugin(mock_kernel)
        plugin.on_load()
        plugin.on_unload()
        mock_kernel.event_bus.off.assert_called()


if __name__ == "__main__":
    unittest.main()
