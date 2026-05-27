# -*- coding: utf-8 -*-
"""
WindowStatus Demo - 方案一：轻量版（tkinter）
运行方式：python demo_tkinter.py
"""

import tkinter as tk
import win32gui
import win32process
import psutil
import json
import os

# 分类规则配置
CATEGORIES = {
    "游戏": {
        "icon": "🎮",
        "color": "#FF6B6B",
        "rules": [
            {"type": "process", "pattern": "steam.exe"},
            {"type": "process", "pattern": "Unity.exe"},
            {"type": "process", "pattern": "UE4Editor.exe"},
            {"type": "title", "pattern": "*原神*"},
            {"type": "title", "pattern": "*英雄联盟*"},
            {"type": "title", "pattern": "*League of Legends*"},
        ]
    },
    "办公": {
        "icon": "📊",
        "color": "#4ECDC4",
        "rules": [
            {"type": "process", "pattern": "EXCEL.EXE"},
            {"type": "process", "pattern": "WINWORD.EXE"},
            {"type": "process", "pattern": "POWERPNT.EXE"},
            {"type": "title", "pattern": "*WPS*"},
            {"type": "title", "pattern": "*Excel*"},
            {"type": "title", "pattern": "*Word*"},
        ]
    },
    "摸鱼": {
        "icon": "🐟",
        "color": "#FFE66D",
        "rules": [
            {"type": "process", "pattern": "chrome.exe"},
            {"type": "process", "pattern": "msedge.exe"},
            {"type": "process", "pattern": "firefox.exe"},
            {"type": "title", "pattern": "*微博*"},
            {"type": "title", "pattern": "*B站*"},
            {"type": "title", "pattern": "*bilibili*"},
            {"type": "title", "pattern": "*抖音*"},
            {"type": "title", "pattern": "*知乎*"},
        ]
    },
    "开发": {
        "icon": "💻",
        "color": "#A8E6CF",
        "rules": [
            {"type": "process", "pattern": "Code.exe"},
            {"type": "process", "pattern": "devenv.exe"},
            {"type": "process", "pattern": "pycharm64.exe"},
            {"type": "process", "pattern": "idea64.exe"},
            {"type": "title", "pattern": "*Visual Studio*"},
            {"type": "title", "pattern": "*PyCharm*"},
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
        # 简单通配符匹配
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
                return category, info["icon"], info["color"]
    return "其他", "💻", "#95a5a6"

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

class DemoOverlay:
    """方案一 Demo：轻量悬浮窗"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WindowStatus Demo - 方案一")
        self.root.geometry("300x120+50+50")
        self.root.resizable(False, False)
        
        # 设置窗口样式
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes('-topmost', True)  # 置顶
        self.root.attributes('-alpha', 0.9)  # 半透明
        
        # 背景颜色
        self.root.configure(bg='#1a1a2e')
        
        # 创建界面
        self._create_ui()
        
        # 拖拽支持
        self.drag_x = 0
        self.drag_y = 0
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.on_drag)
        
        # 开始监控
        self.last_title = ""
        self.monitor_window()
        
        # 右键菜单
        self.root.bind('<Button-3>', self.show_menu)
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="退出", command=self.root.quit)
    
    def _create_ui(self):
        """创建界面"""
        # 主框架
        main_frame = tk.Frame(self.root, bg='#16213e', padx=15, pady=10)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 分类图标和名称
        self.category_label = tk.Label(
            main_frame,
            text="💻 其他",
            font=('Segoe UI Emoji', 14, 'bold'),
            fg='#ffffff',
            bg='#16213e',
            anchor='w'
        )
        self.category_label.pack(fill='x')
        
        # 窗口标题
        self.title_label = tk.Label(
            main_frame,
            text="等待窗口切换...",
            font=('Microsoft YaHei UI', 10),
            fg='#b8b8b8',
            bg='#16213e',
            anchor='w',
            wraplength=250
        )
        self.title_label.pack(fill='x', pady=(5, 0))
        
        # 进程名
        self.process_label = tk.Label(
            main_frame,
            text="",
            font=('Microsoft YaHei UI', 8),
            fg='#808080',
            bg='#16213e',
            anchor='w'
        )
        self.process_label.pack(fill='x', pady=(2, 0))
    
    def start_drag(self, event):
        """开始拖拽"""
        self.drag_x = event.x
        self.drag_y = event.y
    
    def on_drag(self, event):
        """拖拽中"""
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"+{x}+{y}")
    
    def show_menu(self, event):
        """显示右键菜单"""
        self.menu.post(event.x_root, event.y_root)
    
    def update_display(self, title, process_name):
        """更新显示"""
        category, icon, color = classify_window(title, process_name)
        
        # 更新分类
        self.category_label.config(text=f"{icon} {category}")
        
        # 更新标题（截断过长的标题）
        display_title = title if len(title) <= 30 else title[:27] + "..."
        self.title_label.config(text=display_title)
        
        # 更新进程名
        self.process_label.config(text=process_name)
        
        # 更新边框颜色
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=color)
    
    def monitor_window(self):
        """监控窗口切换"""
        title, process_name = get_active_window()
        if title != self.last_title:
            self.update_display(title, process_name)
            self.last_title = title
        self.root.after(100, self.monitor_window)  # 100ms 检查一次
    
    def run(self):
        """运行"""
        self.root.mainloop()

if __name__ == '__main__':
    print("WindowStatus Demo - 方案一（轻量版）")
    print("=" * 40)
    print("功能：")
    print("  - 实时显示当前活动窗口分类")
    print("  - 深色主题、半透明悬浮窗")
    print("  - 可拖拽、右键菜单退出")
    print("  - 支持游戏/办公/摸鱼/开发分类")
    print("=" * 40)
    print("启动中...")
    
    demo = DemoOverlay()
    demo.run()