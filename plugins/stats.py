# -*- coding: utf-8 -*-
"""
统计插件 - 插件层
记录和查询使用统计数据
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple, Optional


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


class StatsPlugin:
    """
    统计插件
    
    记录窗口使用时长，提供统计数据查询
    """
    
    def __init__(self, db_path: str):
        """
        初始化统计插件
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._ensure_dir()
        self._connect()
        self._create_tables()
    
    def _ensure_dir(self):
        """确保目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    def _connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            print(f"数据库连接失败: {e}")
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
            print(f"创建表失败: {e}")
    
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
        except Exception as e:
            print(f"记录活动失败: {e}")
    
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
            print(f"获取今日统计失败: {e}")
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
            print(f"获取时间线失败: {e}")
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
            print(f"获取最近活动失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None