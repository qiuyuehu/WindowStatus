# -*- coding: utf-8 -*-
"""
插件层公共工具函数
"""

from datetime import datetime
from typing import Optional


def format_duration(seconds: int) -> str:
    """
    格式化时长为人类可读的字符串

    Args:
        seconds: 秒数

    Returns:
        格式化后的时长字符串，如 "3分钟"、"1小时30分钟"
    """
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}小时{minutes}分钟"
        return f"{hours}小时"


def truncate_text(text: str, max_length: int = 25) -> str:
    """
    截断过长的文本，超出部分用省略号替代

    Args:
        text: 原始文本
        max_length: 最大长度（含省略号）

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_timestamp(dt: Optional[datetime], fmt: str = "%H:%M") -> str:
    """
    格式化时间戳

    Args:
        dt: datetime 对象，None 时返回空字符串
        fmt: 格式化模板

    Returns:
        格式化后的时间字符串
    """
    if dt is None:
        return ""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime(fmt)
