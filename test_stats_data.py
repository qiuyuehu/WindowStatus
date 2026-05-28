# -*- coding: utf-8 -*-
"""
测试脚本：往 daily_stats 插入假数据，模拟过去4周的统计
用于测试周/月统计功能
"""

import sqlite3
import random
from datetime import datetime, timedelta

# 数据库路径
DB_PATH = r"C:\Users\秋月\.WindowStatus\data.db"

# 分类配置（模拟真实使用场景）
CATEGORIES = {
    "开发": {"min_minutes": 60, "max_minutes": 300},   # 1-5小时
    "摸鱼": {"min_minutes": 30, "max_minutes": 120},   # 0.5-2小时
    "办公": {"min_minutes": 30, "max_minutes": 180},   # 0.5-3小时
    "游戏": {"min_minutes": 0, "max_minutes": 120},    # 0-2小时（不一定每天玩）
    "工具": {"min_minutes": 10, "max_minutes": 60},    # 10-60分钟
}

def generate_daily_data(date: datetime.date) -> list:
    """生成某一天的统计数据"""
    records = []
    
    # 工作日和周末的数据不同
    is_weekday = date.weekday() < 5  # 0-4 是周一到周五
    
    for category, config in CATEGORIES.items():
        # 周末游戏时间更长，办公时间更短
        if is_weekday:
            min_m = config["min_minutes"]
            max_m = config["max_minutes"]
        else:
            if category == "办公":
                min_m = 0
                max_m = 30
            elif category == "游戏":
                min_m = 30
                max_m = 180
            else:
                min_m = config["min_minutes"]
                max_m = config["max_minutes"]
        
        # 随机生成时长（有些分类可能为0）
        if random.random() < 0.1 and category != "工具":  # 10%概率跳过（工具必有）
            continue
        
        duration_minutes = random.randint(min_m, max_m)
        if duration_minutes > 0:
            duration_seconds = duration_minutes * 60
            # 模拟切换次数（每5-15分钟切换一次）
            session_count = max(1, duration_minutes // random.randint(5, 15))
            records.append((date, category, duration_seconds, session_count))
    
    return records

def main():
    print(f"连接数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 确保表存在
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date DATE,
            category TEXT,
            total_duration INTEGER DEFAULT 0,
            session_count INTEGER DEFAULT 0,
            PRIMARY KEY (date, category)
        )
    ''')
    
    # 生成过去4周的数据
    today = datetime.now().date()
    start_date = today - timedelta(days=28)  # 4周前
    
    total_records = 0
    current_date = start_date
    
    while current_date < today:
        records = generate_daily_data(current_date)
        for date, category, duration, sessions in records:
            cursor.execute('''
                INSERT OR REPLACE INTO daily_stats 
                (date, category, total_duration, session_count)
                VALUES (?, ?, ?, ?)
            ''', (date, category, duration, sessions))
            total_records += 1
        
        current_date += timedelta(days=1)
    
    conn.commit()
    
    # 验证插入结果
    cursor.execute('SELECT COUNT(DISTINCT date) FROM daily_stats')
    days_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT date, category, total_duration FROM daily_stats ORDER BY date DESC LIMIT 10')
    sample_data = cursor.fetchall()
    
    print(f"\n插入完成！")
    print(f"- 共插入 {total_records} 条记录")
    print(f"- 覆盖 {days_count} 天")
    print(f"\n最近10条数据示例:")
    for date, category, duration in sample_data:
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        print(f"  {date} | {category:4} | {hours}小时{minutes}分钟")
    
    conn.close()
    print(f"\n重启 WindowStatus 后，统计窗口应该能看到周/月统计数据")

if __name__ == "__main__":
    main()
