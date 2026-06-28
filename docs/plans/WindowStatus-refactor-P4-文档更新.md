

## 阶段：P4 - 文档更新

**目标**：更新 SPEC.md、DECISIONS.md、创建 devlog

**任务数**：3

---

     1|# WindowStatus 重构方案
     2|
     3|> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
     4|
     5|## 前置条件（发给分身/CC 时必须写）
     6|
     7|- 身份：你是 work profile 的衾衾，负责代码审查和方案设计
     8|- 项目路径：`C:\Users\秋月\Desktop\WindowStatus`
     9|- WSL 路径：`/mnt/c/Users/秋月/Desktop/WindowStatus`
    10|- 代码规范：Python 3、PyQt5、变量用 snake_case、函数用 snake_case、注释用中文
    11|- 测试运行：`python3 harness/checks.py && python3 -m pytest tests/ -v`
    12|- 开工前必读：`SPEC.md` → `harness/SPEC.md` → `harness/CONSTRAINTS.md` → `harness/DECISIONS.md`
    13|- 禁止事项：不改 main.py 入口逻辑、不改插件加载顺序、不删已有功能
    14|
    15|**Goal:** 全量重构 WindowStatus，统一弹窗样式、清理代码、补全覆盖测试、更新文档
    16|
    17|**Architecture:** 保持现有插件化架构（kernel + plugins），不改变模块职责和通信方式
    18|
    19|**Tech Stack:** Python 3 + PyQt5 + pytest
    20|
    21|---
    22|
    23|## 阶段概览
    24|
    25|| 阶段 | 内容 | 预计任务数 |
    26||------|------|-----------|
    27|| P1 | 弹窗样式统一（oklch 配色 + 通用组件） | 8 |
    28|| P2 | 代码清理（空 catch 块、魔法数字、重复代码） | 6 |
    29|| P3 | 测试全覆盖（12 个模块） | 12 |
    30|| P4 | 文档更新（SPEC、DECISIONS、devlog） | 3 |
    31|
    32|---
    33|
    34|## P1：弹窗样式统一
    35|
    36|### Task 1.1：提取通用样式变量
    37|
    38|**Objective:** 创建通用样式模块，统一配色、字体、间距
    39|
    40|**Files:**
    41|- Create: `plugins/common_styles.py`
    42|
    43|**完成标准：**
    44|- [ ] 定义 oklch 配色系统（主色、强调色、中性色）
    45|- [ ] 定义字体规范（标题、正文、小字）
    46|- [ ] 定义间距规范（xs、sm、md、lg、xl）
    47|- [ ] 定义按钮样式（主按钮、次按钮、危险按钮）
    48|- [ ] 定义卡片样式（背景、边框、圆角）
    49|
    50|**Step 1: 创建通用样式模块**
    51|
    52|```python
    53|# plugins/common_styles.py
    54|# -*- coding: utf-8 -*-
    55|"""
    56|通用样式模块 - 统一弹窗配色和组件样式
    57|"""
    58|
    59|from PyQt5.QtGui import QColor
    60|
    61|# ============================================================
    62|# oklch 配色系统
    63|# ============================================================
    64|
    65|# 转换 oklch 到 QColor 的辅助函数
    66|def oklch_to_qcolor(l, c, h):
    67|    """将 oklch 颜色转换为 QColor（简化版，使用 HSL 近似）"""
    68|    import colorsys
    69|    # oklch 到 HSL 的近似映射
    70|    h_norm = h / 360.0
    71|    s = min(1.0, c * 2)
    72|    l_norm = l
    73|    r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s)
    74|    return QColor(int(r * 255), int(g * 255), int(b * 255))
    75|
    76|# 主色调（琥珀）
    77|COLOR_PRIMARY = oklch_to_qcolor(0.75, 0.15, 70)  # 琥珀强调
    78|COLOR_PRIMARY_HOVER = oklch_to_qcolor(0.65, 0.15, 70)
    79|COLOR_PRIMARY_PRESSED = oklch_to_qcolor(0.55, 0.15, 70)
    80|
    81|# 中性色
    82|COLOR_BG_PRIMARY = QColor(18, 18, 18)  # #121212 深色底
    83|COLOR_BG_SECONDARY = QColor(26, 26, 26)  # #1a1a1a 卡片背景
    84|COLOR_BG_TERTIARY = QColor(36, 36, 36)  # #242424 悬停背景
    85|
    86|COLOR_TEXT_PRIMARY = QColor(232, 232, 232)  # #e8e8e8 主文字
    87|COLOR_TEXT_SECONDARY = QColor(153, 153, 153)  # #999 次要文字
    88|COLOR_TEXT_MUTED = QColor(102, 102, 102)  # #666 弱化文字
    89|
    90|COLOR_BORDER = QColor(42, 42, 42)  # #2a2a2a 边框
    91|COLOR_BORDER_SUBTLE = QColor(30, 30, 30)  # #1e1e1e 细边框
    92|
    93|# 状态色
    94|COLOR_SUCCESS = oklch_to_qcolor(0.7, 0.15, 145)  # 绿色
    95|COLOR_WARNING = oklch_to_qcolor(0.75, 0.15, 70)  # 黄色
    96|COLOR_ERROR = oklch_to_qcolor(0.6, 0.2, 25)  # 红色
    97|
    98|# ============================================================
    99|# 字体规范
   100|# ============================================================
   101|
   102|FONT_FAMILY = "Microsoft YaHei, PingFang SC, sans-serif"
   103|
   104|FONT_SIZE_TITLE = 16
   105|FONT_SIZE_SUBTITLE = 14
   106|FONT_SIZE_BODY = 13
   107|FONT_SIZE_CAPTION = 11
   108|
   109|FONT_WEIGHT_NORMAL = "normal"
   110|FONT_WEIGHT_BOLD = "bold"
   111|
   112|# ============================================================
   113|# 间距规范
   114|# ============================================================
   115|
   116|SPACING_XS = 4
   117|SPACING_SM = 8
   118|SPACING_MD = 16
   119|SPACING_LG = 24
   120|SPACING_XL = 32
   121|
   122|# ============================================================
   123|# 圆角规范
   124|# ============================================================
   125|
   126|RADIUS_SM = 4
   127|RADIUS_MD = 8
   128|RADIUS_LG = 12
   129|RADIUS_XL = 16
   130|
   131|# ============================================================
   132|# 通用样式表
   133|# ============================================================
   134|
   135|DIALOG_BASE_STYLE = f"""
   136|QDialog {{
   137|    background-color: {COLOR_BG_PRIMARY.name()};
   138|    color: {COLOR_TEXT_PRIMARY.name()};
   139|    font-family: {FONT_FAMILY};
   140|    font-size: {FONT_SIZE_BODY}px;
   141|}}
   142|"""
   143|
   144|BUTTON_PRIMARY_STYLE = f"""
   145|QPushButton#primary {{
   146|    background-color: {COLOR_PRIMARY.name()};
   147|    color: white;
   148|    border: none;
   149|    padding: {SPACING_SM}px {SPACING_MD}px;
   150|    border-radius: {RADIUS_SM}px;
   151|    font-size: {FONT_SIZE_BODY}px;
   152|    min-width: 80px;
   153|}}
   154|QPushButton#primary:hover {{
   155|    background-color: {COLOR_PRIMARY_HOVER.name()};
   156|}}
   157|QPushButton#primary:pressed {{
   158|    background-color: {COLOR_PRIMARY_PRESSED.name()};
   159|}}
   160|"""
   161|
   162|BUTTON_SECONDARY_STYLE = f"""
   163|QPushButton {{
   164|    background-color: {COLOR_BG_SECONDARY.name()};
   165|    color: {COLOR_TEXT_PRIMARY.name()};
   166|    border: 1px solid {COLOR_BORDER.name()};
   167|    padding: {SPACING_SM}px {SPACING_MD}px;
   168|    border-radius: {RADIUS_SM}px;
   169|    font-size: {FONT_SIZE_BODY}px;
   170|    min-width: 80px;
   171|}}
   172|QPushButton:hover {{
   173|    background-color: {COLOR_BG_TERTIARY.name()};
   174|}}
   175|"""
   176|
   177|CARD_STYLE = f"""
   178|QWidget#card {{
   179|    background-color: {COLOR_BG_SECONDARY.name()};
   180|    border: 1px solid {COLOR_BORDER.name()};
   181|    border-radius: {RADIUS_LG}px;
   182|}}
   183|"""
   184|
   185|# ============================================================
   186|# 通用组件
   187|# ============================================================
   188|
   189|def create_title_label(text):
   190|    """创建标题标签"""
   191|    from PyQt5.QtWidgets import QLabel
   192|    label = QLabel(text)
   193|    label.setStyleSheet(f"""
   194|        font-size: {FONT_SIZE_TITLE}px;
   195|        font-weight: {FONT_WEIGHT_BOLD};
   196|        color: {COLOR_TEXT_PRIMARY.name()};
   197|    """)
   198|    return label
   199|
   200|def create_body_label(text):
   201|    """创建正文标签"""
   202|    from PyQt5.QtWidgets import QLabel
   203|    label = QLabel(text)
   204|    label.setStyleSheet(f"""
   205|        font-size: {FONT_SIZE_BODY}px;
   206|        color: {COLOR_TEXT_PRIMARY.name()};
   207|    """)
   208|    return label
   209|
   210|def create_caption_label(text):
   211|    """创建说明标签"""
   212|    from PyQt5.QtWidgets import QLabel
   213|    label = QLabel(text)
   214|    label.setStyleSheet(f"""
   215|        font-size: {FONT_SIZE_CAPTION}px;
   216|        color: {COLOR_TEXT_SECONDARY.name()};
   217|    """)
   218|    return label
   219|
   220|def create_primary_button(text):
   221|    """创建主按钮"""
   222|    from PyQt5.QtWidgets import QPushButton
   223|    btn = QPushButton(text)
   224|    btn.setObjectName("primary")
   225|    btn.setStyleSheet(BUTTON_PRIMARY_STYLE)
   226|    return btn
   227|
   228|def create_secondary_button(text):
   229|    """创建次按钮"""
   230|    from PyQt5.QtWidgets import QPushButton
   231|    btn = QPushButton(text)
   232|    btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
   233|    return btn
   234|
   235|def create_separator():
   236|    """创建分隔线"""
   237|    from PyQt5.QtWidgets import QFrame
   238|    line = QFrame()
   239|    line.setFrameShape(QFrame.HLine)
   240|    line.setFrameShadow(QFrame.Sunken)
   241|    line.setStyleSheet(f"background-color: {COLOR_BORDER.name()};")
   242|    return line
   243|```
   244|
   245|**Step 2: 验证语法**
   246|
   247|Run: `python3 -m py_compile plugins/common_styles.py`
   248|Expected: 无输出（语法正确）
   249|
   250|**Step 3: Commit**
   251|
   252|```bash
   253|git add plugins/common_styles.py
   254|git commit -m "feat: 添加通用样式模块（oklch 配色系统）"
   255|```
   256|
   257|---
   258|
   259|### Task 1.2：统计弹窗应用通用样式
   260|
   261|**Objective:** 统计弹窗使用 common_styles 的配色和组件
   262|
   263|**Files:**
   264|- Modify: `plugins/stats/dialog.py`
   265|
   266|**完成标准：**
   267|- [ ] 导入 common_styles 模块
   268|- [ ] 标题栏使用 COLOR_BG_PRIMARY
   269|- [ ] 卡片使用 COLOR_BG_SECONDARY
   270|- [ ] 文字使用 COLOR_TEXT_PRIMARY / COLOR_TEXT_SECONDARY
   271|- [ ] 按钮使用 create_primary_button / create_secondary_button
   272|- [ ] 分隔线使用 COLOR_BORDER
   273|- [ ] 环形图使用 oklch 配色
   274|
   275|**Step 1: 修改 imports**
   276|
   277|在 `plugins/stats/dialog.py` 顶部添加：
   278|```python
   279|from plugins.common_styles import (
   280|    COLOR_BG_PRIMARY, COLOR_BG_SECONDARY, COLOR_BG_TERTIARY,
   281|    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
   282|    COLOR_BORDER, COLOR_PRIMARY,
   283|    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_CAPTION,
   284|    SPACING_SM, SPACING_MD, SPACING_LG,
   285|    RADIUS_SM, RADIUS_MD, RADIUS_LG,
   286|    create_title_label, create_body_label, create_caption_label,
   287|    create_primary_button, create_secondary_button, create_separator
   288|)
   289|```
   290|
   291|**Step 2: 更新 STYLESHEET**
   292|
   293|将硬编码的颜色值替换为 common_styles 的常量。
   294|
   295|**Step 3: 更新组件创建**
   296|
   297|将手动创建的 QLabel、QPushButton 替换为 create_xxx 函数。
   298|
   299|**Step 4: 验证语法**
   300|
   301|Run: `python3 -m py_compile plugins/stats/dialog.py`
   302|Expected: 无输出
   303|
   304|**Step 5: Commit**
   305|
   306|```bash
   307|git add plugins/stats/dialog.py
   308|git commit -m "refactor: 统计弹窗应用通用样式"
   309|```
   310|
   311|---
   312|
   313|### Task 1.3：设置弹窗应用通用样式
   314|
   315|**Objective:** 设置弹窗使用 common_styles 的配色和组件
   316|
   317|**Files:**
   318|- Modify: `plugins/settings/dialog.py`
   319|
   320|**完成标准：**
   321|- [ ] 导入 common_styles 模块
   322|- [ ] 标题栏使用 COLOR_BG_PRIMARY
   323|- [ ] 侧边栏使用 COLOR_BG_SECONDARY
   324|- [ ] 按钮使用 create_primary_button / create_secondary_button
   325|- [ ] ToggleSwitch 使用 COLOR_PRIMARY
   326|- [ ] 文字大小统一（标题 16px、正文 13px、说明 11px）
   327|
   328|**Step 1-5:** 同 Task 1.2 的流程
   329|
   330|---
   331|
   332|### Task 1.4：关于弹窗应用通用样式
   333|
   334|**Objective:** 关于弹窗使用 common_styles 的配色和组件
   335|
   336|**Files:**
   337|- Modify: `plugins/about/plugin.py`
   338|
   339|**完成标准：**
   340|- [ ] 导入 common_styles 模块
   341|- [ ] 背景色使用 COLOR_BG_PRIMARY
   342|- [ ] 强调色使用 COLOR_PRIMARY
   343|- [ ] 文字颜色使用 COLOR_TEXT_PRIMARY / COLOR_TEXT_SECONDARY
   344|
   345|**Step 1-5:** 同 Task 1.2 的流程
   346|
   347|---
   348|
   349|### Task 1.5：更新环形图配色
   350|
   351|**Objective:** 统计弹窗的环形图使用 oklch 配色
   352|
   353|**Files:**
   354|- Modify: `plugins/stats/dialog.py`（DonutChart 类）
   355|
   356|**完成标准：**
   357|- [ ] 环形图颜色从硬编码 RGB 改为 oklch 生成
   358|- [ ] 颜色数量足够（至少 8 种）
   359|- [ ] 视觉效果与原版一致或更好
   360|
   361|**Step 1: 更新 FALLBACK_COLORS**
   362|
   363|```python
   364|from plugins.common_styles import oklch_to_qcolor
   365|
   366|class DonutChart(QWidget):
   367|    # 备用颜色（oklch 生成）
   368|    FALLBACK_COLORS = [
   369|        oklch_to_qcolor(0.7, 0.15, 25),   # 红
   370|        oklch_to_qcolor(0.7, 0.15, 70),   # 黄
   371|        oklch_to_qcolor(0.7, 0.15, 145),  # 绿
   372|        oklch_to_qcolor(0.7, 0.15, 230),  # 蓝
   373|        oklch_to_qcolor(0.7, 0.15, 300),  # 紫
   374|        oklch_to_qcolor(0.7, 0.15, 30),   # 橙
   375|        oklch_to_qcolor(0.7, 0.15, 180),  # 青
   376|        oklch_to_qcolor(0.7, 0.15, 340),  # 粉
   377|    ]
   378|```
   379|
   380|**Step 2-4:** 验证、测试、Commit
   381|
   382|---
   383|
   384|### Task 1.6：更新进度条配色
   385|
   386|**Objective:** 统计弹窗的进度条使用 oklch 配色
   387|
   388|**Files:**
   389|- Modify: `plugins/stats/dialog.py`（_ProgressBar 类）
   390|
   391|**完成标准：**
   392|- [ ] 进度条背景使用 COLOR_BG_TERTIARY
   393|- [ ] 进度条填充使用 oklch 生成的颜色
   394|- [ ] 视觉效果与原版一致或更好
   395|
   396|---
   397|
   398|### Task 1.7：更新 CategoryRow 配色
   399|
   400|**Objective:** 统计弹窗的分类行使用 oklch 配色
   401|
   402|**Files:**
   403|- Modify: `plugins/stats/dialog.py`（CategoryRow 类）
   404|
   405|**完成标准：**
   406|- [ ] 分类名称使用 COLOR_TEXT_PRIMARY
   407|- [ ] 时长使用 COLOR_TEXT_SECONDARY
   408|- [ ] 百分比使用 COLOR_TEXT_SECONDARY
   409|- [ ] 进度条使用 oklch 配色
   410|
   411|---
   412|
   413|### Task 1.8：验证 P1 效果
   414|
   415|**Objective:** 确保所有弹窗样式统一，无视觉错误
   416|
   417|**完成标准：**
   418|- [ ] 语法检查通过：`python3 -m py_compile plugins/stats/dialog.py plugins/settings/dialog.py plugins/about/plugin.py`
   419|- [ ] 约束检查通过：`python3 harness/checks.py`
   420|- [ ] 手动测试：打开统计弹窗、设置弹窗、关于弹窗，确认样式一致
   421|
   422|---
   423|
   424|## P2：代码清理
   425|
   426|### Task 2.1：清理空 catch 块
   427|
   428|**Objective:** 所有空 except 块添加注释说明
   429|
   430|**Files:**
   431|- Modify: `main.py`（1 处）
   432|- Modify: `kernel/event_bus.py`（1 处）
   433|- Modify: `plugins/overlay/plugin.py`（2 处）
   434|- Modify: `plugins/stats/plugin.py`（1 处）
   435|
   436|**完成标准：**
   437|- [ ] 所有空 except 块有注释说明为什么忽略
   438|- [ ] 约束检查通过：`python3 harness/checks.py`
   439|
   440|**Step 1: 查找空 catch 块**
   441|
   442|Run: `grep -n "except.*:$" plugins/stats/plugin.py plugins/overlay/plugin.py kernel/event_bus.py main.py | head -20`
   443|
   444|**Step 2: 逐个添加注释**
   445|
   446|例如：
   447|```python
   448|# 原来
   449|except Exception:
   450|    pass
   451|
   452|# 改为
   453|except Exception:
   454|    # 忽略：xxx 操作失败不影响主流程
   455|    pass
   456|```
   457|
   458|**Step 3: 验证**
   459|
   460|Run: `python3 harness/checks.py`
   461|Expected: 0 violations
   462|
   463|---
   464|
   465|### Task 2.2：提取魔法数字
   466|
   467|**Objective:** 将硬编码的数字提取为常量
   468|
   469|**Files:**
   470|- Modify: `plugins/overlay/plugin.py`（定时器间隔、透明度等）
   471|- Modify: `plugins/desktop_pet/widget.py`（长按时间、定时器间隔等）
   472|- Modify: `plugins/stats/plugin.py`（缓存大小、超时时间等）
   473|
   474|**完成标准：**
   475|- [ ] 所有魔法数字提取为模块级常量
   476|- [ ] 常量有注释说明用途
   477|- [ ] 逻辑行为不变
   478|
   479|---
   480|
   481|### Task 2.3：提取重复代码
   482|
   483|**Objective:** 将重复的代码提取为公共方法
   484|
   485|**Files:**
   486|- Modify: `plugins/overlay/plugin.py`
   487|- Modify: `plugins/desktop_pet/widget.py`
   488|
   489|**完成标准：**
   490|- [ ] 窗口状态保存逻辑提取为公共方法
   491|- [ ] TOPMOST 维护逻辑提取为公共方法
   492|- [ ] 逻辑行为不变
   493|
   494|---
   495|
   496|### Task 2.4：清理未使用的 import
   497|
   498|**Objective:** 删除未使用的 import 语句
   499|
   500|**Files:**
   501|

---

## P4 验收标准

1. SPEC.md 已更新（版本号、配色、测试覆盖）
2. DECISIONS.md 已添加新决策
3. devlog 已创建

*编写时间：2026-06-28*
