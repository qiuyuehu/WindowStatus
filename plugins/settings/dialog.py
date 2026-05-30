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


# ============================================================
# 共享样式
# ============================================================

DIALOG_STYLESHEET = """
    QDialog {
        background-color: #1a1a2e;
        color: white;
    }
    QListWidget {
        background-color: #16213e;
        color: white;
        border: 1px solid #0f3460;
        outline: none;
    }
    QListWidget::item {
        padding: 6px 10px;
    }
    QListWidget::item:selected {
        background-color: #0f3460;
    }
    QListWidget::item:hover {
        background-color: #1a3a6e;
    }
    QTableWidget {
        background-color: #16213e;
        color: white;
        border: 1px solid #0f3460;
        gridline-color: #1a1a2e;
    }
    QHeaderView::section {
        background-color: #0f3460;
        color: white;
        padding: 5px;
        border: none;
    }
    QTabWidget::pane {
        border: 1px solid #16213e;
        background-color: #1a1a2e;
    }
    QTabBar::tab {
        background-color: #16213e;
        color: white;
        padding: 8px 20px;
        border: 1px solid #0f3460;
        border-bottom: none;
        min-width: 80px;
    }
    QTabBar::tab:selected {
        background-color: #0f3460;
    }
    QPushButton {
        background-color: #0f3460;
        color: white;
        border: none;
        padding: 6px 14px;
        border-radius: 4px;
        min-width: 60px;
    }
    QPushButton:hover {
        background-color: #1a4a8a;
    }
    QPushButton:disabled {
        background-color: #2a2a4a;
        color: #666;
    }
    QCheckBox {
        color: white;
        spacing: 6px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
    }
    QCheckBox::indicator:unchecked {
        background-color: #16213e;
        border: 1px solid #0f3460;
        border-radius: 3px;
    }
    QCheckBox::indicator:checked {
        background-color: #4ECDC4;
        border: 1px solid #4ECDC4;
        border-radius: 3px;
    }
    QLabel {
        color: #b8b8b8;
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
            # 复选框
            checkbox = QCheckBox()
            checkbox.setChecked(plugin["enabled"])
            checkbox.stateChanged.connect(lambda state, r=row: self._on_toggle(r, state))
            self.table.setCellWidget(row, 0, checkbox)

            # 插件名
            name_item = QTableWidgetItem(plugin["name"])
            name_item.setFont(QFont("Consolas", 10))
            self.table.setItem(row, 1, name_item)

            # 说明
            desc_item = QTableWidgetItem(plugin.get("description", ""))
            self.table.setItem(row, 2, desc_item)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def _on_toggle(self, row: int, state: int):
        self._plugins[row]["enabled"] = (state == Qt.Checked)

    def get_plugins_config(self) -> Dict[str, bool]:
        """获取插件启用/禁用配置"""
        return {p["name"]: p["enabled"] for p in self._plugins}


# ============================================================
# 通用设置标签页
# ============================================================

class GeneralTab(QWidget):
    """通用设置标签页（主题等）"""

    THEMES = [
        ("dark", "暗色模式"),
        ("light", "亮色模式"),
    ]

    def __init__(self, current_theme: str = "dark", parent=None):
        super().__init__(parent)
        self._current_theme = current_theme
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(16)

        # 主题模式
        theme_group_label = QLabel("主题模式")
        theme_group_label.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        layout.addWidget(theme_group_label)

        theme_hint = QLabel("选择气泡的显示主题。")
        theme_hint.setWordWrap(True)
        theme_hint.setStyleSheet("color: #808080; font-size: 12px;")
        layout.addWidget(theme_hint)

        self.theme_combo = QComboBox()
        for value, label in self.THEMES:
            self.theme_combo.addItem(label, value)
            if value == self._current_theme:
                self.theme_combo.setCurrentIndex(self.theme_combo.count() - 1)
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #16213e;
                color: white;
                border: 1px solid #0f3460;
                padding: 6px 10px;
                border-radius: 4px;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #16213e;
                color: white;
                selection-background-color: #0f3460;
            }
        """)
        layout.addWidget(self.theme_combo)

        layout.addStretch()
        self.setLayout(layout)

    def get_theme(self) -> str:
        return self.theme_combo.currentData()


# ============================================================
# 设置主窗口
# ============================================================

class SettingsDialog(QDialog):
    """
    设置窗口

    标签页：
    1. 分类规则 — 增删改分类和匹配规则
    2. 插件管理 — 启用/禁用插件
    """

    def __init__(self, categories: Dict[str, dict],
                 plugins_info: Optional[List[dict]] = None,
                 current_theme: str = "dark",
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("WindowStatus 设置")
        self.setMinimumSize(720, 520)
        self.setStyleSheet(DIALOG_STYLESHEET)

        self._on_save_callback: Optional[Callable] = None

        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 标题
        title = QLabel("WindowStatus 设置")
        title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # 标签页
        tabs = QTabWidget()

        self.general_tab = GeneralTab(current_theme)
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
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4ECDC4;
                color: #1a1a2e;
                font-weight: bold;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background-color: #5EDDD4;
            }
        """)
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(cancel_btn)
        layout.addLayout(bottom_layout)

        self.setLayout(layout)

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
