# -*- coding: utf-8 -*-
"""
Stats 插件 - 插件层
记录和查询使用统计数据
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from plugins.base import Plugin
from kernel.event_bus import Events


def format_duration(seconds: int) -> str:
    """格式化时长"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分钟"


class StatsPlugin(Plugin):
    """
    统计插件
    
    职责：
    - 监听 CATEGORY_MATCHED 事件
    - 记录窗口使用时长
    - 提供统计数据查询
    """
    
    name = "stats"
    version = "1.0.0"
    description = "统计插件，记录和查询使用统计数据"
    
    def __init__(self, kernel):
        super().__init__(kernel)
        
        self.db_path = kernel.db_path
        self.conn: Optional[sqlite3.Connection] = None
        
        # 当前活动记录
        self._current_title: Optional[str] = None
        self._current_process: Optional[str] = None
        self._current_category: Optional[str] = None
        self._current_start_time: Optional[datetime] = None
    
    def on_load(self):
        """插件加载"""
        self.logger = self.kernel.logger
        
        # 确保目录存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # 连接数据库
        self._connect()
        self._create_tables()
        
        # 注册事件监听
        self.event_bus.on(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.on(Events.QUIT, self._on_quit)
        
        self.logger.info(f"Stats 插件已加载，数据库: {self.db_path}")
    
    def on_unload(self):
        """插件卸载"""
        # 注销事件监听
        self.event_bus.off(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.off(Events.QUIT, self._on_quit)
        
        # 记录最后一个活动
        self._record_current_activity()
        
        # 关闭数据库
        self.close()
        
        self.logger.info("Stats 插件已卸载")
    
    def on_enable(self):
        """插件启用"""
        self.logger.info("Stats 插件已启用")
    
    def on_disable(self):
        """插件禁用"""
        # 记录当前活动
        self._record_current_activity()
        self.logger.info("Stats 插件已禁用")
    
    def _connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            self.logger.error(f"Stats 插件: 数据库连接失败: {e}")
            self.conn = None
    
    def _create_tables(self):
        """创建表"""
        if not self.conn:
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    window_title TEXT,
                    process_name TEXT,
                    category TEXT,
                    start_time DATETIME,
                    end_time DATETIME,
                    duration INTEGER
                )
            ''')
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Stats 插件: 创建表失败: {e}")
    
    def _on_category_matched(self, **kwargs):
        """处理分类匹配事件"""
        if not self.enabled:
            return
        
        # 记录上一个活动
        self._record_current_activity()
        
        # 更新当前活动
        self._current_title = kwargs.get('title', '')
        self._current_process = kwargs.get('process_name', '')
        self._current_category = kwargs.get('category', '其他')
        self._current_start_time = datetime.now()
        
        self.logger.debug(f"Stats 插件: 开始记录 [{self._current_category}] {self._current_title[:30]}")
    
    def _on_quit(self, **kwargs):
        """处理退出事件"""
        self._record_current_activity()
    
    def _record_current_activity(self):
        """记录当前活动"""
        if not self._current_start_time or not self._current_title:
            return
        
        duration = int((datetime.now() - self._current_start_time).total_seconds())
        if duration <= 0:
            return
        
        self.log_activity(
            self._current_title,
            self._current_process,
            self._current_category,
            self._current_start_time,
            duration
        )
        
        # 重置当前活动
        self._current_title = None
        self._current_process = None
        self._current_category = None
        self._current_start_time = None
    
    def log_activity(self, window_title: str, process_name: str, 
                     category: str, start_time: datetime, duration: int):
        """
        记录活动
        
        Args:
            window_title: 窗口标题
            process_name: 进程名
            category: 分类
            start_time: 开始时间
            duration: 持续时间（秒）
        """
        if not self.conn:
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO activity_log (window_title, process_name, category, start_time, end_time, duration)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (window_title, process_name, category, start_time, 
                  start_time + timedelta(seconds=duration), duration))
            self.conn.commit()
            
            # 发送统计记录事件
            self.event_bus.emit(
                Events.STATS_RECORDED,
                window_title=window_title,
                process_name=process_name,
                category=category,
                duration=duration
            )
            
        except Exception as e:
            self.logger.error(f"Stats 插件: 记录活动失败: {e}")
    
    def get_today_stats(self) -> List[Tuple[str, int]]:
        """
        获取今日统计
        
        Returns:
            List[Tuple[str, int]]: [(分类, 总时长), ...]
        """
        if not self.conn:
            return []
        
        try:
            today = datetime.now().date()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT category, SUM(duration) as total_duration
                FROM activity_log
                WHERE DATE(start_time) = ?
                GROUP BY category
                ORDER BY total_duration DESC
            ''', (today,))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Stats 插件: 获取今日统计失败: {e}")
            return []
    
    def get_today_timeline(self, limit: int = 50) -> List[Tuple]:
        """
        获取今日时间线
        
        Args:
            limit: 返回记录数限制
        
        Returns:
            List[Tuple]: [(窗口标题, 进程名, 分类, 开始时间, 时长), ...]
        """
        if not self.conn:
            return []
        
        try:
            today = datetime.now().date()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT window_title, process_name, category, start_time, duration
                FROM activity_log
                WHERE DATE(start_time) = ?
                ORDER BY start_time DESC
                LIMIT ?
            ''', (today, limit))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Stats 插件: 获取时间线失败: {e}")
            return []
    
    def get_recent_activity(self, limit: int = 10) -> List[Tuple]:
        """
        获取最近活动
        
        Args:
            limit: 返回记录数限制
        
        Returns:
            List[Tuple]: [(窗口标题, 进程名, 分类, 开始时间, 时长), ...]
        """
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT window_title, process_name, category, start_time, duration
                FROM activity_log
                ORDER BY start_time DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Stats 插件: 获取最近活动失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None


# 约定：PluginClass 变量指向插件类
PluginClass = StatsPlugin
