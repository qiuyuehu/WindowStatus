# -*- coding: utf-8 -*-
"""
WindowStatus — Windows 窗口状态显示器
Author: 衾衾 (Hermes Agent)

功能：
- 实时监控当前活动窗口
- 自动分类（游戏/办公/摸鱼/开发/工具/其他）
- 悬浮窗显示（可拖拽、可调透明度、可置顶）
- 自定义分类规则
- 智能识别分类
- 使用统计（今日时间线、分类时长）
"""

import sys
import json
import os
import time
import sqlite3
from datetime import datetime, timedelta
import win32gui
import win32process
import psutil
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QApplication, QSystemTrayIcon, QMenu, QAction,
                             QSlider, QPushButton, QDialog, QLineEdit,
                             QComboBox, QListWidget, QListWidgetItem,
                             QGroupBox, QFormLayout, QMessageBox, QInputDialog,
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QProgressBar)
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont, QIcon

# 配置文件路径
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.WindowStatus')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
DB_FILE = os.path.join(CONFIG_DIR, 'data.db')

# 根据用户软件定制的分类规则
DEFAULT_CATEGORIES = {
    "游戏": {
        "icon": "🎮",
        "color": [255, 107, 107],
        "rules": [
            {"type": "process", "pattern": "steam.exe"},
            {"type": "process", "pattern": "steamwebhelper.exe"},
            {"type": "process", "pattern": "EpicGamesLauncher.exe"},
            {"type": "process", "pattern": "360game.exe"},
            {"type": "process", "pattern": "NarutoOnline.exe"},
            {"type": "title", "pattern": "*Naruto Online*"},
            {"type": "title", "pattern": "*火影忍者*"},
            {"type": "process", "pattern": "MuMuPlayer.exe"},
            {"type": "process", "pattern": "NemuPlayer.exe"},
            {"type": "process", "pattern": "OurPlay.exe"},
            {"type": "title", "pattern": "*MuMu*"},
            {"type": "title", "pattern": "*OurPlay*"},
            {"type": "process", "pattern": "cloudGenshin.exe"},
            {"type": "title", "pattern": "*云·原神*"},
            {"type": "process", "pattern": "GamePP.exe"},
            {"type": "process", "pattern": "Wallpaper64.exe"},
            {"type": "process", "pattern": "Wallpaper32.exe"},
            {"type": "title", "pattern": "*Wallpaper Engine*"},
            {"type": "process", "pattern": "miHoYoLauncher.exe"},
            {"type": "title", "pattern": "*米哈游*"},
            {"type": "title", "pattern": "*原神*"},
            {"type": "title", "pattern": "*崩坏*"},
            {"type": "title", "pattern": "*星穹铁道*"},
            {"type": "process", "pattern": "guiguai.exe"},
            {"type": "title", "pattern": "*古怪加速器*"},
        ]
    },
    "办公": {
        "icon": "📊",
        "color": [78, 205, 196],
        "rules": [
            {"type": "process", "pattern": "EXCEL.EXE"},
            {"type": "process", "pattern": "WINWORD.EXE"},
            {"type": "process", "pattern": "POWERPNT.EXE"},
            {"type": "process", "pattern": "ONENOTE.EXE"},
            {"type": "process", "pattern": "OUTLOOK.EXE"},
            {"type": "process", "pattern": "officeclicktorun.exe"},
            {"type": "process", "pattern": "TIM.exe"},
            {"type": "process", "pattern": "QQ.exe"},
            {"type": "process", "pattern": "WeChat.exe"},
            {"type": "process", "pattern": "telegram.exe"},
            {"type": "process", "pattern": "DingTalk.exe"},
            {"type": "process", "pattern": "Feishu.exe"},
            {"type": "process", "pattern": "Lark.exe"},
            {"type": "title", "pattern": "*钉钉*"},
            {"type": "title", "pattern": "*飞书*"},
            {"type": "process", "pattern": "123Pan.exe"},
            {"type": "process", "pattern": "AliyunPan.exe"},
            {"type": "process", "pattern": "Quark.exe"},
            {"type": "title", "pattern": "*123云盘*"},
            {"type": "title", "pattern": "*阿里云盘*"},
            {"type": "title", "pattern": "*夸克*"},
            {"type": "process", "pattern": "UURemote.exe"},
            {"type": "title", "pattern": "*UU远程*"},
        ]
    },
    "摸鱼": {
        "icon": "🐟",
        "color": [255, 230, 109],
        "rules": [
            {"type": "process", "pattern": "chrome.exe"},
            {"type": "process", "pattern": "msedge.exe"},
            {"type": "process", "pattern": "firefox.exe"},
            {"type": "process", "pattern": "FlashBrowser.exe"},
            {"type": "process", "pattern": "bilibili.exe"},
            {"type": "process", "pattern": "哔哩哔哩直播姬.exe"},
            {"type": "process", "pattern": "必剪.exe"},
            {"type": "title", "pattern": "*B站*"},
            {"type": "title", "pattern": "*bilibili*"},
            {"type": "title", "pattern": "*哔哩哔哩*"},
            {"type": "title", "pattern": "*抖音*"},
            {"type": "title", "pattern": "*快手*"},
            {"type": "title", "pattern": "*YouTube*"},
            {"type": "title", "pattern": "*微博*"},
            {"type": "title", "pattern": "*知乎*"},
            {"type": "title", "pattern": "*贴吧*"},
            {"type": "title", "pattern": "*豆瓣*"},
            {"type": "title", "pattern": "*小红书*"},
            {"type": "process", "pattern": "YesPlayMusic.exe"},
            {"type": "process", "pattern": "cloudmusic.exe"},
            {"type": "process", "pattern": "QQMusic.exe"},
            {"type": "title", "pattern": "*网易云音乐*"},
            {"type": "title", "pattern": "*QQ音乐*"},
            {"type": "process", "pattern": "doubao.exe"},
            {"type": "title", "pattern": "*豆包*"},
        ]
    },
    "开发": {
        "icon": "💻",
        "color": [168, 230, 207],
        "rules": [
            {"type": "process", "pattern": "Code.exe"},
            {"type": "process", "pattern": "devenv.exe"},
            {"type": "process", "pattern": "pycharm64.exe"},
            {"type": "process", "pattern": "idea64.exe"},
            {"type": "process", "pattern": "webstorm64.exe"},
            {"type": "process", "pattern": "sublime_text.exe"},
            {"type": "title", "pattern": "*Visual Studio*"},
            {"type": "title", "pattern": "*PyCharm*"},
            {"type": "title", "pattern": "*IntelliJ*"},
            {"type": "title", "pattern": "*WebStorm*"},
            {"type": "title", "pattern": "*VS Code*"},
            {"type": "process", "pattern": "WindowsTerminal.exe"},
            {"type": "process", "pattern": "cmd.exe"},
            {"type": "process", "pattern": "powershell.exe"},
            {"type": "process", "pattern": "pwsh.exe"},
            {"type": "process", "pattern": "Hyper.exe"},
            {"type": "process", "pattern": "wt.exe"},
            {"type": "process", "pattern": "git.exe"},
            {"type": "process", "pattern": "GitHubDesktop.exe"},
            {"type": "process", "pattern": "node.exe"},
            {"type": "process", "pattern": "npm.exe"},
            {"type": "process", "pattern": "npx.exe"},
            {"type": "process", "pattern": "python.exe"},
            {"type": "process", "pattern": "pythonw.exe"},
            {"type": "process", "pattern": "pip.exe"},
            {"type": "process", "pattern": "ollama.exe"},
            {"type": "process", "pattern": "Ollama App.exe"},
            {"type": "title", "pattern": "*Ollama*"},
            {"type": "process", "pattern": "mysqld.exe"},
            {"type": "process", "pattern": "postgres.exe"},
            {"type": "process", "pattern": "redis-server.exe"},
            {"type": "process", "pattern": "Docker Desktop.exe"},
            {"type": "process", "pattern": "docker.exe"},
        ]
    },
    "工具": {
        "icon": "🔧",
        "color": [149, 165, 166],
        "rules": [
            {"type": "process", "pattern": "explorer.exe"},
            {"type": "process", "pattern": "taskmgr.exe"},
            {"type": "process", "pattern": "regedit.exe"},
            {"type": "process", "pattern": "msconfig.exe"},
            {"type": "process", "pattern": "control.exe"},
            {"type": "process", "pattern": "Everything.exe"},
            {"type": "process", "pattern": "7zFM.exe"},
            {"type": "process", "pattern": "WinRAR.exe"},
            {"type": "title", "pattern": "*Everything*"},
            {"type": "process", "pattern": "SnippingTool.exe"},
            {"type": "process", "pattern": "i_view64.exe"},
            {"type": "title", "pattern": "*IrfanView*"},
            {"type": "process", "pattern": "PowerToys.AdvancedPaste.exe"},
            {"type": "process", "pattern": "PowerToys.ColorPickerUI.exe"},
            {"type": "process", "pattern": "PowerToys.Peek.UI.exe"},
            {"type": "process", "pattern": "clash-verge.exe"},
            {"type": "process", "pattern": "verge-mihomo.exe"},
            {"type": "title", "pattern": "*Clash*"},
            {"type": "process", "pattern": "lghub.exe"},
            {"type": "process", "pattern": "lghub_agent.exe"},
            {"type": "title", "pattern": "*Logitech G HUB*"},
            {"type": "process", "pattern": "i4Tools.exe"},
            {"type": "title", "pattern": "*爱思助手*"},
        ]
    }
}

# 智能识别关键词
SMART_KEYWORDS = {
    "游戏": ["游戏", "game", "play", "steam", "epic", "origin", "育碧", "暴雪", 
             "原神", "崩坏", "星穹", "火影", "英雄联盟", "LOL", "DOTA", "CS", "VALORANT",
             "启动器", "launcher", "加速器", "模拟器", "emulator"],
    "办公": ["办公", "office", "文档", "表格", "演示", "会议", "邮件", "outlook", 
             "teams", "zoom", "腾讯会议", "钉钉", "飞书", "企业微信", "云盘", "网盘"],
    "摸鱼": ["视频", "音乐", "社交", "微博", "b站", "bilibili", "抖音", "快手", 
             "小红书", "知乎", "贴吧", "豆瓣", "twitter", "facebook", "instagram", 
             "youtube", "直播", "游戏", "漫画", "小说"],
    "开发": ["开发", "code", "编程", "ide", "editor", "terminal", "cmd", "powershell", 
             "git", "github", "vscode", "pycharm", "intellij", "node", "python", 
             "npm", "docker", "database", "数据库", "redis", "mysql", "postgres"],
    "工具": ["工具", "tool", "管理", "manager", "设置", "settings", "系统", "system",
             "截图", "录屏", "代理", "proxy", "vpn", "外设", "驱动", "driver"],
}


class Database:
    """数据库管理"""
    
    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_FILE)
        self._create_tables()
    
    def _create_tables(self):
        """创建表"""
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
    
    def log_activity(self, window_title, process_name, category, start_time, duration):
        """记录活动"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO activity_log (window_title, process_name, category, start_time, end_time, duration)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (window_title, process_name, category, start_time, 
              start_time + timedelta(seconds=duration), duration))
        self.conn.commit()
    
    def get_today_stats(self):
        """获取今日统计"""
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
    
    def get_today_timeline(self):
        """获取今日时间线"""
        today = datetime.now().date()
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT window_title, process_name, category, start_time, duration
            FROM activity_log
            WHERE DATE(start_time) = ?
            ORDER BY start_time DESC
            LIMIT 50
        ''', (today,))
        return cursor.fetchall()
    
    def get_recent_activity(self, limit=10):
        """获取最近活动"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT window_title, process_name, category, start_time, duration
            FROM activity_log
            ORDER BY start_time DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def close(self):
        """关闭连接"""
        self.conn.close()


def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for name, info in DEFAULT_CATEGORIES.items():
                    if name not in config.get("categories", {}):
                        config.setdefault("categories", {})[name] = info
                return config
        except:
            pass
    return {"categories": DEFAULT_CATEGORIES, "opacity": 0.9, "always_on_top": True}

def save_config(config):
    """保存配置文件"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

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

def smart_classify(title, process_name):
    """智能识别分类"""
    title_lower = title.lower()
    process_lower = process_name.lower()
    
    for category, keywords in SMART_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in title_lower or keyword.lower() in process_lower:
                return category
    return None

def classify_window(title, process_name, categories):
    """根据窗口标题和进程名判断分类"""
    for category, info in categories.items():
        for rule in info.get("rules", []):
            if match_rule(rule, title, process_name):
                return category, info.get("icon", "📋"), info.get("color", [149, 165, 166])
    
    smart_result = smart_classify(title, process_name)
    if smart_result and smart_result in categories:
        info = categories[smart_result]
        return smart_result, info.get("icon", "📋"), info.get("color", [149, 165, 166])
    
    return "其他", "💻", [149, 165, 166]

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

def format_duration(seconds):
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


class StatsDialog(QDialog):
    """统计对话框"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("WindowStatus 使用统计")
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #16213e;
                background-color: #1a1a2e;
            }
            QTabBar::tab {
                background-color: #16213e;
                color: white;
                padding: 8px 16px;
                border: 1px solid #0f3460;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #0f3460;
            }
            QTableWidget {
                background-color: #16213e;
                color: white;
                border: 1px solid #0f3460;
                gridline-color: #0f3460;
            }
            QHeaderView::section {
                background-color: #0f3460;
                color: white;
                padding: 5px;
                border: 1px solid #16213e;
            }
            QLabel {
                color: white;
            }
            QProgressBar {
                border: 1px solid #0f3460;
                border-radius: 3px;
                text-align: center;
                background-color: #16213e;
            }
            QProgressBar::chunk {
                background-color: #4ECDC4;
                border-radius: 2px;
            }
        """)
        
        self._create_ui()
        self._load_data()
    
    def _create_ui(self):
        layout = QVBoxLayout()
        
        # 标签页
        tabs = QTabWidget()
        
        # 今日统计页
        stats_widget = QWidget()
        stats_layout = QVBoxLayout()
        
        # 分类统计
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(3)
        self.stats_table.setHorizontalHeaderLabels(["分类", "时长", "占比"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        stats_layout.addWidget(self.stats_table)
        
        stats_widget.setLayout(stats_layout)
        tabs.addTab(stats_widget, "今日统计")
        
        # 时间线页
        timeline_widget = QWidget()
        timeline_layout = QVBoxLayout()
        
        self.timeline_table = QTableWidget()
        self.timeline_table.setColumnCount(4)
        self.timeline_table.setHorizontalHeaderLabels(["时间", "窗口", "分类", "时长"])
        self.timeline_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        timeline_layout.addWidget(self.timeline_table)
        
        timeline_widget.setLayout(timeline_layout)
        tabs.addTab(timeline_widget, "时间线")
        
        layout.addWidget(tabs)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def _load_data(self):
        """加载数据"""
        # 今日统计
        stats = self.db.get_today_stats()
        self.stats_table.setRowCount(len(stats))
        
        total_duration = sum(s[1] for s in stats) if stats else 1
        
        for i, (category, duration) in enumerate(stats):
            self.stats_table.setItem(i, 0, QTableWidgetItem(category))
            self.stats_table.setItem(i, 1, QTableWidgetItem(format_duration(duration)))
            
            percentage = (duration / total_duration) * 100
            self.stats_table.setItem(i, 2, QTableWidgetItem(f"{percentage:.1f}%"))
        
        # 时间线
        timeline = self.db.get_today_timeline()
        self.timeline_table.setRowCount(len(timeline))
        
        for i, (title, process, category, start_time, duration) in enumerate(timeline):
            # 格式化时间
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            time_str = start_time.strftime("%H:%M")
            
            self.timeline_table.setItem(i, 0, QTableWidgetItem(time_str))
            
            # 窗口标题（截断）
            display_title = title[:30] + "..." if len(title) > 30 else title
            self.timeline_table.setItem(i, 1, QTableWidgetItem(display_title))
            self.timeline_table.setItem(i, 2, QTableWidgetItem(category))
            self.timeline_table.setItem(i, 3, QTableWidgetItem(format_duration(duration)))


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("WindowStatus 设置")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                color: white;
            }
            QGroupBox {
                border: 1px solid #16213e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: white;
            }
            QLineEdit, QComboBox {
                background-color: #16213e;
                color: white;
                border: 1px solid #0f3460;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #16213e;
            }
            QListWidget {
                background-color: #16213e;
                color: white;
                border: 1px solid #0f3460;
                border-radius: 3px;
            }
        """)
        
        self._create_ui()
    
    def _create_ui(self):
        layout = QVBoxLayout()
        
        category_group = QGroupBox("分类管理")
        category_layout = QVBoxLayout()
        
        self.category_list = QListWidget()
        self._refresh_category_list()
        category_layout.addWidget(self.category_list)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加分类")
        add_btn.clicked.connect(self._add_category)
        edit_btn = QPushButton("编辑规则")
        edit_btn.clicked.connect(self._edit_rules)
        delete_btn = QPushButton("删除分类")
        delete_btn.clicked.connect(self._delete_category)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        category_layout.addLayout(btn_layout)
        
        category_group.setLayout(category_layout)
        layout.addWidget(category_group)
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
        
        self.setLayout(layout)
    
    def _refresh_category_list(self):
        self.category_list.clear()
        for name, info in self.config.get("categories", {}).items():
            icon = info.get("icon", "📋")
            rules_count = len(info.get("rules", []))
            self.category_list.addItem(f"{icon} {name} ({rules_count} 条规则)")
    
    def _add_category(self):
        name, ok = QInputDialog.getText(self, "添加分类", "分类名称：")
        if ok and name:
            icon, ok = QInputDialog.getText(self, "添加分类", "分类图标（emoji）：", text="📋")
            if ok:
                self.config.setdefault("categories", {})[name] = {
                    "icon": icon,
                    "color": [149, 165, 166],
                    "rules": []
                }
                save_config(self.config)
                self._refresh_category_list()
    
    def _edit_rules(self):
        current = self.category_list.currentItem()
        if not current:
            QMessageBox.warning(self, "提示", "请先选择一个分类")
            return
        
        text = current.text()
        category_name = text.split(" ", 1)[1].rsplit(" (", 1)[0]
        
        rules_text = ""
        for rule in self.config["categories"][category_name].get("rules", []):
            rules_text += f"{rule['type']}:{rule['pattern']}\n"
        
        new_rules, ok = QInputDialog.getMultiLineText(
            self, f"编辑 {category_name} 规则",
            "每行一条规则，格式：type:pattern\n例如：process:chrome.exe\n例如：title:*B站*",
            rules_text
        )
        
        if ok:
            rules = []
            for line in new_rules.strip().split('\n'):
                line = line.strip()
                if ':' in line:
                    rule_type, pattern = line.split(':', 1)
                    rules.append({"type": rule_type.strip(), "pattern": pattern.strip()})
            self.config["categories"][category_name]["rules"] = rules
            save_config(self.config)
            self._refresh_category_list()
    
    def _delete_category(self):
        current = self.category_list.currentItem()
        if not current:
            QMessageBox.warning(self, "提示", "请先选择一个分类")
            return
        
        text = current.text()
        category_name = text.split(" ", 1)[1].rsplit(" (", 1)[0]
        
        reply = QMessageBox.question(self, "确认", f"确定要删除分类 '{category_name}' 吗？")
        if reply == QMessageBox.Yes:
            del self.config["categories"][category_name]
            save_config(self.config)
            self._refresh_category_list()


class OverlayWindow(QWidget):
    """悬浮窗"""
    
    def __init__(self, config, db):
        super().__init__()
        self.config = config
        self.db = db
        self.setWindowTitle("WindowStatus")
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 100)
        
        self.drag_position = QPoint()
        self.current_category = "其他"
        self.current_icon = "💻"
        self.current_color = QColor(149, 165, 166)
        
        self._create_ui()
        
        # 记录当前活动
        self.current_title = ""
        self.current_process = ""
        self.current_start_time = None
        
        # 时长更新定时器
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self._update_duration)
        self.duration_timer.start(1000)  # 每秒更新
        
        self.last_title = ""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_window)
        self.monitor_timer.start(100)
        
        self.setWindowOpacity(config.get("opacity", 0.9))
    
    def _create_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)
        
        self.icon_label = QLabel(self.current_icon)
        self.icon_label.setFont(QFont('Segoe UI Emoji', 24))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedWidth(50)
        layout.addWidget(self.icon_label)
        
        right_layout = QVBoxLayout()
        right_layout.setSpacing(2)
        
        self.category_label = QLabel(self.current_category)
        self.category_label.setFont(QFont('Microsoft YaHei UI', 12, QFont.Bold))
        self.category_label.setStyleSheet("color: white;")
        right_layout.addWidget(self.category_label)
        
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
        
        # 使用时长
        self.duration_label = QLabel("")
        self.duration_label.setFont(QFont('Microsoft YaHei UI', 8))
        self.duration_label.setStyleSheet("color: #4ECDC4;")
        right_layout.addWidget(self.duration_label)
        
        layout.addLayout(right_layout, 1)
        self.setLayout(layout)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addRoundedRect(5, 5, self.width() - 10, self.height() - 10, 15, 15)
        
        painter.fillPath(path, QColor(26, 26, 46, 220))
        
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
    
    def update_display(self, title, process_name):
        categories = self.config.get("categories", {})
        category, icon, color = classify_window(title, process_name, categories)
        
        # 记录上一个活动的时长
        if self.current_start_time and self.current_title:
            duration = int((datetime.now() - self.current_start_time).total_seconds())
            if duration > 0:
                self.db.log_activity(
                    self.current_title, self.current_process, 
                    self.current_category, self.current_start_time, duration
                )
        
        # 更新当前活动
        self.current_category = category
        self.current_icon = icon
        self.current_color = QColor(*color)
        self.current_title = title
        self.current_process = process_name
        self.current_start_time = datetime.now()
        
        self.icon_label.setText(icon)
        self.category_label.setText(category)
        
        display_title = title if len(title) <= 25 else title[:22] + "..."
        self.title_label.setText(display_title)
        self.process_label.setText(process_name)
        
        self.update()
    
    def monitor_window(self):
        title, process_name = get_active_window()
        if title != self.last_title:
            self.update_display(title, process_name)
            self.last_title = title
    
    def _update_duration(self):
        """更新使用时长显示"""
        if self.current_start_time:
            duration = int((datetime.now() - self.current_start_time).total_seconds())
            self.duration_label.setText(f"⏱ {format_duration(duration)}")
    
    def set_opacity(self, opacity):
        self.setWindowOpacity(opacity)
        self.config["opacity"] = opacity
        save_config(self.config)
    
    def set_always_on_top(self, enabled):
        if enabled:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
        self.config["always_on_top"] = enabled
        save_config(self.config)


class TrayApp:
    """系统托盘应用"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.config = load_config()
        self.db = Database()
        
        self.overlay = OverlayWindow(self.config, self.db)
        self.overlay.show()
        
        self._create_tray()
    
    def _create_tray(self):
        self.tray = QSystemTrayIcon()
        
        # 创建简单的托盘图标
        from PyQt5.QtGui import QPixmap, QPainter, QColor
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(78, 205, 196))  # 青色图标
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont('Arial', 16, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "W")
        painter.end()
        self.tray.setIcon(QIcon(pixmap))
        
        self.tray.setToolTip("WindowStatus - 窗口状态显示器")
        
        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet("""
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
        
        show_action = self.tray_menu.addAction("显示悬浮窗")
        show_action.triggered.connect(self.overlay.show)
        
        hide_action = self.tray_menu.addAction("隐藏悬浮窗")
        hide_action.triggered.connect(self.overlay.hide)
        
        self.tray_menu.addSeparator()
        
        self.top_action = self.tray_menu.addAction("取消置顶" if self.config.get("always_on_top", True) else "置顶")
        self.top_action.triggered.connect(self._toggle_top)
        
        self.tray_menu.addSeparator()
        
        opacity_menu = self.tray_menu.addMenu("透明度")
        for value in [100, 90, 80, 70, 60, 50]:
            action = opacity_menu.addAction(f"{value}%")
            action.triggered.connect(lambda checked, v=value: self.overlay.set_opacity(v / 100))
        
        self.tray_menu.addSeparator()
        
        stats_action = self.tray_menu.addAction("使用统计")
        stats_action.triggered.connect(self._show_stats)
        
        settings_action = self.tray_menu.addAction("设置")
        settings_action.triggered.connect(self._show_settings)
        
        self.tray_menu.addSeparator()
        
        # 开机自启动
        self.autostart_action = self.tray_menu.addAction("开机自启动")
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(self._is_autostart_enabled())
        self.autostart_action.triggered.connect(self._toggle_autostart)
        
        self.tray_menu.addSeparator()
        
        quit_action = self.tray_menu.addAction("退出")
        quit_action.triggered.connect(self._quit)
        
        self.tray.setContextMenu(self.tray_menu)
        self.tray.show()
    
    def _toggle_top(self):
        current = self.config.get("always_on_top", True)
        new_state = not current
        self.overlay.set_always_on_top(new_state)
        self.top_action.setText("取消置顶" if new_state else "置顶")
    
    def _show_stats(self):
        dialog = StatsDialog(self.db)
        dialog.exec_()
    
    def _show_settings(self):
        dialog = SettingsDialog(self.config)
        if dialog.exec_() == QDialog.Accepted:
            pass
    
    def _is_autostart_enabled(self):
        """检查是否已启用开机自启动"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, "WindowStatus")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except:
            return False
    
    def _toggle_autostart(self, checked):
        """切换开机自启动"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            
            if checked:
                # 获取当前脚本路径
                if getattr(sys, 'frozen', False):
                    # 打包后的 exe
                    app_path = sys.executable
                else:
                    # Python 脚本
                    app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
                
                winreg.SetValueEx(key, "WindowStatus", 0, winreg.REG_SZ, app_path)
                QMessageBox.information(self, "提示", "已启用开机自启动")
            else:
                try:
                    winreg.DeleteValue(key, "WindowStatus")
                except FileNotFoundError:
                    pass
                QMessageBox.information(self, "提示", "已禁用开机自启动")
            
            winreg.CloseKey(key)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"设置开机自启动失败：{e}")
    
    def _quit(self):
        # 退出前记录最后一个活动
        if self.overlay.current_start_time and self.overlay.current_title:
            duration = int((datetime.now() - self.overlay.current_start_time).total_seconds())
            if duration > 0:
                self.db.log_activity(
                    self.overlay.current_title, self.overlay.current_process,
                    self.overlay.current_category, self.overlay.current_start_time, duration
                )
        self.db.close()
        self.app.quit()
    
    def run(self):
        return self.app.exec_()

if __name__ == '__main__':
    print("WindowStatus — Windows 窗口状态显示器")
    print("=" * 40)
    print("功能：")
    print("  - 实时监控当前活动窗口")
    print("  - 自动分类（游戏/办公/摸鱼/开发/工具/其他）")
    print("  - 悬浮窗显示（可拖拽、可调透明度、可置顶）")
    print("  - 自定义分类规则")
    print("  - 智能识别分类")
    print("  - 使用统计（今日时间线、分类时长）")
    print("=" * 40)
    print("启动中...")
    print("（程序在后台运行，请查看系统托盘图标）")
    
    tray_app = TrayApp()
    sys.exit(tray_app.run())