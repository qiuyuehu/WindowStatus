# -*- coding: utf-8 -*-
"""
日志模块 - 核心层
提供统一的日志记录功能
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """
    日志管理器
    
    支持控制台和文件输出，日志轮转
    """
    
    def __init__(self, name: str = "WindowStatus", log_file: Optional[str] = None,
                 level: str = "INFO", max_size: int = 10485760, backup_count: int = 3):
        """
        初始化日志管理器
        
        Args:
            name: 日志名称
            log_file: 日志文件路径（None则只输出到控制台）
            level: 日志级别（DEBUG/INFO/WARNING/ERROR）
            max_size: 单个日志文件最大大小（字节）
            backup_count: 保留的旧日志文件数量
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # 文件处理器（可选）
        if log_file:
            self._ensure_log_dir(log_file)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def _ensure_log_dir(self, log_file: str):
        """确保日志目录存在"""
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录普通信息"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告信息"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误信息"""
        self.logger.error(message)
    
    def exception(self, message: str):
        """记录异常信息（包含堆栈）"""
        self.logger.exception(message)


# 全局日志实例
_logger: Optional[Logger] = None


def init_logger(log_file: Optional[str] = None, level: str = "INFO",
                max_size: int = 10485760, backup_count: int = 3) -> Logger:
    """
    初始化全局日志
    
    Args:
        log_file: 日志文件路径
        level: 日志级别
        max_size: 单个日志文件最大大小
        backup_count: 保留的旧日志文件数量
    
    Returns:
        Logger: 日志实例
    """
    global _logger
    _logger = Logger(
        name="WindowStatus",
        log_file=log_file,
        level=level,
        max_size=max_size,
        backup_count=backup_count
    )
    return _logger


def get_logger() -> Logger:
    """
    获取全局日志实例
    
    Returns:
        Logger: 日志实例
    """
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger