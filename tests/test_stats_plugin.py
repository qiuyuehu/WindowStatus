# -*- coding: utf-8 -*-
"""
Stats 插件单元测试（使用内存数据库）
"""

import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.stats.plugin import StatsPlugin


class TestStatsPluginDB(unittest.TestCase):
    """测试 Stats 插件数据库操作"""

    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_kernel.event_bus = MagicMock()
        self.mock_kernel.config = MagicMock()
        self.mock_kernel.logger = MagicMock()
        self.mock_kernel.db_path = ":memory:"
        self.plugin = StatsPlugin(self.mock_kernel)
        self.plugin.on_load()

    def tearDown(self):
        self.plugin.close()

    def test_connect(self):
        """数据库连接成功"""
        self.assertIsNotNone(self.plugin.conn)

    def test_create_tables(self):
        """创建表结构"""
        cursor = self.plugin.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        self.assertIn("activity_log", tables)
        self.assertIn("daily_stats", tables)
        self.assertIn("weekly_stats", tables)
        self.assertIn("monthly_stats", tables)

    def test_get_today_stats_empty(self):
        """今日统计（无数据时返回空）"""
        result = self.plugin.get_today_stats()
        self.assertEqual(result, [])

    def test_get_week_stats_empty(self):
        """本周统计（无数据时返回空）"""
        result = self.plugin.get_week_stats()
        self.assertEqual(result, [])

    def test_get_month_stats_empty(self):
        """本月统计（无数据时返回空）"""
        result = self.plugin.get_month_stats()
        self.assertEqual(result, [])

    def test_get_yesterday_stats_empty(self):
        """昨日统计（无数据时返回空）"""
        result = self.plugin.get_yesterday_stats()
        self.assertEqual(result, [])

    def test_get_today_timeline_empty(self):
        """今日时间线（无数据时返回空）"""
        result = self.plugin.get_today_timeline()
        self.assertEqual(result, [])


class TestStatsPluginActivity(unittest.TestCase):
    """测试 Stats 插件活动记录"""

    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_kernel.event_bus = MagicMock()
        self.mock_kernel.config = MagicMock()
        self.mock_kernel.logger = MagicMock()
        self.mock_kernel.db_path = ":memory:"
        self.plugin = StatsPlugin(self.mock_kernel)
        self.plugin.on_load()

    def tearDown(self):
        self.plugin.close()

    def test_log_activity(self):
        """记录活动到数据库"""
        self.plugin.log_activity(
            window_title="VS Code",
            process_name="code.exe",
            category="开发",
            start_time=datetime.now() - timedelta(minutes=30),
            duration=1800
        )
        cursor = self.plugin.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM activity_log")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

    def test_aggregate_daily(self):
        """聚合每日数据"""
        now = datetime.now()
        # 插入测试数据
        self.plugin.log_activity(
            window_title="Test", process_name="test.exe",
            category="开发", start_time=now - timedelta(hours=1),
            duration=3600
        )
        # 聚合
        self.plugin._aggregate_daily(now.date())
        cursor = self.plugin.conn.cursor()
        cursor.execute("SELECT total_duration FROM daily_stats WHERE category='开发'")
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 3600)


class TestStatsPluginEvents(unittest.TestCase):
    """测试 Stats 插件事件处理"""

    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_kernel.event_bus = MagicMock()
        self.mock_kernel.config = MagicMock()
        self.mock_kernel.logger = MagicMock()
        self.mock_kernel.db_path = ":memory:"
        self.plugin = StatsPlugin(self.mock_kernel)
        self.plugin.on_load()

    def tearDown(self):
        self.plugin.close()

    def test_on_category_matched(self):
        """处理分类匹配事件"""
        self.plugin._on_category_matched(
            category="开发", icon="💻", color=(78, 205, 196),
            title="VS Code", process_name="code.exe"
        )
        self.assertEqual(self.plugin._current_category, "开发")
        self.assertEqual(self.plugin._current_title, "VS Code")

    def test_on_idle_detected(self):
        """处理空闲检测事件"""
        # 先设置当前活动
        self.plugin._current_category = "开发"
        self.plugin._current_start_time = datetime.now() - timedelta(minutes=10)
        self.plugin._on_idle_detected()
        self.assertTrue(self.plugin._is_idle)

    def test_on_idle_resumed(self):
        """处理空闲恢复事件"""
        self.plugin._is_idle = True
        self.plugin._current_category = "开发"
        self.plugin._current_start_time = datetime.now() - timedelta(minutes=30)
        self.plugin._on_idle_resumed()
        self.assertFalse(self.plugin._is_idle)


if __name__ == "__main__":
    unittest.main()
