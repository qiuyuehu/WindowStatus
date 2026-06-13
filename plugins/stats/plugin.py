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
from plugins.utils import format_duration
from kernel.event_bus import Events


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
        
        # 空闲状态
        self._is_idle = False
        self._idle_start_time: Optional[datetime] = None
        
        # 统计弹窗引用（防止被垃圾回收）
        self._active_dialog = None
    
    def on_load(self):
        """插件加载"""
        

        # 确保目录存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        # 连接数据库
        self._connect()
        self._create_tables()

        # 启动时自动备份数据库
        self._backup_database()

        # 启动时自动聚合历史数据
        self._aggregate_history()

        # 注册事件监听
        self.event_bus.on(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.on(Events.IDLE_DETECTED, self._on_idle_detected)
        self.event_bus.on(Events.IDLE_RESUMED, self._on_idle_resumed)
        self.event_bus.on(Events.QUIT, self._on_quit)

        self.logger.info(f"Stats 插件已加载，数据库: {self.db_path}")
    
    def on_unload(self):
        """插件卸载"""
        # 注销事件监听
        self.event_bus.off(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.off(Events.IDLE_DETECTED, self._on_idle_detected)
        self.event_bus.off(Events.IDLE_RESUMED, self._on_idle_resumed)
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

            # 明细表
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

            # 每日统计汇总表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date DATE,
                    category TEXT,
                    total_duration INTEGER DEFAULT 0,
                    session_count INTEGER DEFAULT 0,
                    PRIMARY KEY (date, category)
                )
            ''')

            # 每周统计汇总表 (week_start 为该周的周一日期)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weekly_stats (
                    week_start DATE,
                    category TEXT,
                    total_duration INTEGER DEFAULT 0,
                    session_count INTEGER DEFAULT 0,
                    PRIMARY KEY (week_start, category)
                )
            ''')

            # 每月统计汇总表 (month 格式: YYYY-MM)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monthly_stats (
                    month TEXT,
                    category TEXT,
                    total_duration INTEGER DEFAULT 0,
                    session_count INTEGER DEFAULT 0,
                    PRIMARY KEY (month, category)
                )
            ''')

            # 创建索引加速查询
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_activity_log_start_time
                ON activity_log(start_time)
            ''')

            self.conn.commit()
            self.logger.info("Stats 插件: 数据表已就绪")
        except Exception as e:
            self.logger.error(f"Stats 插件: 创建表失败: {e}")
    
    def _backup_database(self):
        """备份数据库（保留最近 7 天）"""
        import shutil
        from datetime import datetime
        
        if not os.path.exists(self.db_path):
            return
        
        try:
            # 备份目录
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"data_{timestamp}.db")
            
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Stats 插件: 数据库已备份到 {backup_path}")
            
            # 清理旧备份（保留最近 7 天）
            self._cleanup_old_backups(backup_dir, keep_days=7)
            
        except Exception as e:
            self.logger.error(f"Stats 插件: 数据库备份失败: {e}")
    
    def _cleanup_old_backups(self, backup_dir: str, keep_days: int = 7):
        """清理旧备份文件"""
        import glob
        from datetime import datetime, timedelta
        
        try:
            # 获取所有备份文件
            backup_files = glob.glob(os.path.join(backup_dir, "data_*.db"))
            
            # 计算截止时间
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            
            for backup_file in backup_files:
                try:
                    # 从文件名提取时间戳
                    filename = os.path.basename(backup_file)
                    timestamp_str = filename.replace("data_", "").replace(".db", "")
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    # 删除过期备份
                    if file_time < cutoff_time:
                        os.remove(backup_file)
                        self.logger.debug(f"Stats 插件: 已删除旧备份 {filename}")
                except (ValueError, OSError):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Stats 插件: 清理旧备份失败: {e}")

    def _aggregate_daily(self, target_date: datetime.date = None):
        """
        聚合指定日期的活动数据到 daily_stats

        Args:
            target_date: 要聚合的日期，默认为昨天
        """
        if not self.conn:
            return

        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).date()

        try:
            cursor = self.conn.cursor()

            # 检查是否已经聚合过
            cursor.execute(
                'SELECT COUNT(*) FROM daily_stats WHERE date = ?',
                (target_date,)
            )
            if cursor.fetchone()[0] > 0:
                self.logger.debug(f"Stats 插件: {target_date} 已聚合，跳过")
                return

            # 从 activity_log 聚合当天数据
            cursor.execute('''
                SELECT category,
                       SUM(duration) as total_duration,
                       COUNT(*) as session_count
                FROM activity_log
                WHERE DATE(start_time) = ?
                GROUP BY category
            ''', (target_date,))

            rows = cursor.fetchall()
            if not rows:
                self.logger.debug(f"Stats 插件: {target_date} 无数据，跳过聚合")
                return

            # 写入 daily_stats
            for category, total_duration, session_count in rows:
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_stats
                    (date, category, total_duration, session_count)
                    VALUES (?, ?, ?, ?)
                ''', (target_date, category, total_duration, session_count))

            # 删除已聚合的明细数据
            cursor.execute('''
                DELETE FROM activity_log
                WHERE DATE(start_time) = ?
            ''', (target_date,))

            self.conn.commit()
            self.logger.info(f"Stats 插件: 已聚合 {target_date} 的数据，{len(rows)} 个分类")

        except Exception as e:
            self.logger.error(f"Stats 插件: 聚合 {target_date} 失败: {e}")

    def _get_week_start(self, dt: datetime.date = None) -> datetime.date:
        """获取指定日期所在周的周一"""
        if dt is None:
            dt = datetime.now().date()
        # weekday(): 0=周一, 6=周日
        return dt - timedelta(days=dt.weekday())

    def _aggregate_weekly(self, week_start: datetime.date = None):
        """
        聚合指定周的 daily_stats 到 weekly_stats

        Args:
            week_start: 该周的周一日期，默认为上周一
        """
        if not self.conn:
            return

        if week_start is None:
            last_week = datetime.now().date() - timedelta(days=7)
            week_start = self._get_week_start(last_week)

        week_end = week_start + timedelta(days=6)

        try:
            cursor = self.conn.cursor()

            # 检查是否已经聚合过
            cursor.execute(
                'SELECT COUNT(*) FROM weekly_stats WHERE week_start = ?',
                (week_start,)
            )
            if cursor.fetchone()[0] > 0:
                self.logger.debug(f"Stats 插件: 周 {week_start} 已聚合，跳过")
                return

            # 从 daily_stats 聚合该周数据
            cursor.execute('''
                SELECT category,
                       SUM(total_duration) as total_duration,
                       SUM(session_count) as session_count
                FROM daily_stats
                WHERE date >= ? AND date <= ?
                GROUP BY category
            ''', (week_start, week_end))

            rows = cursor.fetchall()
            if not rows:
                self.logger.debug(f"Stats 插件: 周 {week_start} 无数据，跳过聚合")
                return

            # 写入 weekly_stats
            for category, total_duration, session_count in rows:
                cursor.execute('''
                    INSERT OR REPLACE INTO weekly_stats
                    (week_start, category, total_duration, session_count)
                    VALUES (?, ?, ?, ?)
                ''', (week_start, category, total_duration, session_count))

            # 删除已聚合的 daily_stats（只删除该周的）
            cursor.execute('''
                DELETE FROM daily_stats
                WHERE date >= ? AND date <= ?
            ''', (week_start, week_end))

            self.conn.commit()
            self.logger.info(f"Stats 插件: 已聚合周 {week_start} 的数据，{len(rows)} 个分类")

        except Exception as e:
            self.logger.error(f"Stats 插件: 聚合周 {week_start} 失败: {e}")

    def _aggregate_monthly(self, year_month: str = None):
        """
        聚合指定月的 daily_stats 到 monthly_stats

        Args:
            year_month: 格式 "YYYY-MM"，默认为上个月
        """
        if not self.conn:
            return

        if year_month is None:
            today = datetime.now().date()
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - timedelta(days=1)
            year_month = last_month_end.strftime("%Y-%m")

        try:
            cursor = self.conn.cursor()

            # 检查是否已经聚合过
            cursor.execute(
                'SELECT COUNT(*) FROM monthly_stats WHERE month = ?',
                (year_month,)
            )
            if cursor.fetchone()[0] > 0:
                self.logger.debug(f"Stats 插件: 月 {year_month} 已聚合，跳过")
                return

            # 从 daily_stats 聚合该月数据
            cursor.execute('''
                SELECT category,
                       SUM(total_duration) as total_duration,
                       SUM(session_count) as session_count
                FROM daily_stats
                WHERE strftime('%Y-%m', date) = ?
                GROUP BY category
            ''', (year_month,))

            rows = cursor.fetchall()
            if not rows:
                self.logger.debug(f"Stats 插件: 月 {year_month} 无数据，跳过聚合")
                return

            # 写入 monthly_stats
            for category, total_duration, session_count in rows:
                cursor.execute('''
                    INSERT OR REPLACE INTO monthly_stats
                    (month, category, total_duration, session_count)
                    VALUES (?, ?, ?, ?)
                ''', (year_month, category, total_duration, session_count))

            # 删除已聚合的 daily_stats
            cursor.execute('''
                DELETE FROM daily_stats
                WHERE strftime('%Y-%m', date) = ?
            ''', (year_month,))

            self.conn.commit()
            self.logger.info(f"Stats 插件: 已聚合月 {year_month} 的数据，{len(rows)} 个分类")

        except Exception as e:
            self.logger.error(f"Stats 插件: 聚合月 {year_month} 失败: {e}")

    def _aggregate_history(self):
        """
        启动时自动聚合历史数据

        逻辑：
        1. 检查 activity_log 中最早的数据日期
        2. 聚合昨天及之前的所有天数到 daily_stats
        3. 聚合上周及之前的所有周到 weekly_stats
        4. 聚合上月及之前的所有月到 monthly_stats
        """
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            today = datetime.now().date()

            # 1. 聚合昨天及之前的 activity_log 到 daily_stats
            cursor.execute('''
                SELECT DISTINCT DATE(start_time) as log_date
                FROM activity_log
                WHERE DATE(start_time) < ?
                ORDER BY log_date
            ''', (today,))

            old_dates = [row[0] for row in cursor.fetchall()]
            if old_dates:
                self.logger.info(f"Stats 插件: 发现 {len(old_dates)} 天待聚合的明细数据")
                for date_str in old_dates:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    self._aggregate_daily(date)

            # 2. 聚合上周及之前的 daily_stats 到 weekly_stats
            this_week_start = self._get_week_start(today)

            cursor.execute('''
                SELECT DISTINCT date FROM daily_stats
                WHERE date < ?
                ORDER BY date
            ''', (this_week_start,))

            old_daily_dates = [row[0] for row in cursor.fetchall()]
            if old_daily_dates:
                # 按周分组聚合
                weeks_to_aggregate = set()
                for date_str in old_daily_dates:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    week_start = self._get_week_start(date)
                    weeks_to_aggregate.add(week_start)

                self.logger.info(f"Stats 插件: 发现 {len(weeks_to_aggregate)} 周待聚合的每日数据")
                for week_start in sorted(weeks_to_aggregate):
                    self._aggregate_weekly(week_start)

            # 3. 聚合上月及之前的 daily_stats 到 monthly_stats
            first_of_month = today.replace(day=1)

            cursor.execute('''
                SELECT DISTINCT date FROM daily_stats
                WHERE date < ?
                ORDER BY date
            ''', (first_of_month,))

            old_daily_for_month = [row[0] for row in cursor.fetchall()]
            if old_daily_for_month:
                # 按月分组聚合
                months_to_aggregate = set()
                for date_str in old_daily_for_month:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    year_month = date.strftime("%Y-%m")
                    months_to_aggregate.add(year_month)

                self.logger.info(f"Stats 插件: 发现 {len(months_to_aggregate)} 月待聚合的每日数据")
                for year_month in sorted(months_to_aggregate):
                    self._aggregate_monthly(year_month)

            self.logger.info("Stats 插件: 历史数据聚合完成")

        except Exception as e:
            self.logger.error(f"Stats 插件: 历史聚合失败: {e}")
    
    def _on_category_matched(self, **kwargs):
        """处理分类匹配事件"""
        if not self.enabled or self._is_idle:
            return
        
        # 记录上一个活动
        self._record_current_activity()
        
        # 更新当前活动
        self._current_title = kwargs.get('title', '')
        self._current_process = kwargs.get('process_name', '')
        self._current_category = kwargs.get('category', '其他')
        self._current_start_time = datetime.now()
        
        self.logger.debug(f"Stats 插件: 开始记录 [{self._current_category}] {self._current_title[:30]}")
    
    def _on_idle_detected(self, **kwargs):
        """用户空闲时暂停统计"""
        if not self.enabled or self._is_idle:
            return
        
        self._is_idle = True
        self._idle_start_time = datetime.now()
        
        # 记录当前活动（截止到空闲开始）
        self._record_current_activity()
        
        idle_seconds = kwargs.get('idle_seconds', 0)
        self.logger.info(f"Stats 插件: 用户空闲 {idle_seconds:.0f} 秒，暂停统计")
    
    def _on_idle_resumed(self, **kwargs):
        """用户回来时恢复统计"""
        if not self.enabled or not self._is_idle:
            return
        
        self._is_idle = False
        
        # 记录空闲时长（可选：单独记录空闲时间）
        if self._idle_start_time:
            idle_duration = int((datetime.now() - self._idle_start_time).total_seconds())
            self.logger.info(f"Stats 插件: 用户回来，空闲了 {idle_duration} 秒")
        
        self._idle_start_time = None
        # 注意：当前窗口的统计会在下次 CATEGORY_MATCHED 事件时重新开始
    
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

    def get_week_stats(self) -> List[Tuple[str, int]]:
        """
        获取本周统计

        先尝试从 weekly_stats 查询，如果没有则从 activity_log + daily_stats 聚合

        Returns:
            List[Tuple[str, int]]: [(分类, 总时长), ...]
        """
        if not self.conn:
            return []

        try:
            today = datetime.now().date()
            week_start = self._get_week_start(today)
            week_end = week_start + timedelta(days=6)

            cursor = self.conn.cursor()

            # 先查 weekly_stats（已完成的周）
            cursor.execute('''
                SELECT category, SUM(total_duration) as total_duration
                FROM weekly_stats
                WHERE week_start = ?
                GROUP BY category
                ORDER BY total_duration DESC
            ''', (week_start,))

            result = cursor.fetchall()
            if result:
                return result

            # 如果 weekly_stats 没有数据，从 activity_log + daily_stats 实时聚合
            # 本周已过去的天数从 daily_stats 取
            cursor.execute('''
                SELECT category, SUM(total_duration) as total_duration
                FROM daily_stats
                WHERE date >= ? AND date < ?
                GROUP BY category
            ''', (week_start, today))

            daily_result = {row[0]: row[1] for row in cursor.fetchall()}

            # 今天的数据从 activity_log 取
            cursor.execute('''
                SELECT category, SUM(duration) as total_duration
                FROM activity_log
                WHERE DATE(start_time) = ?
                GROUP BY category
            ''', (today,))

            for category, duration in cursor.fetchall():
                daily_result[category] = daily_result.get(category, 0) + duration

            # 转换为排序列表
            result = sorted(daily_result.items(), key=lambda x: x[1], reverse=True)
            return result

        except Exception as e:
            self.logger.error(f"Stats 插件: 获取本周统计失败: {e}")
            return []

    def get_month_stats(self) -> List[Tuple[str, int]]:
        """
        获取本月统计

        数据来源：
        1. monthly_stats（已完成的月聚合）
        2. weekly_stats 中属于本月的周数据
        3. daily_stats 中本周的数据
        4. activity_log 中今天的数据

        Returns:
            List[Tuple[str, int]]: [(分类, 总时长), ...]
        """
        if not self.conn:
            return []

        try:
            today = datetime.now().date()
            year_month = today.strftime("%Y-%m")
            first_of_month = today.replace(day=1)
            this_week_start = self._get_week_start(today)

            cursor = self.conn.cursor()

            # 1. 先查 monthly_stats（已完成的月）
            cursor.execute('''
                SELECT category, SUM(total_duration) as total_duration
                FROM monthly_stats
                WHERE month = ?
                GROUP BY category
                ORDER BY total_duration DESC
            ''', (year_month,))

            result = cursor.fetchall()
            if result:
                return result

            # 2. 从 weekly_stats 取本月已结束的周数据
            #    （week_start < 本周一 且 属于本月）
            cursor.execute('''
                SELECT category, SUM(total_duration) as total_duration
                FROM weekly_stats
                WHERE week_start >= ? AND week_start < ?
                GROUP BY category
            ''', (first_of_month, this_week_start))

            monthly_from_weekly = {row[0]: row[1] for row in cursor.fetchall()}

            # 3. 从 daily_stats 取本周的数据（尚未聚合到 weekly_stats）
            cursor.execute('''
                SELECT category, SUM(total_duration) as total_duration
                FROM daily_stats
                WHERE date >= ? AND date < ?
                GROUP BY category
            ''', (this_week_start, today))

            for category, duration in cursor.fetchall():
                monthly_from_weekly[category] = monthly_from_weekly.get(category, 0) + duration

            # 4. 今天的数据从 activity_log 取
            cursor.execute('''
                SELECT category, SUM(duration) as total_duration
                FROM activity_log
                WHERE DATE(start_time) = ?
                GROUP BY category
            ''', (today,))

            for category, duration in cursor.fetchall():
                monthly_from_weekly[category] = monthly_from_weekly.get(category, 0) + duration

            # 转换为排序列表
            result = sorted(monthly_from_weekly.items(), key=lambda x: x[1], reverse=True)
            return result

        except Exception as e:
            self.logger.error(f"Stats 插件: 获取本月统计失败: {e}")
            return []
    
    def get_yesterday_stats(self) -> List[Tuple[str, int]]:
        """
        获取昨日统计

        先查 daily_stats（昨天已被聚合），如果没有则查 activity_log。

        Returns:
            List[Tuple[str, int]]: [(分类, 总时长), ...]
        """
        if not self.conn:
            return []

        try:
            yesterday = (datetime.now() - timedelta(days=1)).date()
            cursor = self.conn.cursor()

            # 先查 daily_stats（已被聚合的历史数据）
            cursor.execute('''
                SELECT category, total_duration
                FROM daily_stats
                WHERE date = ?
                ORDER BY total_duration DESC
            ''', (yesterday,))
            result = cursor.fetchall()
            if result:
                return result

            # 如果 daily_stats 没有，查 activity_log（昨天数据尚未聚合）
            cursor.execute('''
                SELECT category, SUM(duration) as total_duration
                FROM activity_log
                WHERE DATE(start_time) = ?
                GROUP BY category
                ORDER BY total_duration DESC
            ''', (yesterday,))
            return cursor.fetchall()

        except Exception as e:
            self.logger.error(f"Stats 插件: 获取昨日统计失败: {e}")
            return []

    def get_last_week_stats(self) -> List[Tuple[str, int]]:
        """
        获取上周统计

        Returns:
            List[Tuple[str, int]]: [(分类, 总时长), ...]
        """
        if not self.conn:
            return []

        try:
            today = datetime.now().date()
            this_week_start = self._get_week_start(today)
            last_week_start = this_week_start - timedelta(days=7)
            last_week_end = this_week_start - timedelta(days=1)

            cursor = self.conn.cursor()

            # 先查 weekly_stats
            cursor.execute('''
                SELECT category, SUM(total_duration) as total_duration
                FROM weekly_stats
                WHERE week_start = ?
                GROUP BY category
                ORDER BY total_duration DESC
            ''', (last_week_start,))
            result = cursor.fetchall()
            if result:
                return result

            # 如果没有，从 daily_stats 聚合
            cursor.execute('''
                SELECT category, SUM(total_duration) as total_duration
                FROM daily_stats
                WHERE date >= ? AND date <= ?
                GROUP BY category
                ORDER BY total_duration DESC
            ''', (last_week_start, last_week_end))
            return cursor.fetchall()

        except Exception as e:
            self.logger.error(f"Stats 插件: 获取上周统计失败: {e}")
            return []

    def get_last_month_stats(self) -> List[Tuple[str, int]]:
        """
        获取上月统计

        Returns:
            List[Tuple[str, int]]: [(分类, 总时长), ...]
        """
        if not self.conn:
            return []

        try:
            today = datetime.now().date()
            # 上月1号和最后一天
            first_of_this_month = today.replace(day=1)
            last_month_end = first_of_this_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)

            cursor = self.conn.cursor()

            # 先查 monthly_stats
            cursor.execute('''
                SELECT category, total_duration
                FROM monthly_stats
                WHERE year = ? AND month = ?
                ORDER BY total_duration DESC
            ''', (last_month_start.year, last_month_start.month))
            result = cursor.fetchall()
            if result:
                return result

            # 如果没有，从 daily_stats 聚合
            cursor.execute('''
                SELECT category, SUM(total_duration) as total_duration
                FROM daily_stats
                WHERE date >= ? AND date <= ?
                GROUP BY category
                ORDER BY total_duration DESC
            ''', (last_month_start, last_month_end))
            return cursor.fetchall()

        except Exception as e:
            self.logger.error(f"Stats 插件: 获取上月统计失败: {e}")
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
    
    def export_to_csv(self, output_path: str = None) -> str:
        """
        导出统计数据到 CSV 文件
        
        Args:
            output_path: 输出文件路径，默认为桌面
        
        Returns:
            导出文件路径
        """
        import csv
        from datetime import datetime
        
        if not self.conn:
            raise Exception("数据库未连接")
        
        # 默认输出到桌面
        if output_path is None:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(desktop, f"WindowStatus_统计_{timestamp}.csv")
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    window_title,
                    process_name,
                    category,
                    start_time,
                    duration
                FROM activity_log
                ORDER BY start_time DESC
            ''')
            
            rows = cursor.fetchall()
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['窗口标题', '进程名', '分类', '开始时间', '时长(秒)'])
                
                for row in rows:
                    writer.writerow(row)
            
            self.logger.info(f"Stats 插件: 已导出 {len(rows)} 条记录到 {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Stats 插件: 导出失败: {e}")
            raise
    
    def export_to_json(self, output_path: str = None) -> str:
        """
        导出统计数据到 JSON 文件
        
        Args:
            output_path: 输出文件路径，默认为桌面
        
        Returns:
            导出文件路径
        """
        import json
        from datetime import datetime
        
        if not self.conn:
            raise Exception("数据库未连接")
        
        # 默认输出到桌面
        if output_path is None:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(desktop, f"WindowStatus_统计_{timestamp}.json")
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    window_title,
                    process_name,
                    category,
                    start_time,
                    duration
                FROM activity_log
                ORDER BY start_time DESC
            ''')
            
            rows = cursor.fetchall()
            
            data = {
                "export_time": datetime.now().isoformat(),
                "total_records": len(rows),
                "records": [
                    {
                        "window_title": row[0],
                        "process_name": row[1],
                        "category": row[2],
                        "start_time": row[3],
                        "duration": row[4]
                    }
                    for row in rows
                ]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Stats 插件: 已导出 {len(rows)} 条记录到 {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Stats 插件: 导出失败: {e}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def show_dialog(self, parent=None):
        """
        显示统计弹窗

        由主应用通过事件调用，插件自己负责弹窗的创建和展示。
        使用非阻塞方式显示，避免阻塞事件循环。
        """
        from plugins.stats.dialog import StatsDialog

        # 如果已有弹窗在显示，先关闭
        if self._active_dialog and self._active_dialog.isVisible():
            self._active_dialog.close()

        stats_data = self.get_today_stats()
        timeline_data = self.get_today_timeline()
        week_stats = self.get_week_stats()
        month_stats = self.get_month_stats()
        yesterday_stats = self.get_yesterday_stats()
        last_week_stats = self.get_last_week_stats()
        last_month_stats = self.get_last_month_stats()

        # 从配置获取分类信息（颜色、图标）
        categories_config = self._kernel.config.get_categories()

        dialog = StatsDialog(
            stats_data=stats_data,
            timeline_data=timeline_data,
            week_stats=week_stats,
            month_stats=month_stats,
            yesterday_stats=yesterday_stats,
            last_week_stats=last_week_stats,
            last_month_stats=last_month_stats,
            categories_config=categories_config,
            export_csv_fn=self.export_to_csv,
            export_json_fn=self.export_to_json,
            parent=parent
        )
        self._active_dialog = dialog
        dialog.finished.connect(self._on_dialog_finished)
        dialog.show()

    def _on_dialog_finished(self, result):
        """统计弹窗关闭回调"""
        self._active_dialog = None


# 约定：PluginClass 变量指向插件类
PluginClass = StatsPlugin
