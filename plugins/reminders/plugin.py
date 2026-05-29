# -*- coding: utf-8 -*-
"""
Reminders 插件 - 插件层
分类使用时长提醒：在某个分类持续一定时间后弹出提示
"""

from datetime import datetime
from typing import Optional

from PyQt5.QtCore import QTimer

from plugins.base import Plugin
from kernel.event_bus import Events


class RemindersPlugin(Plugin):
    """
    提醒插件

    职责：
    - 监听 CATEGORY_MATCHED 事件，跟踪当前分类
    - 定时检查是否超过预设时长
    - 通过托盘通知提醒用户

    配置格式（config.json 中的 reminders）：
    {
        "摸鱼": {"enabled": true, "interval_minutes": 30, "message": "..."},
        "_default": {"enabled": false, "interval_minutes": 45, "message": "..."}
    }

    消息中 {minutes} 会被替换为实际分钟数。
    """

    name = "reminders"
    version = "1.0.0"
    description = "分类使用时长提醒（休息、喝水等）"

    def __init__(self, kernel):
        super().__init__(kernel)
        self._current_category: Optional[str] = None
        self._category_start: Optional[datetime] = None
        self._triggered_intervals: set = set()  # 已触发的 (category, interval) 避免重复
        self._check_timer: Optional[QTimer] = None
        self._active_msg_box = None  # 保持弹窗引用，防止被垃圾回收
        
        # 空闲状态
        self._is_idle = False
        self._idle_start_time: Optional[datetime] = None

    def on_load(self):
        """插件加载"""
        self.logger = self.kernel.logger

        # 注册事件
        self.event_bus.on(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.on(Events.IDLE_DETECTED, self._on_idle_detected)
        self.event_bus.on(Events.IDLE_RESUMED, self._on_idle_resumed)

        # 每 30 秒检查一次
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_reminders)
        self._check_timer.start(30 * 1000)

        self.logger.info("Reminders 插件已加载")

    def on_unload(self):
        """插件卸载"""
        self.event_bus.off(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.off(Events.IDLE_DETECTED, self._on_idle_detected)
        self.event_bus.off(Events.IDLE_RESUMED, self._on_idle_resumed)

        if self._check_timer:
            self._check_timer.stop()
            self._check_timer = None

        self.logger.info("Reminders 插件已卸载")

    def on_enable(self):
        """插件启用"""
        self.logger.info("Reminders 插件已启用")

    def on_disable(self):
        """插件禁用"""
        self._triggered_intervals.clear()
        self.logger.info("Reminders 插件已禁用")

    def _on_category_matched(self, category: str, **kwargs):
        """分类变化时重置计时"""
        if self._is_idle:
            return  # 空闲时不更新分类
        if category != self._current_category:
            self._current_category = category
            self._category_start = datetime.now()
            self._triggered_intervals.clear()

    def _on_idle_detected(self, **kwargs):
        """用户空闲时暂停计时"""
        if self._is_idle:
            return
        self._is_idle = True
        self._idle_start_time = datetime.now()
        self.logger.info("Reminders 插件: 用户空闲，暂停提醒计时")

    def _on_idle_resumed(self, **kwargs):
        """用户回来时恢复计时"""
        if not self._is_idle:
            return
        self._is_idle = False
        # 重置分类开始时间，避免空闲时间被计入
        if self._category_start and self._idle_start_time:
            idle_duration = (datetime.now() - self._idle_start_time).total_seconds()
            self._category_start = datetime.now()  # 重新开始计时
            self.logger.info(f"Reminders 插件: 用户回来，空闲了 {idle_duration:.0f} 秒，重置提醒计时")
        self._idle_start_time = None

    def _check_reminders(self):
        """检查是否需要提醒"""
        if not self.enabled or not self._current_category or not self._category_start:
            return

        elapsed = (datetime.now() - self._category_start).total_seconds()
        elapsed_minutes = int(elapsed / 60)

        # 获取该分类的提醒配置
        reminders_config = self.config.get("reminders", {})
        cat_config = reminders_config.get(self._current_category)
        if not cat_config:
            cat_config = reminders_config.get("_default")
        if not cat_config or not cat_config.get("enabled", False):
            return

        interval = cat_config.get("interval_minutes", 30)
        if interval <= 0:
            return

        # 检查是否到了触发时间
        if elapsed_minutes >= interval:
            # 检查是否已经触发过这个间隔
            trigger_key = (self._current_category, interval)
            if trigger_key not in self._triggered_intervals:
                self._triggered_intervals.add(trigger_key)
                self._show_reminder(cat_config, elapsed_minutes)

    def _show_reminder(self, cat_config: dict, minutes: int):
        """显示提醒（非阻塞弹窗）"""
        message_template = cat_config.get("message", "已经连续使用 {minutes} 分钟了！")
        message = message_template.replace("{minutes}", str(minutes))

        self.logger.info(f"Reminders 插件: 触发提醒 [{self._current_category}] {message}")
        self.logger.info(f"Reminders 插件: 准备弹窗...")

        try:
            # 弹窗提醒
            from PyQt5.QtWidgets import QMessageBox
            from PyQt5.QtCore import Qt

            # 如果已有弹窗在显示，先关闭
            if self._active_msg_box and self._active_msg_box.isVisible():
                self._active_msg_box.close()

            msg_box = QMessageBox()
            msg_box.setWindowTitle(f"WindowStatus - {self._current_category}")
            msg_box.setText(message)
            msg_box.setInformativeText("注意休息，保护眼睛和颈椎！")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)

            # 深色主题样式
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1a1a2e;
                    color: white;
                }
                QLabel {
                    color: white;
                }
                QPushButton {
                    background-color: #0f3460;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #1a4a8a;
                }
            """)

            # 置顶显示
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)
            
            # 非阻塞显示，保持引用防止被垃圾回收
            self._active_msg_box = msg_box
            msg_box.finished.connect(self._on_msg_box_finished)
            msg_box.show()
            self.logger.info(f"Reminders 插件: 弹窗已显示（非阻塞）")

        except Exception as e:
            self.logger.error(f"Reminders 插件: 弹窗失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _on_msg_box_finished(self, result):
        """弹窗关闭回调"""
        self._active_msg_box = None
        self.logger.info(f"Reminders 插件: 弹窗已关闭")


# 约定：PluginClass 变量指向插件类
PluginClass = RemindersPlugin
