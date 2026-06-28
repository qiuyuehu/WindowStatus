# -*- coding: utf-8 -*-
"""
Kernel 核心类单元测试
"""

import unittest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKernelInit(unittest.TestCase):
    """测试 Kernel 初始化"""

    @patch('kernel.core.PluginManager')
    @patch('kernel.core.Config')
    @patch('kernel.core.EventBus')
    def test_init_creates_event_bus(self, mock_eb_cls, mock_cfg_cls, mock_pm_cls):
        """初始化创建 EventBus"""
        from kernel.core import Kernel
        kernel = Kernel('/tmp/config.json', '/tmp/data.db', '/tmp/log.txt')
        self.assertIs(kernel.event_bus, mock_eb_cls.return_value)

    @patch('kernel.core.PluginManager')
    @patch('kernel.core.Config')
    @patch('kernel.core.EventBus')
    def test_init_creates_config(self, mock_eb_cls, mock_cfg_cls, mock_pm_cls):
        """初始化创建 Config"""
        from kernel.core import Kernel
        kernel = Kernel('/tmp/config.json', '/tmp/data.db', '/tmp/log.txt')
        mock_cfg_cls.assert_called_once_with('/tmp/config.json')

    @patch('kernel.core.PluginManager')
    @patch('kernel.core.Config')
    @patch('kernel.core.EventBus')
    def test_init_creates_plugin_manager(self, mock_eb_cls, mock_cfg_cls, mock_pm_cls):
        """初始化创建 PluginManager"""
        from kernel.core import Kernel
        kernel = Kernel('/tmp/config.json', '/tmp/data.db', '/tmp/log.txt')
        mock_pm_cls.assert_called_once_with(kernel)

    @patch('kernel.core.PluginManager')
    @patch('kernel.core.Config')
    @patch('kernel.core.EventBus')
    def test_set_qt_app(self, mock_eb_cls, mock_cfg_cls, mock_pm_cls):
        """设置 QApplication 引用"""
        from kernel.core import Kernel
        kernel = Kernel('/tmp/config.json', '/tmp/data.db', '/tmp/log.txt')
        mock_app = MagicMock()
        kernel.set_qt_app(mock_app)
        kernel.event_bus.set_qt_app.assert_called_once_with(mock_app)

    @patch('kernel.core.PluginManager')
    @patch('kernel.core.Config')
    @patch('kernel.core.EventBus')
    def test_start_calls_load_plugins(self, mock_eb_cls, mock_cfg_cls, mock_pm_cls):
        """start() 调用 load_plugins"""
        from kernel.core import Kernel
        kernel = Kernel('/tmp/config.json', '/tmp/data.db', '/tmp/log.txt')
        kernel.load_plugins = MagicMock()
        kernel.start()
        kernel.load_plugins.assert_called_once()

    @patch('kernel.core.PluginManager')
    @patch('kernel.core.Config')
    @patch('kernel.core.EventBus')
    def test_stop_unloads_plugins(self, mock_eb_cls, mock_cfg_cls, mock_pm_cls):
        """stop() 卸载插件并清理事件总线"""
        from kernel.core import Kernel
        kernel = Kernel('/tmp/config.json', '/tmp/data.db', '/tmp/log.txt')
        kernel.unload_plugins = MagicMock()
        kernel.stop()
        kernel.unload_plugins.assert_called_once()
        kernel.event_bus.off_all_handlers.assert_called_once()


if __name__ == "__main__":
    unittest.main()
