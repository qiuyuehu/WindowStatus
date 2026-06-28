# -*- coding: utf-8 -*-
"""
Common Styles 单元测试
测试 oklch 配色系统和样式常量
"""

import unittest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtGui import QColor

from plugins.common_styles import (
    oklch_to_qcolor,
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_PRESSED,
    COLOR_BG_PRIMARY, COLOR_BG_SECONDARY, COLOR_BG_TERTIARY,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_BORDER, COLOR_BORDER_SUBTLE,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_CAPTION,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
)


class TestOklchToQColor(unittest.TestCase):
    """测试 oklch 到 QColor 转换"""

    def test_returns_qcolor(self):
        """返回值是 QColor 类型"""
        result = oklch_to_qcolor(0.7, 0.15, 70)
        self.assertIsInstance(result, QColor)

    def test_valid_rgb_range(self):
        """RGB 值在 0-255 范围内"""
        for l_val in [0.3, 0.5, 0.7, 0.9]:
            for c_val in [0.05, 0.15, 0.25]:
                for h_val in [0, 70, 145, 230, 300]:
                    color = oklch_to_qcolor(l_val, c_val, h_val)
                    self.assertGreaterEqual(color.red(), 0)
                    self.assertLessEqual(color.red(), 255)
                    self.assertGreaterEqual(color.green(), 0)
                    self.assertLessEqual(color.green(), 255)
                    self.assertGreaterEqual(color.blue(), 0)
                    self.assertLessEqual(color.blue(), 255)

    def test_different_hues_produce_different_colors(self):
        """不同色相产生不同颜色"""
        red = oklch_to_qcolor(0.7, 0.15, 25)
        green = oklch_to_qcolor(0.7, 0.15, 145)
        self.assertTrue(
            abs(red.red() - green.red()) > 30 or
            abs(red.green() - green.green()) > 30
        )

    def test_zero_chroma_produces_gray(self):
        """零饱和度产生灰色"""
        gray = oklch_to_qcolor(0.5, 0, 0)
        # R/G/B 应该接近
        self.assertAlmostEqual(gray.red(), gray.green(), delta=5)
        self.assertAlmostEqual(gray.green(), gray.blue(), delta=5)


class TestColorConstants(unittest.TestCase):
    """测试颜色常量定义"""

    def test_all_colors_are_qcolor(self):
        """所有颜色常量都是 QColor 类型"""
        colors = [
            COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_PRESSED,
            COLOR_BG_PRIMARY, COLOR_BG_SECONDARY, COLOR_BG_TERTIARY,
            COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
            COLOR_BORDER, COLOR_BORDER_SUBTLE,
            COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR,
        ]
        for color in colors:
            self.assertIsInstance(color, QColor, f"{color} 不是 QColor")

    def test_bg_colors_are_dark(self):
        """背景色是深色"""
        self.assertLess(COLOR_BG_PRIMARY.red(), 50)
        self.assertLess(COLOR_BG_SECONDARY.red(), 50)
        self.assertLess(COLOR_BG_TERTIARY.red(), 50)

    def test_text_primary_is_light(self):
        """主文字颜色是亮色"""
        self.assertGreater(COLOR_TEXT_PRIMARY.red(), 200)

    def test_text_secondary_is_medium(self):
        """次要文字颜色是中等亮度"""
        self.assertGreater(COLOR_TEXT_SECONDARY.red(), 100)
        self.assertLess(COLOR_TEXT_SECONDARY.red(), 200)

    def test_primary_is_distinct_from_bg(self):
        """主色和背景色有明显差异"""
        self.assertNotEqual(COLOR_PRIMARY.name(), COLOR_BG_PRIMARY.name())

    def test_border_darker_than_bg(self):
        """边框颜色比背景色深或相同"""
        self.assertLessEqual(COLOR_BORDER.red(), COLOR_BG_SECONDARY.red() + 20)

    def test_status_colors_distinct(self):
        """三种状态色互不相同"""
        self.assertNotEqual(COLOR_SUCCESS.name(), COLOR_WARNING.name())
        self.assertNotEqual(COLOR_WARNING.name(), COLOR_ERROR.name())
        self.assertNotEqual(COLOR_SUCCESS.name(), COLOR_ERROR.name())


class TestSpacingConstants(unittest.TestCase):
    """测试间距常量"""

    def test_spacing_ordering(self):
        """间距从小到大排列"""
        self.assertLess(SPACING_XS, SPACING_SM)
        self.assertLess(SPACING_SM, SPACING_MD)
        self.assertLess(SPACING_MD, SPACING_LG)
        self.assertLess(SPACING_LG, SPACING_XL)

    def test_spacing_positive(self):
        """所有间距为正数"""
        for s in [SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL]:
            self.assertGreater(s, 0)


class TestRadiusConstants(unittest.TestCase):
    """测试圆角常量"""

    def test_radius_ordering(self):
        """圆角从小到大排列"""
        self.assertLess(RADIUS_SM, RADIUS_MD)
        self.assertLess(RADIUS_MD, RADIUS_LG)
        self.assertLess(RADIUS_LG, RADIUS_XL)

    def test_radius_positive(self):
        """所有圆角为正数"""
        for r in [RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL]:
            self.assertGreater(r, 0)


class TestFontSizeConstants(unittest.TestCase):
    """测试字体大小常量"""

    def test_font_size_ordering(self):
        """字体大小从大到小排列"""
        self.assertGreater(FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE)
        self.assertGreater(FONT_SIZE_SUBTITLE, FONT_SIZE_BODY)
        self.assertGreater(FONT_SIZE_BODY, FONT_SIZE_CAPTION)

    def test_font_size_positive(self):
        """所有字体大小为正数"""
        for s in [FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_CAPTION]:
            self.assertGreater(s, 0)


if __name__ == "__main__":
    unittest.main()
