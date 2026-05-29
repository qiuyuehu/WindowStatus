# -*- coding: utf-8 -*-
"""
Utils 单元测试
"""

import unittest
from datetime import datetime

# 添加项目根目录到路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.utils import format_duration, truncate_text, format_timestamp


class TestFormatDuration(unittest.TestCase):
    """测试 format_duration"""
    
    def test_seconds(self):
        """测试秒数格式化"""
        self.assertEqual(format_duration(0), "0秒")
        self.assertEqual(format_duration(30), "30秒")
        self.assertEqual(format_duration(59), "59秒")
    
    def test_minutes(self):
        """测试分钟格式化"""
        self.assertEqual(format_duration(60), "1分钟")
        self.assertEqual(format_duration(90), "1分钟")
        self.assertEqual(format_duration(120), "2分钟")
        self.assertEqual(format_duration(3599), "59分钟")
    
    def test_hours(self):
        """测试小时格式化"""
        self.assertEqual(format_duration(3600), "1小时")
        self.assertEqual(format_duration(3660), "1小时1分钟")
        self.assertEqual(format_duration(7200), "2小时")
        self.assertEqual(format_duration(7320), "2小时2分钟")


class TestTruncateText(unittest.TestCase):
    """测试 truncate_text"""
    
    def test_short_text(self):
        """测试短文本"""
        self.assertEqual(truncate_text("Hello", 10), "Hello")
        self.assertEqual(truncate_text("Hello", 5), "Hello")
    
    def test_long_text(self):
        """测试长文本"""
        self.assertEqual(truncate_text("Hello World", 8), "Hello...")
        self.assertEqual(truncate_text("Hello World", 10), "Hello W...")
    
    def test_exact_length(self):
        """测试精确长度"""
        self.assertEqual(truncate_text("Hello", 5), "Hello")
        self.assertEqual(truncate_text("Hello", 4), "H...")
    
    def test_custom_max_length(self):
        """测试自定义最大长度"""
        self.assertEqual(truncate_text("Hello World", 6), "Hel...")


class TestFormatTimestamp(unittest.TestCase):
    """测试 format_timestamp"""
    
    def test_datetime(self):
        """测试 datetime 对象"""
        dt = datetime(2026, 5, 28, 14, 30)
        self.assertEqual(format_timestamp(dt), "14:30")
    
    def test_none(self):
        """测试 None"""
        self.assertEqual(format_timestamp(None), "")
    
    def test_string(self):
        """测试字符串"""
        self.assertEqual(format_timestamp("2026-05-28T14:30:00"), "14:30")
    
    def test_custom_format(self):
        """测试自定义格式"""
        dt = datetime(2026, 5, 28, 14, 30)
        self.assertEqual(format_timestamp(dt, "%Y-%m-%d %H:%M"), "2026-05-28 14:30")


if __name__ == "__main__":
    unittest.main()
