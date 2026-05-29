# -*- coding: utf-8 -*-
"""
WindowStatus — Windows 窗口状态显示器
Author: 衾衾 (Hermes Agent)

v3.0 - 完整插件化架构
- 事件总线驱动
- 插件动态加载
- 线程安全
"""

import sys
import os

# === 修复 Qt 平台插件路径 ===
# PyQt5 有时找不到自己的 plugins 目录，手动指定
def _fix_qt_plugin_path():
    try:
        import PyQt5
        qt_dir = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
        if os.path.isdir(qt_dir):
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_dir
    except Exception:
        pass

_fix_qt_plugin_path()
# === 修复结束 ===

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon

from kernel.core import Kernel
from kernel.event_bus import Events


# 配置文件路径
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.WindowStatus')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
DB_FILE = os.path.join(CONFIG_DIR, 'data.db')
LOG_FILE = os.path.join(CONFIG_DIR, 'window_status.log')


def _get_icon_path() -> str:
    """获取图标文件路径（兼容开发模式和打包模式）"""
    if getattr(sys, 'frozen', False):
        # 打包模式：图标在 exe 同目录
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发模式：图标在项目根目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, 'icon.ico')
    if os.path.exists(icon_path):
        return icon_path
    return ''


class WindowStatusApp:
    """
    WindowStatus 主应用
    
    v3.0 架构：
    - 只负责组装 Kernel 和启动 Qt 应用
    - 所有业务逻辑由插件处理
    - 通过事件总线进行插件间通信
    """
    
    def __init__(self):
        # 初始化 Qt 应用
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # 设置应用图标（所有窗口继承）
        icon_path = _get_icon_path()
        if icon_path:
            self.app.setWindowIcon(QIcon(icon_path))
        
        # 初始化 Kernel
        try:
            self.kernel = Kernel(CONFIG_FILE, DB_FILE, LOG_FILE)
            self.kernel.set_qt_app(self.app)
        except Exception as e:
            # Kernel 初始化失败，使用 fallback 日志（kernel.logger 尚不存在）
            import logging
            import traceback
            _fallback_log = logging.getLogger("WindowStatus")
            _fallback_log.error(f"Kernel 初始化失败: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(
                None,
                "WindowStatus 启动错误",
                f"程序初始化失败，无法继续运行。\n\n"
                f"错误信息: {e}\n\n"
                f"请检查配置文件是否损坏，或磁盘空间是否充足。\n"
                f"配置目录: {CONFIG_DIR}"
            )
            raise
        
        # 注册应用级事件处理
        self._register_app_events()
    
    def _register_app_events(self):
        """注册应用级事件处理"""
        # 退出事件
        self.kernel.event_bus.on(Events.QUIT, self._on_quit)

        # 显示统计窗口（stats 插件的弹窗需要通过主应用委托）
        self.kernel.event_bus.on(Events.SHOW_STATS, self._on_show_stats)
    
    def start(self) -> int:
        """启动应用"""
        try:
            self.kernel.logger.info("WindowStatus 启动中...")
            
            # 启动 Kernel（加载插件）
            self.kernel.start()
            
            self.kernel.logger.info("WindowStatus 启动完成")
            
            # 运行 Qt 应用
            return self.app.exec_()
        
        except Exception as e:
            self.kernel.logger.exception(f"启动失败: {e}")
            QMessageBox.critical(None, "错误", f"启动失败: {e}")
            return 1
    
    def _on_quit(self, **kwargs):
        """处理退出事件"""
        try:
            self.kernel.logger.info("WindowStatus 退出中...")
            
            # 停止 Kernel
            self.kernel.stop()
            
            # 退出 Qt 应用
            self.app.quit()
        
        except Exception as e:
            self.kernel.logger.error(f"退出失败: {e}")
            self.app.quit()
    
    def _on_show_stats(self, **kwargs):
        """显示统计窗口 — 委托给 stats 插件自己处理"""
        try:
            stats_plugin = self.kernel.plugin_manager.get_plugin("stats")
            if not stats_plugin:
                QMessageBox.information(None, "统计", "统计插件未加载")
                return
            stats_plugin.show_dialog()
        except Exception as e:
            self.kernel.logger.error(f"显示统计失败: {e}")

def main():
    """主函数"""
    try:
        app = WindowStatusApp()
        sys.exit(app.start())
    except Exception:
        # QMessageBox 已在 WindowStatusApp.__init__ 中显示，直接退出
        sys.exit(1)


if __name__ == '__main__':
    main()
