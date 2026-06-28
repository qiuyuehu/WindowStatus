# WindowStatus 重构方案

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

## 前置条件（发给分身/CC 时必须写）

- 身份：你是 work profile 的衾衾，负责代码审查和方案设计
- 项目路径：`C:\Users\秋月\Desktop\WindowStatus`
- WSL 路径：`/mnt/c/Users/秋月/Desktop/WindowStatus`
- 代码规范：Python 3、PyQt5、变量用 snake_case、函数用 snake_case、注释用中文
- 测试运行：`python3 harness/checks.py && python3 -m pytest tests/ -v`
- 开工前必读：`SPEC.md` → `harness/SPEC.md` → `harness/CONSTRAINTS.md` → `harness/DECISIONS.md`
- 禁止事项：不改 main.py 入口逻辑、不改插件加载顺序、不删已有功能

**Goal:** 全量重构 WindowStatus，统一弹窗样式、清理代码、补全覆盖测试、更新文档

**Architecture:** 保持现有插件化架构（kernel + plugins），不改变模块职责和通信方式

**Tech Stack:** Python 3 + PyQt5 + pytest

---

## 阶段概览

| 阶段 | 内容 | 预计任务数 |
|------|------|-----------|
| P1 | 弹窗样式统一（oklch 配色 + 通用组件） | 8 |
| P2 | 代码清理（空 catch 块、魔法数字、重复代码） | 6 |
| P3 | 测试全覆盖（12 个模块） | 12 |
| P4 | 文档更新（SPEC、DECISIONS、devlog） | 3 |

---

## P1：弹窗样式统一

### Task 1.1：提取通用样式变量

**Objective:** 创建通用样式模块，统一配色、字体、间距

**Files:**
- Create: `plugins/common_styles.py`

**完成标准：**
- [ ] 定义 oklch 配色系统（主色、强调色、中性色）
- [ ] 定义字体规范（标题、正文、小字）
- [ ] 定义间距规范（xs、sm、md、lg、xl）
- [ ] 定义按钮样式（主按钮、次按钮、危险按钮）
- [ ] 定义卡片样式（背景、边框、圆角）

**Step 1: 创建通用样式模块**

```python
# plugins/common_styles.py
# -*- coding: utf-8 -*-
"""
通用样式模块 - 统一弹窗配色和组件样式
"""

from PyQt5.QtGui import QColor

# ============================================================
# oklch 配色系统
# ============================================================

# 转换 oklch 到 QColor 的辅助函数
def oklch_to_qcolor(l, c, h):
    """将 oklch 颜色转换为 QColor（简化版，使用 HSL 近似）"""
    import colorsys
    # oklch 到 HSL 的近似映射
    h_norm = h / 360.0
    s = min(1.0, c * 2)
    l_norm = l
    r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s)
    return QColor(int(r * 255), int(g * 255), int(b * 255))

# 主色调（琥珀）
COLOR_PRIMARY = oklch_to_qcolor(0.75, 0.15, 70)  # 琥珀强调
COLOR_PRIMARY_HOVER = oklch_to_qcolor(0.65, 0.15, 70)
COLOR_PRIMARY_PRESSED = oklch_to_qcolor(0.55, 0.15, 70)

# 中性色
COLOR_BG_PRIMARY = QColor(18, 18, 18)  # #121212 深色底
COLOR_BG_SECONDARY = QColor(26, 26, 26)  # #1a1a1a 卡片背景
COLOR_BG_TERTIARY = QColor(36, 36, 36)  # #242424 悬停背景

COLOR_TEXT_PRIMARY = QColor(232, 232, 232)  # #e8e8e8 主文字
COLOR_TEXT_SECONDARY = QColor(153, 153, 153)  # #999 次要文字
COLOR_TEXT_MUTED = QColor(102, 102, 102)  # #666 弱化文字

COLOR_BORDER = QColor(42, 42, 42)  # #2a2a2a 边框
COLOR_BORDER_SUBTLE = QColor(30, 30, 30)  # #1e1e1e 细边框

# 状态色
COLOR_SUCCESS = oklch_to_qcolor(0.7, 0.15, 145)  # 绿色
COLOR_WARNING = oklch_to_qcolor(0.75, 0.15, 70)  # 黄色
COLOR_ERROR = oklch_to_qcolor(0.6, 0.2, 25)  # 红色

# ============================================================
# 字体规范
# ============================================================

FONT_FAMILY = "Microsoft YaHei, PingFang SC, sans-serif"

FONT_SIZE_TITLE = 16
FONT_SIZE_SUBTITLE = 14
FONT_SIZE_BODY = 13
FONT_SIZE_CAPTION = 11

FONT_WEIGHT_NORMAL = "normal"
FONT_WEIGHT_BOLD = "bold"

# ============================================================
# 间距规范
# ============================================================

SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
SPACING_XL = 32

# ============================================================
# 圆角规范
# ============================================================

RADIUS_SM = 4
RADIUS_MD = 8
RADIUS_LG = 12
RADIUS_XL = 16

# ============================================================
# 通用样式表
# ============================================================

DIALOG_BASE_STYLE = f"""
QDialog {{
    background-color: {COLOR_BG_PRIMARY.name()};
    color: {COLOR_TEXT_PRIMARY.name()};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_BODY}px;
}}
"""

BUTTON_PRIMARY_STYLE = f"""
QPushButton#primary {{
    background-color: {COLOR_PRIMARY.name()};
    color: white;
    border: none;
    padding: {SPACING_SM}px {SPACING_MD}px;
    border-radius: {RADIUS_SM}px;
    font-size: {FONT_SIZE_BODY}px;
    min-width: 80px;
}}
QPushButton#primary:hover {{
    background-color: {COLOR_PRIMARY_HOVER.name()};
}}
QPushButton#primary:pressed {{
    background-color: {COLOR_PRIMARY_PRESSED.name()};
}}
"""

BUTTON_SECONDARY_STYLE = f"""
QPushButton {{
    background-color: {COLOR_BG_SECONDARY.name()};
    color: {COLOR_TEXT_PRIMARY.name()};
    border: 1px solid {COLOR_BORDER.name()};
    padding: {SPACING_SM}px {SPACING_MD}px;
    border-radius: {RADIUS_SM}px;
    font-size: {FONT_SIZE_BODY}px;
    min-width: 80px;
}}
QPushButton:hover {{
    background-color: {COLOR_BG_TERTIARY.name()};
}}
"""

CARD_STYLE = f"""
QWidget#card {{
    background-color: {COLOR_BG_SECONDARY.name()};
    border: 1px solid {COLOR_BORDER.name()};
    border-radius: {RADIUS_LG}px;
}}
"""

# ============================================================
# 通用组件
# ============================================================

def create_title_label(text):
    """创建标题标签"""
    from PyQt5.QtWidgets import QLabel
    label = QLabel(text)
    label.setStyleSheet(f"""
        font-size: {FONT_SIZE_TITLE}px;
        font-weight: {FONT_WEIGHT_BOLD};
        color: {COLOR_TEXT_PRIMARY.name()};
    """)
    return label

def create_body_label(text):
    """创建正文标签"""
    from PyQt5.QtWidgets import QLabel
    label = QLabel(text)
    label.setStyleSheet(f"""
        font-size: {FONT_SIZE_BODY}px;
        color: {COLOR_TEXT_PRIMARY.name()};
    """)
    return label

def create_caption_label(text):
    """创建说明标签"""
    from PyQt5.QtWidgets import QLabel
    label = QLabel(text)
    label.setStyleSheet(f"""
        font-size: {FONT_SIZE_CAPTION}px;
        color: {COLOR_TEXT_SECONDARY.name()};
    """)
    return label

def create_primary_button(text):
    """创建主按钮"""
    from PyQt5.QtWidgets import QPushButton
    btn = QPushButton(text)
    btn.setObjectName("primary")
    btn.setStyleSheet(BUTTON_PRIMARY_STYLE)
    return btn

def create_secondary_button(text):
    """创建次按钮"""
    from PyQt5.QtWidgets import QPushButton
    btn = QPushButton(text)
    btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
    return btn

def create_separator():
    """创建分隔线"""
    from PyQt5.QtWidgets import QFrame
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet(f"background-color: {COLOR_BORDER.name()};")
    return line
```

**Step 2: 验证语法**

Run: `python3 -m py_compile plugins/common_styles.py`
Expected: 无输出（语法正确）

**Step 3: Commit**

```bash
git add plugins/common_styles.py
git commit -m "feat: 添加通用样式模块（oklch 配色系统）"
```

---

### Task 1.2：统计弹窗应用通用样式

**Objective:** 统计弹窗使用 common_styles 的配色和组件

**Files:**
- Modify: `plugins/stats/dialog.py`

**完成标准：**
- [ ] 导入 common_styles 模块
- [ ] 标题栏使用 COLOR_BG_PRIMARY
- [ ] 卡片使用 COLOR_BG_SECONDARY
- [ ] 文字使用 COLOR_TEXT_PRIMARY / COLOR_TEXT_SECONDARY
- [ ] 按钮使用 create_primary_button / create_secondary_button
- [ ] 分隔线使用 COLOR_BORDER
- [ ] 环形图使用 oklch 配色

**Step 1: 修改 imports**

在 `plugins/stats/dialog.py` 顶部添加：
```python
from plugins.common_styles import (
    COLOR_BG_PRIMARY, COLOR_BG_SECONDARY, COLOR_BG_TERTIARY,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_BORDER, COLOR_PRIMARY,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_CAPTION,
    SPACING_SM, SPACING_MD, SPACING_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    create_title_label, create_body_label, create_caption_label,
    create_primary_button, create_secondary_button, create_separator
)
```

**Step 2: 更新 STYLESHEET**

将硬编码的颜色值替换为 common_styles 的常量。

**Step 3: 更新组件创建**

将手动创建的 QLabel、QPushButton 替换为 create_xxx 函数。

**Step 4: 验证语法**

Run: `python3 -m py_compile plugins/stats/dialog.py`
Expected: 无输出

**Step 5: Commit**

```bash
git add plugins/stats/dialog.py
git commit -m "refactor: 统计弹窗应用通用样式"
```

---

### Task 1.3：设置弹窗应用通用样式

**Objective:** 设置弹窗使用 common_styles 的配色和组件

**Files:**
- Modify: `plugins/settings/dialog.py`

**完成标准：**
- [ ] 导入 common_styles 模块
- [ ] 标题栏使用 COLOR_BG_PRIMARY
- [ ] 侧边栏使用 COLOR_BG_SECONDARY
- [ ] 按钮使用 create_primary_button / create_secondary_button
- [ ] ToggleSwitch 使用 COLOR_PRIMARY
- [ ] 文字大小统一（标题 16px、正文 13px、说明 11px）

**Step 1-5:** 同 Task 1.2 的流程

---

### Task 1.4：关于弹窗应用通用样式

**Objective:** 关于弹窗使用 common_styles 的配色和组件

**Files:**
- Modify: `plugins/about/plugin.py`

**完成标准：**
- [ ] 导入 common_styles 模块
- [ ] 背景色使用 COLOR_BG_PRIMARY
- [ ] 强调色使用 COLOR_PRIMARY
- [ ] 文字颜色使用 COLOR_TEXT_PRIMARY / COLOR_TEXT_SECONDARY

**Step 1-5:** 同 Task 1.2 的流程

---

### Task 1.5：更新环形图配色

**Objective:** 统计弹窗的环形图使用 oklch 配色

**Files:**
- Modify: `plugins/stats/dialog.py`（DonutChart 类）

**完成标准：**
- [ ] 环形图颜色从硬编码 RGB 改为 oklch 生成
- [ ] 颜色数量足够（至少 8 种）
- [ ] 视觉效果与原版一致或更好

**Step 1: 更新 FALLBACK_COLORS**

```python
from plugins.common_styles import oklch_to_qcolor

class DonutChart(QWidget):
    # 备用颜色（oklch 生成）
    FALLBACK_COLORS = [
        oklch_to_qcolor(0.7, 0.15, 25),   # 红
        oklch_to_qcolor(0.7, 0.15, 70),   # 黄
        oklch_to_qcolor(0.7, 0.15, 145),  # 绿
        oklch_to_qcolor(0.7, 0.15, 230),  # 蓝
        oklch_to_qcolor(0.7, 0.15, 300),  # 紫
        oklch_to_qcolor(0.7, 0.15, 30),   # 橙
        oklch_to_qcolor(0.7, 0.15, 180),  # 青
        oklch_to_qcolor(0.7, 0.15, 340),  # 粉
    ]
```

**Step 2-4:** 验证、测试、Commit

---

### Task 1.6：更新进度条配色

**Objective:** 统计弹窗的进度条使用 oklch 配色

**Files:**
- Modify: `plugins/stats/dialog.py`（_ProgressBar 类）

**完成标准：**
- [ ] 进度条背景使用 COLOR_BG_TERTIARY
- [ ] 进度条填充使用 oklch 生成的颜色
- [ ] 视觉效果与原版一致或更好

---

### Task 1.7：更新 CategoryRow 配色

**Objective:** 统计弹窗的分类行使用 oklch 配色

**Files:**
- Modify: `plugins/stats/dialog.py`（CategoryRow 类）

**完成标准：**
- [ ] 分类名称使用 COLOR_TEXT_PRIMARY
- [ ] 时长使用 COLOR_TEXT_SECONDARY
- [ ] 百分比使用 COLOR_TEXT_SECONDARY
- [ ] 进度条使用 oklch 配色

---

### Task 1.8：验证 P1 效果

**Objective:** 确保所有弹窗样式统一，无视觉错误

**完成标准：**
- [ ] 语法检查通过：`python3 -m py_compile plugins/stats/dialog.py plugins/settings/dialog.py plugins/about/plugin.py`
- [ ] 约束检查通过：`python3 harness/checks.py`
- [ ] 手动测试：打开统计弹窗、设置弹窗、关于弹窗，确认样式一致

---

## P2：代码清理

### Task 2.1：清理空 catch 块

**Objective:** 所有空 except 块添加注释说明

**Files:**
- Modify: `main.py`（1 处）
- Modify: `kernel/event_bus.py`（1 处）
- Modify: `plugins/overlay/plugin.py`（2 处）
- Modify: `plugins/stats/plugin.py`（1 处）

**完成标准：**
- [ ] 所有空 except 块有注释说明为什么忽略
- [ ] 约束检查通过：`python3 harness/checks.py`

**Step 1: 查找空 catch 块**

Run: `grep -n "except.*:$" plugins/stats/plugin.py plugins/overlay/plugin.py kernel/event_bus.py main.py | head -20`

**Step 2: 逐个添加注释**

例如：
```python
# 原来
except Exception:
    pass

# 改为
except Exception:
    # 忽略：xxx 操作失败不影响主流程
    pass
```

**Step 3: 验证**

Run: `python3 harness/checks.py`
Expected: 0 violations

---

### Task 2.2：提取魔法数字

**Objective:** 将硬编码的数字提取为常量

**Files:**
- Modify: `plugins/overlay/plugin.py`（定时器间隔、透明度等）
- Modify: `plugins/desktop_pet/widget.py`（长按时间、定时器间隔等）
- Modify: `plugins/stats/plugin.py`（缓存大小、超时时间等）

**完成标准：**
- [ ] 所有魔法数字提取为模块级常量
- [ ] 常量有注释说明用途
- [ ] 逻辑行为不变

---

### Task 2.3：提取重复代码

**Objective:** 将重复的代码提取为公共方法

**Files:**
- Modify: `plugins/overlay/plugin.py`
- Modify: `plugins/desktop_pet/widget.py`

**完成标准：**
- [ ] 窗口状态保存逻辑提取为公共方法
- [ ] TOPMOST 维护逻辑提取为公共方法
- [ ] 逻辑行为不变

---

### Task 2.4：清理未使用的 import

**Objective:** 删除未使用的 import 语句

**Files:**
- 所有 .py 文件

**完成标准：**
- [ ] 无未使用的 import
- [ ] 语法检查通过

---

### Task 2.5：统一注释风格

**Objective:** 统一代码注释风格

**完成标准：**
- [ ] 函数有 docstring
- [ ] 关键逻辑有行内注释
- [ ] 注释语言统一为中文

---

### Task 2.6：验证 P2 效果

**Objective:** 确保代码清理无遗漏

**完成标准：**
- [ ] 约束检查通过：`python3 harness/checks.py`
- [ ] 语法检查通过：`python3 -m py_compile` 所有修改的文件
- [ ] 功能不变：打开统计、设置、关于弹窗，确认功能正常

---

## P3：测试全覆盖

### Task 3.1：统计插件测试

**Objective:** 覆盖统计插件的核心逻辑

**Files:**
- Create: `tests/test_stats.py`

**完成标准：**
- [ ] 测试 get_today_stats()
- [ ] 测试 get_week_stats()
- [ ] 测试 get_month_stats()
- [ ] 测试 get_yesterday_stats()
- [ ] 测试 get_last_week_stats()
- [ ] 测试 get_last_month_stats()
- [ ] 测试 _get_week_start()
- [ ] 测试 _aggregate_daily()
- [ ] 测试 _aggregate_weekly()
- [ ] 测试 _aggregate_monthly()
- [ ] 测试 log_activity()
- [ ] 测试 _record_current_activity()
- [ ] 所有测试通过

---

### Task 3.2：设置插件测试

**Objective:** 覆盖设置插件的核心逻辑

**Files:**
- Create: `tests/test_settings.py`

**完成标准：**
- [ ] 测试 _set_autostart()
- [ ] 测试 _on_save()（mock config）
- [ ] 测试 _get_plugins_info()
- [ ] 所有测试通过

---

### Task 3.3：窗口监控测试

**Objective:** 覆盖窗口监控插件的核心逻辑

**Files:**
- Create: `tests/test_monitor.py`

**完成标准：**
- [ ] 测试事件触发逻辑
- [ ] 测试空闲检测逻辑
- [ ] 测试 debounce 逻辑
- [ ] 所有测试通过

---

### Task 3.4：悬浮气泡测试

**Objective:** 覆盖悬浮气泡插件的核心逻辑

**Files:**
- Create: `tests/test_overlay.py`

**完成标准：**
- [ ] 测试主题切换逻辑
- [ ] 测试位置保存/恢复
- [ ] 测试置顶状态管理
- [ ] 所有测试通过

---

### Task 3.5：桌宠插件测试

**Objective:** 覆盖桌宠插件的核心逻辑

**Files:**
- Create: `tests/test_desktop_pet_plugin.py`

**完成标准：**
- [ ] 测试状态映射逻辑
- [ ] 测试拖拽状态管理
- [ ] 测试位置保存/恢复
- [ ] 所有测试通过

---

### Task 3.6：系统托盘测试

**Objective:** 覆盖系统托盘插件的核心逻辑

**Files:**
- Create: `tests/test_tray.py`

**完成标准：**
- [ ] 测试菜单创建逻辑
- [ ] 测试事件触发逻辑
- [ ] 所有测试通过

---

### Task 3.7：关于弹窗测试

**Objective:** 覆盖关于弹窗的核心逻辑

**Files:**
- Create: `tests/test_about.py`

**完成标准：**
- [ ] 测试弹窗创建
- [ ] 测试样式应用
- [ ] 所有测试通过

---

### Task 3.8：Kernel 测试

**Objective:** 覆盖 Kernel 类的核心逻辑

**Files:**
- Create: `tests/test_kernel.py`

**完成标准：**
- [ ] 测试 init()
- [ ] 测试 set_qt_app()
- [ ] 测试 start() / stop()
- [ ] 所有测试通过

---

### Task 3.9：PluginManager 测试

**Objective:** 覆盖插件管理器的核心逻辑

**Files:**
- Create: `tests/test_plugin_manager.py`

**完成标准：**
- [ ] 测试 discover_plugins()
- [ ] 测试 load_plugin()
- [ ] 测试 unload_plugin()
- [ ] 测试拓扑排序
- [ ] 所有测试通过

---

### Task 3.10：主窗口测试

**Objective:** 覆盖主窗口的核心逻辑

**Files:**
- Create: `tests/test_main_window.py`

**完成标准：**
- [ ] 测试窗口创建
- [ ] 测试最小化到托盘
- [ ] 测试关闭逻辑
- [ ] 所有测试通过

---

### Task 3.11：通用样式测试

**Objective:** 覆盖 common_styles 模块

**Files:**
- Create: `tests/test_common_styles.py`

**完成标准：**
- [ ] 测试 oklch_to_qcolor()
- [ ] 测试颜色常量非空
- [ ] 测试组件创建函数
- [ ] 所有测试通过

---

### Task 3.12：验证 P3 效果

**Objective:** 确保所有测试通过

**完成标准：**
- [ ] 约束检查通过：`python3 harness/checks.py`
- [ ] 所有测试通过：`python3 -m pytest tests/ -v`
- [ ] 测试覆盖率：核心逻辑 100%

---

## P4：文档更新

### Task 4.1：更新 SPEC.md

**Objective:** 更新项目规格文档

**Files:**
- Modify: `SPEC.md`

**完成标准：**
- [ ] 更新版本号（v3.4.0 → v3.5.0）
- [ ] 更新设计系统（oklch 配色）
- [ ] 更新测试覆盖说明
- [ ] 更新技术债务状态

---

### Task 4.2：更新 DECISIONS.md

**Objective:** 记录本次重构的决策

**Files:**
- Modify: `harness/DECISIONS.md`

**完成标准：**
- [ ] 添加 D-008: oklch 配色系统
- [ ] 添加 D-009: 弹窗样式统一
- [ ] 添加 D-010: 测试全覆盖

---

### Task 4.3：创建 devlog

**Objective:** 记录本次重构的开发日志

**Files:**
- Create: `~/.hermes/docs/logs/WindowStatus-refactor-20260628.md`

**完成标准：**
- [ ] 记录重构目标
- [ ] 记录每个阶段的改动
- [ ] 记录踩坑和解决方案
- [ ] 记录测试结果

---

## 验收标准

1. `python3 harness/checks.py` 约束检查 0 违规
2. `python3 -m pytest tests/ -v` 所有测试通过
3. 语法检查通过：`python3 -m py_compile` 所有 .py 文件
4. 弹窗样式统一（oklch 配色 + 通用组件）
5. 代码无空 catch 块（都有注释）
6. 无魔法数字（都提取为常量）
7. SPEC.md / DECISIONS.md 已更新

## 手动测试（主人执行）

1. 打开统计弹窗 → 确认样式统一
2. 打开设置弹窗 → 确认样式统一
3. 打开关于弹窗 → 确认样式统一
4. 切换亮色/暗色主题 → 确认颜色跟随
5. 打开/关闭桌宠 → 确认功能正常
6. 刷新游戏 → 确认重启正常

---

*编写时间：2026-06-28*
*预计完成时间：1 天*
*阶段数：4*
*任务数：29*
