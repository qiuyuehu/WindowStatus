# -*- coding: utf-8 -*-
"""
Overlay 单元测试
测试 OverlayWidget 常量和主题配置（不创建 QWidget 实例）
"""

import unittest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.overlay.plugin import OverlayWidget


class TestOverlayWidgetConstants(unittest.TestCase):
    """测试 OverlayWidget 类常量"""

    def test_bubble_dimensions(self):
        """气泡尺寸为正数"""
        self.assertGreater(OverlayWidget.BUBBLE_WIDTH, 0)
        self.assertGreater(OverlayWidget.BUBBLE_HEIGHT, 0)
        self.assertGreater(OverlayWidget.BUBBLE_RADIUS, 0)
        self.assertGreater(OverlayWidget.DOT_RADIUS, 0)

    def test_timer_intervals(self):
        """定时器间隔为正数"""
        self.assertGreater(OverlayWidget.DURATION_INTERVAL_MS, 0)
        self.assertGreater(OverlayWidget.TOPMOST_INTERVAL_MS, 0)

    def test_bubble_width_greater_than_height(self):
        """气泡宽度大于高度（横长形）"""
        self.assertGreater(OverlayWidget.BUBBLE_WIDTH, OverlayWidget.BUBBLE_HEIGHT)

    def test_window_flags_include_frameless(self):
        """窗口标志包含无边框"""
        self.assertTrue(OverlayWidget.WINDOW_FLAGS & 0x00000800)  # Qt.FramelessWindowHint


if __name__ == "__main__":
    unittest.main()
