# -*- coding: utf-8 -*-
"""
Settings 设置窗口
提供分类规则编辑和插件管理界面
"""

from typing import Dict, List, Optional, Callable

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QComboBox, QLineEdit,
    QInputDialog, QMessageBox, QWidget, QAbstractItemView, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from plugins.utils import CustomTabBar, FramelessDialog, ToggleSwitch


# ============================================================
# 共享样式
# ============================================================

DIALOG_STYLESHEET = """
    QDialog {
        color: #e8e8e8;
    }
    QListWidget {
        background-color: #1a1a1a;
        color: #e8e8e8;
        border: 1px solid #2a2a2a;
        outline: none;
    }
    QListWidget::item {
        padding: 6px 10px;
    }
    QListWidget::item:selected {
        background-color: #252525;
        color: #a0a0a0;
    }
    QListWidget::item:hover {
        background-color: #222;
    }
    QTableWidget {
        background-color: #1a1a1a;
        color: #e8e8e8;
        border: 1px solid #2a2a2a;
        gridline-color: #1e1e1e;
    }
    QHeaderView::section {
        background-color: #0f0f0f;
        color: #e8e8e8;
        padding: 5px;
        border: none;
    }
    QTabWidget::pane {
        border: none;
        background-color: #121212;
    }
    QPushButton {
        background-color: #1a1a1a;
        color: #e8e8e8;
        border: 1px solid #333;
        padding: 6px 14px;
        border-radius: 4px;
        min-width: 60px;
    }
    QPushButton:hover {
        background-color: #252525;
    }
    QPushButton#primary {
        background-color: #d97706;
        color: #fff;
        border: none;
    }
    QPushButton#primary:hover {
        background-color: #b45309;
    }
    QPushButton:disabled {
        background-color: #1e1e1e;
        color: #555;
    }
    QCheckBox {
        color: #e8e8e8;
        spacing: 6px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
    }
    QCheckBox::indicator:unchecked {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 3px;
    }
    QCheckBox::indicator:checked {
        background-color: #d97706;
        border: 1px solid #d97706;
        border-radius: 3px;
    }
    QLabel {
        color: #999;
    }
"""


# ============================================================
# 规则编辑对话框
# ============================================================

class RuleEditorDialog(QDialog):
    """单条规则的编辑/新增对话框"""

    def __init__(self, rule_type: str = "process", pattern: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑规则")
        self.setFixedSize(400, 150)
        self.setStyleSheet(DIALOG_STYLESHEET)
        self._rule_type = rule_type
        self._pattern = pattern
        self._result = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["process", "title"])
        self.type_combo.setCurrentText(self._rule_type)
        self.type_combo.setToolTip("process = 匹配进程名，title = 匹配窗口标题")
        type_layout.addWidget(self.type_combo, 1)
        layout.addLayout(type_layout)

        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("模式:"))
        self.pattern_edit = QLineEdit(self._pattern)
        self.pattern_edit.setPlaceholderText("例: chrome.exe  或  *YouTube*")
        pattern_layout.addWidget(self.pattern_edit, 1)
        layout.addLayout(pattern_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("确定")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _on_save(self):
        pattern = self.pattern_edit.text().strip()
        if not pattern:
            QMessageBox.warning(self, "提示", "请输入匹配模式")
            return
        self._result = {"type": self.type_combo.currentText(), "pattern": pattern}
        self.accept()

    def get_result(self) -> Optional[dict]:
        return self._result


# ============================================================
# 分类规则标签页
# ============================================================

class CategoriesTab(QWidget):
    """分类规则编辑标签页"""

    def __init__(self, categories: Dict[str, dict], parent=None):
        super().__init__(parent)
        self._categories = {k: {
            "icon": v.get("icon", "💻"),
            "color": v.get("color", [149, 165, 166]),
            "rules": [r.copy() for r in v.get("rules", [])]
        } for k, v in categories.items()}

        self._selected_category: Optional[str] = None
        self._init_ui()
        self._refresh_category_list()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        # 左侧：分类列表
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(5, 5, 5, 5)

        left_header = QHBoxLayout()
        left_header.addWidget(QLabel("分类"))
        left_header.addStretch()
        self.btn_add_cat = QPushButton("+ 添加")
        self.btn_add_cat.clicked.connect(self._on_add_category)
        left_header.addWidget(self.btn_add_cat)
        left_layout.addLayout(left_header)

        self.category_list = QListWidget()
        self.category_list.currentItemChanged.connect(self._on_category_selected)
        left_layout.addWidget(self.category_list)

        self.btn_del_cat = QPushButton("删除分类")
        self.btn_del_cat.clicked.connect(self._on_delete_category)
        self.btn_del_cat.setEnabled(False)
        left_layout.addWidget(self.btn_del_cat)

        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        # 右侧：规则表格
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(5, 5, 5, 5)

        right_header = QHBoxLayout()
        self.rules_label = QLabel("规则列表")
        self.rules_label.setStyleSheet("color: white; font-weight: bold;")
        right_header.addWidget(self.rules_label)
        right_header.addStretch()
        self.btn_add_rule = QPushButton("+ 添加规则")
        self.btn_add_rule.clicked.connect(self._on_add_rule)
        self.btn_add_rule.setEnabled(False)
        right_header.addWidget(self.btn_add_rule)
        right_layout.addLayout(right_header)

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(2)
        self.rules_table.setHorizontalHeaderLabels(["类型", "匹配模式"])
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.rules_table.doubleClicked.connect(self._on_edit_rule)
        right_layout.addWidget(self.rules_table)

        rule_btn_layout = QHBoxLayout()
        self.btn_edit_rule = QPushButton("编辑规则")
        self.btn_edit_rule.clicked.connect(self._on_edit_rule)
        self.btn_edit_rule.setEnabled(False)
        self.btn_del_rule = QPushButton("删除规则")
        self.btn_del_rule.clicked.connect(self._on_delete_rule)
        self.btn_del_rule.setEnabled(False)
        rule_btn_layout.addWidget(self.btn_edit_rule)
        rule_btn_layout.addWidget(self.btn_del_rule)
        rule_btn_layout.addStretch()
        right_layout.addLayout(rule_btn_layout)

        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)
        self.setLayout(layout)

    def get_categories(self) -> Dict[str, dict]:
        return self._categories

    # ---- 分类操作 ----

    def _refresh_category_list(self):
        self.category_list.clear()
        for name in self._categories:
            icon = self._categories[name].get("icon", "💻")
            item = QListWidgetItem(f"{icon}  {name}")
            item.setData(Qt.UserRole, name)
            self.category_list.addItem(item)

    def _on_category_selected(self, current: QListWidgetItem, _previous):
        if current is None:
            self._selected_category = None
            self.rules_table.setRowCount(0)
            self.rules_label.setText("规则列表")
            self._set_rule_buttons_enabled(False)
            self.btn_del_cat.setEnabled(False)
            self.btn_add_rule.setEnabled(False)
            return
        self._selected_category = current.data(Qt.UserRole)
        self.btn_del_cat.setEnabled(True)
        self.btn_add_rule.setEnabled(True)
        self._refresh_rules_table()

    def _on_add_category(self):
        name, ok = QInputDialog.getText(self, "添加分类", "分类名称:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self._categories:
            QMessageBox.warning(self, "提示", f"分类 '{name}' 已存在")
            return
        self._categories[name] = {"icon": "📁", "color": [149, 165, 166], "rules": []}
        self._refresh_category_list()
        items = self.category_list.findItems(name, Qt.MatchContains)
        if items:
            self.category_list.setCurrentItem(items[0])

    def _on_delete_category(self):
        if not self._selected_category:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除分类 '{self._selected_category}' 及其所有规则吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        del self._categories[self._selected_category]
        self._selected_category = None
        self._refresh_category_list()
        self.rules_table.setRowCount(0)

    # ---- 规则操作 ----

    def _refresh_rules_table(self):
        self.rules_table.setRowCount(0)
        if not self._selected_category:
            return
        rules = self._categories[self._selected_category].get("rules", [])
        self.rules_table.setRowCount(len(rules))
        self.rules_label.setText(f"规则列表 — {self._selected_category} ({len(rules)} 条)")
        type_labels = {"process": "进程名", "title": "窗口标题"}
        for row, rule in enumerate(rules):
            rule_type = rule.get("type", "")
            type_item = QTableWidgetItem(type_labels.get(rule_type, rule_type))
            type_item.setData(Qt.UserRole, rule_type)
            self.rules_table.setItem(row, 0, type_item)
            self.rules_table.setItem(row, 1, QTableWidgetItem(rule.get("pattern", "")))

    def _set_rule_buttons_enabled(self, enabled: bool):
        self.btn_edit_rule.setEnabled(enabled)
        self.btn_del_rule.setEnabled(enabled)

    def _on_add_rule(self):
        if not self._selected_category:
            return
        dialog = RuleEditorDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()
            if result:
                self._categories[self._selected_category].setdefault("rules", []).append(result)
                self._refresh_rules_table()

    def _on_edit_rule(self):
        if not self._selected_category:
            return
        row = self.rules_table.currentRow()
        if row < 0:
            return
        rules = self._categories[self._selected_category].get("rules", [])
        if row >= len(rules):
            return
        rule = rules[row]
        dialog = RuleEditorDialog(rule_type=rule.get("type", "process"), pattern=rule.get("pattern", ""), parent=self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()
            if result:
                rules[row] = result
                self._refresh_rules_table()

    def _on_delete_rule(self):
        if not self._selected_category:
            return
        row = self.rules_table.currentRow()
        if row < 0:
            return
        rules = self._categories[self._selected_category].get("rules", [])
        if row >= len(rules):
            return
        del rules[row]
        self._refresh_rules_table()

    # 规则选择变化
    def showEvent(self, event):
        super().showEvent(event)
        self.rules_table.itemSelectionChanged.connect(self._on_rule_selection_changed)

    def _on_rule_selection_changed(self):
        has_selection = len(self.rules_table.selectedItems()) > 0
        self._set_rule_buttons_enabled(has_selection)


# ============================================================
# 插件管理标签页
# ============================================================

class PluginsTab(QWidget):
    """插件管理标签页"""

    def __init__(self, plugins_info: List[dict], parent=None):
        """
        Args:
            plugins_info: [{"name": "overlay", "description": "...", "enabled": True}, ...]
        """
        super().__init__(parent)
        self._plugins = [p.copy() for p in plugins_info]
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        hint = QLabel("启用/禁用插件。更改在下次启动时生效。")
        hint.setStyleSheet("color: #808080; font-size: 12px;")
        layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["启用", "插件名称", "说明"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        self.table.setRowCount(len(self._plugins))
        for row, plugin in enumerate(self._plugins):
            # toggle 开关
            toggle = ToggleSwitch(checked=plugin["enabled"])
            toggle.toggled.connect(lambda checked, r=row: self._on_toggle(r, checked))
            self.table.setCellWidget(row, 0, toggle)

            # 插件名
            name_item = QTableWidgetItem(plugin["name"])
            name_item.setFont(QFont("Consolas", 10))
            self.table.setItem(row, 1, name_item)

            # 说明
            desc_item = QTableWidgetItem(plugin.get("description", ""))
            self.table.setItem(row, 2, desc_item)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def _on_toggle(self, row: int, checked: bool):
        self._plugins[row]["enabled"] = checked

    def get_plugins_config(self) -> Dict[str, bool]:
        """获取插件启用/禁用配置"""
        return {p["name"]: p["enabled"] for p in self._plugins}


# ============================================================
# 通用设置标签页
# ============================================================

class GeneralTab(QWidget):
    """通用设置标签页 — 按 demo 设计：侧边栏 + 功能分组"""

    SIDEBAR_ITEMS = [
        ("⚙️ 通用设置", "general"),
        ("🎨 外观", "appearance"),
        ("🔔 通知", "notifications"),
    ]

    def __init__(self, current_theme: str = "dark", config=None, event_bus=None, parent=None):
        super().__init__(parent)
        self._current_theme = current_theme
        self._config = config
        self._event_bus = event_bus
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 侧边栏 ──
        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(160)
        self._sidebar.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                color: #999;
                border: none;
                border-right: 1px solid #2a2a2a;
                outline: none;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 16px;
            }
            QListWidget::item:selected {
                background-color: rgba(160,160,160,0.1);
                color: #a0a0a0;
                border-left: 2px solid #a0a0a0;
            }
            QListWidget::item:hover {
                background-color: rgba(255,255,255,0.05);
                color: #e8e8e8;
            }
        """)
        for label, _key in self.SIDEBAR_ITEMS:
            self._sidebar.addItem(label)
        self._sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        layout.addWidget(self._sidebar)

        # ── 内容区（Stacked）──
        from PyQt5.QtWidgets import QStackedWidget
        self._stack = QStackedWidget()

        self._stack.addWidget(self._create_general_page())
        self._stack.addWidget(self._create_appearance_page())
        self._stack.addWidget(self._create_notifications_page())

        layout.addWidget(self._stack, 1)

        # 默认选中第一项
        self._sidebar.setCurrentRow(0)

    def _on_sidebar_changed(self, index):
        """侧边栏切换页面"""
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)

    # ── 通用设置页面 ─────────────────────────────────────────

    def _create_general_page(self) -> QWidget:
        """通用设置：基本设置 + 悬浮窗 + 数据管理"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ── 基本设置组 ──
        layout.addWidget(self._group_title("基本设置"))

        self._autostart_toggle = self._create_toggle(
            self._is_autostart_enabled() if self._config else False)
        layout.addWidget(self._setting_row(
            "开机自启动", "Windows 启动时自动运行", self._autostart_toggle))

        self._minimize_toggle = self._create_toggle(
            self._config.get("minimize_to_tray", True) if self._config else True)
        layout.addWidget(self._setting_row(
            "关闭时最小化到托盘", "点击关闭按钮时隐藏到系统托盘", self._minimize_toggle))

        self._topmost_toggle = self._create_toggle(
            self._config.is_always_on_top() if self._config else True)
        layout.addWidget(self._setting_row(
            "窗口置顶", "悬浮窗和桌宠始终显示在最前面", self._topmost_toggle))

        # ── 悬浮窗组 ──
        layout.addWidget(self._group_title("悬浮窗"))

        opacity_val = int(self._config.get("opacity", 0.9) * 100) if self._config else 90
        self._opacity_label = QLabel(f"{opacity_val}%")
        self._opacity_label.setStyleSheet("color: #d97706; font-size: 13px;")
        layout.addWidget(self._setting_row(
            "透明度", "调整悬浮窗的不透明度", self._opacity_label))

        self._idle_toggle = self._create_toggle(
            self._config.get("idle_detection", True) if self._config else True)
        layout.addWidget(self._setting_row(
            "空闲检测", "无操作超过 5 分钟暂停统计", self._idle_toggle))

        # ── 数据管理组 ──
        layout.addWidget(self._group_title("数据管理"))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        csv_btn = QPushButton("导出 CSV")
        csv_btn.clicked.connect(self._on_export_csv)
        json_btn = QPushButton("导出 JSON")
        json_btn.clicked.connect(self._on_export_json)
        about_btn = QPushButton("关于")
        about_btn.clicked.connect(self._on_about)
        btn_row.addWidget(csv_btn)
        btn_row.addWidget(json_btn)
        btn_row.addWidget(about_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()
        return page

    # ── 外观页面 ─────────────────────────────────────────────

    def _create_appearance_page(self) -> QWidget:
        """外观设置：主题选择"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        layout.addWidget(self._group_title("主题模式"))

        hint = QLabel("选择气泡的显示主题。")
        hint.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(hint)

        from PyQt5.QtWidgets import QComboBox
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("暗色模式", "dark")
        self.theme_combo.addItem("亮色模式", "light")
        if self._current_theme == "light":
            self.theme_combo.setCurrentIndex(1)
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #1a1a1a; color: white;
                border: 1px solid #2a2a2a; padding: 6px 10px;
                border-radius: 4px; min-width: 200px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a; color: white;
                selection-background-color: #252525;
            }
        """)
        layout.addWidget(self.theme_combo)

        layout.addStretch()
        return page

    # ── 通知页面 ─────────────────────────────────────────────

    def _create_notifications_page(self) -> QWidget:
        """通知设置（预留）"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 16, 20, 16)

        placeholder = QLabel("通知功能开发中...")
        placeholder.setStyleSheet("color: #666; font-size: 13px;")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)

        return page

    # ── UI 组件工厂 ──────────────────────────────────────────

    def _group_title(self, text: str) -> QLabel:
        """创建分组标题"""
        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #e8e8e8;"
            "padding: 12px 0 8px 0; border-bottom: 1px solid #2a2a2a;")
        return label

    def _create_toggle(self, checked: bool = False):
        """创建 toggle 开关（自绘圆形滑块）"""
        return ToggleSwitch(checked=checked)

    def _setting_row(self, label_text: str, desc_text: str, widget) -> QWidget:
        """创建一行设置项：左侧标签+描述，右侧控件"""
        row = QWidget()
        row.setMinimumHeight(56)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 8, 0, 8)

        left = QVBoxLayout()
        left.setSpacing(4)
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 13px; color: #e8e8e8;")
        desc = QLabel(desc_text)
        desc.setStyleSheet("font-size: 11px; color: #666;")
        left.addWidget(label)
        left.addWidget(desc)

        layout.addLayout(left, 1)
        layout.addWidget(widget, 0, Qt.AlignRight | Qt.AlignVCenter)
        return row

    # ── 功能回调 ─────────────────────────────────────────────

    def _is_autostart_enabled(self) -> bool:
        """检查是否已启用开机自启动"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "WindowStatus")
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def _on_export_csv(self):
        """导出 CSV"""
        if self._event_bus:
            self._event_bus.emit("export.csv")

    def _on_export_json(self):
        """导出 JSON"""
        if self._event_bus:
            self._event_bus.emit("export.json")

    def _on_about(self):
        """显示关于"""
        from kernel.event_bus import Events
        if self._event_bus:
            self._event_bus.emit(Events.SHOW_ABOUT)

    def get_theme(self) -> str:
        return self.theme_combo.currentData()


# ============================================================
# 设置主窗口
# ============================================================

class SettingsDialog(FramelessDialog):
    """
    设置窗口

    标签页：
    1. 通用 — 基本设置、悬浮窗、数据管理
    2. 分类规则 — 增删改分类和匹配规则
    3. 插件管理 — 启用/禁用插件
    """

    def __init__(self, categories: Dict[str, dict],
                 plugins_info: Optional[List[dict]] = None,
                 current_theme: str = "dark",
                 config=None,
                 event_bus=None,
                 parent=None):
        super().__init__(title="WindowStatus 设置", parent=parent)
        self.setFixedSize(720, 580)
        self.setStyleSheet(DIALOG_STYLESHEET)

        self._on_save_callback: Optional[Callable] = None
        self._config = config
        self._event_bus = event_bus

        # 使用 FramelessDialog 的 content_layout
        layout = self.content_layout
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(10)

        # 标签页
        tabs = QTabWidget()
        tabs.setTabBar(CustomTabBar())

        self.general_tab = GeneralTab(current_theme, config=self._config, event_bus=self._event_bus)
        tabs.addTab(self.general_tab, "通用")

        self.categories_tab = CategoriesTab(categories)
        tabs.addTab(self.categories_tab, "分类规则")

        if plugins_info:
            self.plugins_tab = PluginsTab(plugins_info)
            tabs.addTab(self.plugins_tab, "插件管理")
        else:
            self.plugins_tab = None

        layout.addWidget(tabs, 1)

        # 底部按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(cancel_btn)
        layout.addLayout(bottom_layout)

    def set_on_save(self, callback: Callable):
        """设置保存回调"""
        self._on_save_callback = callback

    def _on_save(self):
        result = {
            "categories": self.categories_tab.get_categories(),
            "plugins": self.plugins_tab.get_plugins_config() if self.plugins_tab else None,
            "theme": self.general_tab.get_theme()
        }
        if self._on_save_callback:
            self._on_save_callback(result)
        self.accept()
