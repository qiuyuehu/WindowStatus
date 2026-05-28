# -*- coding: utf-8 -*-
"""
Kernel 核心类 - 核心层
负责组装和协调各个核心模块
"""

import sys
import threading
from typing import Optional, TYPE_CHECKING

from .event_bus import EventBus
from .plugin_manager import PluginManager
from .config import Config

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication


class Kernel:
    """
    Kernel 核心类
    
    职责：
    - 初始化和持有核心模块（EventBus、PluginManager、Config）
    - 协调插件的生命周期
    - 提供统一的访问接口
    """
    
    def __init__(self, config_path: str, db_path: str, log_path: str):
        """
        初始化 Kernel
        
        Args:
            config_path: 配置文件路径
            db_path: 数据库文件路径
            log_path: 日志文件路径
        """
        self.config_path = config_path
        self.db_path = db_path
        self.log_path = log_path
        
        # 初始化核心模块
        self.event_bus = EventBus()
        self.config = Config(config_path)
        self.plugin_manager = PluginManager(self)
        
        # Qt 应用引用
        self._qt_app: Optional['QApplication'] = None
        
        # 初始化日志
        self._init_logger()
        
        self.logger.info("Kernel 初始化完成")
    
    def _init_logger(self):
        """初始化日志系统"""
        import logging
        from logging.handlers import RotatingFileHandler
        
        # 创建 logger
        self.logger = logging.getLogger("WindowStatus")
        self.logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        try:
            file_handler = RotatingFileHandler(
                self.log_path,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # 格式
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
        except Exception as e:
            # logger 可能不可用，用 basicConfig fallback
            logging.basicConfig(level=logging.INFO)
            logging.getLogger("WindowStatus").error(f"初始化日志失败: {e}")
        
        # 控制台处理器（仅开发环境，打包后 console=False 无意义）
        if not getattr(sys, 'frozen', False):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def set_qt_app(self, app: 'QApplication'):
        """
        设置 QApplication 实例
        
        Args:
            app: QApplication 实例
        """
        self._qt_app = app
        self.event_bus.set_qt_app(app)
        
        # 设置主线程
        main_thread = threading.current_thread()
        self.event_bus.set_main_thread(main_thread)
        
        self.logger.info("Qt 应用已设置")
    
    def load_plugins(self):
        """加载所有启用的插件"""
        enabled_plugins = self.config.get_enabled_plugins()
        self.logger.info(f"加载插件: {enabled_plugins}")
        
        self.plugin_manager.load_all_discovered(enabled_plugins)
        
        # 统计加载结果
        loaded = self.plugin_manager.get_all_plugins()
        self.logger.info(f"已加载 {len(loaded)} 个插件")
    
    def unload_plugins(self):
        """卸载所有插件"""
        self.logger.info("卸载所有插件")
        self.plugin_manager.unload_all()
    
    def start(self):
        """启动 Kernel"""
        self.logger.info("Kernel 启动")
        
        # 加载插件
        self.load_plugins()
    
    def stop(self):
        """停止 Kernel"""
        self.logger.info("Kernel 停止")
        
        # 卸载插件
        self.unload_plugins()
        
        # 清理事件总线
        self.event_bus.off_all_handlers()
        
        self.logger.info("Kernel 已停止")
