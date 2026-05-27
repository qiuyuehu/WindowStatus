# -*- coding: utf-8 -*-
"""
WindowStatus Demo - 方案二：功能完整版（PyQt5）
运行方式：pip install PyQt5 psutil pywin32 && python demo_pyqt5.py
"""

import sys
import win32gui
import win32process
import psutil
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QApplication, QSystemTrayIcon, QMenu, QAction,
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont, QIcon

# 分类规则配置
CATEGORIES = {
    "游戏": {
        "icon": "🎮",
        "color": QColor(255, 107, 107, 200),  # #FF6B6B
        "bg_color": QColor(255, 107, 107, 30),
        "rules": [
            {"type": "process", "pattern": "steam.exe"},
            {"type": "process", "pattern": "Unity.exe"},
            {"type": "process", "pattern": "UE4Editor.exe"},
            {"type": "title", "pattern": "*原神*"},
            {"type": "title", "pattern": "*英雄联盟*"},
        ]
    },
    "办公": {
        "icon": "📊",
        "color": QColor(78, 205, 196, 200),  # #4ECDC4
        "bg_color": QColor(78, 205, 196, 30),
        "rules": [
            {"type": "process", "pattern": "EXCEL.EXE"},
            {"type": "process", "pattern": "WINWORD.EXE"},
            {"type": "title", "pattern": "*WPS*"},
            {"type": "title", "pattern": "*Excel*"},
        ]
    },
    "摸鱼": {
        "icon": "🐟",
        "color": QColor(255, 230, 109, 200),  # #FFE66D
        "bg_color": QColor(255, 230, 109, 30),
        "rules": [
            {"type": "process", "pattern": "chrome.exe"},
            {"type": "process", "pattern": "msedge.exe"},
            {"type": "title", "pattern": "*微博*"},
            {"type": "title", "pattern": "*B站*"},
            {"type": "title", "pattern": "*bilibili*"},
        ]
    },
    "开发": {
        "icon": "💻",
        "color": QColor(168, 230, 207, 200),  # #A8E6CF
        "bg_color": QColor(168, 230, 207, 30),
        "rules": [
            {"type": "process", "pattern": "Code.exe"},
            {"type": "process", "pattern": "devenv.exe"},
            {"type": "process", "pattern": "pycharm64.exe"},
            {"type": "title", "pattern": "*Visual Studio*"},
        ]
    }
}

def match_rule(rule, title, process_name):
    """匹配单条规则"""
    rule_type = rule["type"]
    pattern = rule["pattern"]
    
    if rule_type == "process":
        return process_name.lower() == pattern.lower()
    elif rule_type == "title":
        if pattern.startswith("*") and pattern.endswith("*"):
            return pattern[1:-1].lower() in title.lower()
        elif pattern.startswith("*"):
            return title.lower().endswith(pattern[1:].lower())
        elif pattern.endswith("*"):
            return title.lower().startswith(pattern[:-1].lower())
        else:
            return pattern.lower() in title.lower()
    return False

def classify_window(title, process_name):
    """根据窗口标题和进程名判断分类"""
    for category, info in CATEGORIES.items():
        for rule in info["rules"]:
            if match_rule(rule, title, process_name):
                return category, info["icon"], info["color"], info["bg_color"]
    return "其他", "💻", QColor(149, 165, 166, 200), QColor(149, 165, 166, 30)

def get_active_window():
    """获取当前活动窗口信息"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            process = psutil.Process(pid)
            exe_name = process.name()
        except:
            exe_name = ""
        return title, exe_name
    except:
        return "", ""

class OverlayWindow(QWidget):
    """方案二 Demo：功能完整版悬浮窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WindowStatus Demo - 方案二")
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool  # 不在任务栏显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setFixedSize(320, 100)
        
        # 拖拽支持
        self.drag_position = QPoint()
        
        # 当前状态
        self.current_category = "其他"
        self.current_icon = "💻"
        self.current_color = QColor(149, 165, 166, 200)
        self.current_bg_color = QColor(149, 165, 166, 30)
        
        # 创建界面
        self._create_ui()
        
        # 窗口监控定时器
        self.last_title = ""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_window)
        self.monitor_timer.start(100)  # 100ms 检查一次
        
        # 动画
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def _create_ui(self):
        """创建界面"""
        # 主布局
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)
        
        # 左侧：分类图标
        self.icon_label = QLabel(self.current_icon)
        self.icon_label.setFont(QFont('Segoe UI Emoji', 24))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedWidth(50)
        layout.addWidget(self.icon_label)
        
        # 右侧：文字信息
        right_layout = QVBoxLayout()
        right_layout.setSpacing(2)
        
        # 分类名称
        self.category_label = QLabel(self.current_category)
        self.category_label.setFont(QFont('Microsoft YaHei UI', 12, QFont.Bold))
        self.category_label.setStyleSheet("color: white;")
        right_layout.addWidget(self.category_label)
        
        # 窗口标题
        self.title_label = QLabel("等待窗口切换...")
        self.title_label.setFont(QFont('Microsoft YaHei UI', 9))
        self.title_label.setStyleSheet("color: #b8b8b8;")
        self.title_label.setWordWrap(True)
        right_layout.addWidget(self.title_label)
        
        # 进程名
        self.process_label = QLabel("")
        self.process_label.setFont(QFont('Microsoft YaHei UI', 8))
        self.process_label.setStyleSheet("color: #808080;")
        right_layout.addWidget(self.process_label)
        
        layout.addLayout(right_layout, 1)
        self.setLayout(layout)
    
    def paintEvent(self, event):
        """绘制圆角背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制阴影效果
        path = QPainterPath()
        path.addRoundedRect(5, 5, self.width() - 10, self.height() - 10, 15, 15)
        
        # 绘制背景
        painter.fillPath(path, QColor(26, 26, 46, 220))  # 深色背景
        
        # 绘制分类颜色边框
        pen = painter.pen()
        pen.setColor(self.current_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def contextMenuEvent(self, event):
        """右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a2e;
                color: white;
                border: 1px solid #16213e;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #16213e;
            }
        """)
        
        quit_action = menu.addAction("退出")
        action = menu.exec_(event.globalPos())
        
        if action == quit_action:
            QApplication.quit()
    
    def update_display(self, title, process_name):
        """更新显示"""
        category, icon, color, bg_color = classify_window(title, process_name)
        
        # 检查是否需要更新
        if category == self.current_category:
            # 只更新标题
            display_title = title if len(title) <= 25 else title[:22] + "..."
            self.title_label.setText(display_title)
            self.process_label.setText(process_name)
            return
        
        # 更新状态
        self.current_category = category
        self.current_icon = icon
        self.current_color = color
        self.current_bg_color = bg_color
        
        # 更新界面
        self.icon_label.setText(icon)
        self.category_label.setText(category)
        
        display_title = title if len(title) <= 25 else title[:22] + "..."
        self.title_label.setText(display_title)
        self.process_label.setText(process_name)
        
        # 触发重绘
        self.update()
    
    def monitor_window(self):
        """监控窗口切换"""
        title, process_name = get_active_window()
        if title != self.last_title:
            self.update_display(title, process_name)
            self.last_title = title

class DemoApp:
    """Demo 应用"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # 创建悬浮窗
        self.overlay = OverlayWindow()
        self.overlay.show()
        
        # 创建系统托盘
        self._create_tray()
    
    def _create_tray(self):
        """创建系统托盘"""
        # 托盘图标
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon.fromTheme("utilities-system-monitor"))
        
        # 托盘菜单
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a2e;
                color: white;
                border: 1px solid #16213e;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #16213e;
            }
        """)
        
        show_action = tray_menu.addAction("显示悬浮窗")
        show_action.triggered.connect(self.overlay.show)
        
        hide_action = tray_menu.addAction("隐藏悬浮窗")
        hide_action.triggered.connect(self.overlay.hide)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.app.quit)
        
        self.tray.setContextMenu(tray_menu)
        self.tray.show()
    
    def run(self):
        """运行"""
        return self.app.exec_()

if __name__ == '__main__':
    print("WindowStatus Demo - 方案二（功能完整版）")
    print("=" * 40)
    print("功能：")
    print("  - PyQt5 深色主题悬浮窗")
    print("  - 圆角、半透明、阴影效果")
    print("  - 可拖拽、右键菜单")
    print("  - 系统托盘图标")
    print("  - 支持游戏/办公/摸鱼/开发分类")
    print("=" * 40)
    print("启动中...")
    
    demo = DemoApp()
    sys.exit(demo.run())