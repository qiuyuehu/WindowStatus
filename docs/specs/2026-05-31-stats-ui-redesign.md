# 统计界面改进方案 — Apple Screen Time 风格

## 一、设计目标

将统计弹窗从"纯文字表格"升级为"Apple Screen Time 风格"的可视化仪表盘。
核心改动只涉及 UI 层（dialog.py），不动数据库和统计逻辑。

## 二、已确认的设计决策

| 决策 | 选择 | 说明 |
|------|------|------|
| 视觉风格 | Apple Screen Time | 圆润、留白、柔和渐变色 |
| 窗口尺寸 | 固定 750x600 | 不可拉伸 |
| 摘要内容 | 今日总时长 + 最常用分类 + 和昨天对比 | 三个核心指标 |
| 列表样式 | 进度条 + emoji + 百分比 | 不要左侧色条 |
| 进度条背景色 | #2a2a4e | 比面板底色稍亮 |
| 时间线 tab | 保持表格，分类列加颜色 | 最小改动 |
| 环形占比图 | 做 | QPainter 自绘 |
| 导出按钮 | 加 | CSV 和 JSON |
| 加载动画 | 不做 | 直接显示最终状态 |
| 主题 | 只做暗色 | 实际只有气泡支持主题切换 |

## 三、UI 布局设计

### 整体结构（750x600 固定）

```
┌─────────────────────────────────────────────────────────────┐
│  [Tab: 今日统计] [本周统计] [本月统计] [时间线]              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─── 摘要卡片 ──────────────────────────────────────────┐  │
│  │                                                       │  │
│  │   5小时32分          🎮 游戏 占 35%      比昨天多 12%  │  │
│  │   今日总时长         最常用分类           ↑绿色/↓红色   │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─── 环形图 ─────┐  ┌─── 分类列表 ─────────────────────┐  │
│  │                │  │                                   │  │
│  │    ╭────╮      │  │  🎮 游戏   ██████████░░  2h15m 35% │  │
│  │   ╱  35% ╲     │  │  📊 办公   ███████░░░░  1h40m 27% │  │
│  │  │  27%   │    │  │  🐟 摸鱼   █████░░░░░░  1h05m 21% │  │
│  │   ╲  21% ╱     │  │  💻 其他   ███░░░░░░░░  32m   17% │  │
│  │    ╰────╯      │  │                                   │  │
│  │                │  └───────────────────────────────────┘  │
│  └────────────────┘                                         │
│                                                             │
│                              [导出 CSV] [导出 JSON] [关闭]  │
└─────────────────────────────────────────────────────────────┘
```

### 摘要卡片设计

- 容器：圆角 12px，背景色 #16213e，内边距 16px
- 三列布局，用 QHBoxLayout
- 左列：大号数字（24px 加粗）"5小时32分"，小字（12px）"今日总时长"
- 中列：emoji + 分类名 + "占 XX%"，小字"最常用分类"
- 右列：比昨天多/少 XX%，上升用绿色 #4ecdc4，下降用红色 #ff6b6b，小字"vs 昨天"
- 如果昨天没数据，右列显示"无对比数据"

### 环形图设计

- 尺寸：180x180px
- 用 QPainter 自绘，不需要外部库
- 圆环宽度 30px，外半径 80px，内半径 50px
- 每个扇区颜色从分类配置的 color 读取
- 扇区之间留 2px 间隙（画背景色线条分隔）
- 中间空白区域显示总时长（小字）
- 分类只有 1 个时：画整圆，不画间隙
- 分类为 0 时：画一个灰色空圆环

### 分类列表设计

- 每行高度 48px，行间距 8px
- 左侧：emoji 图标（20px）+ 分类名（14px）
- 中间：圆角进度条（高度 8px，圆角 4px）
  - 填充色：分类的 color
  - 背景色：#2a2a4e
  - 宽度自适应填满
- 右侧：时长文字（12px）+ 百分比（12px，灰色）
- 列表用 QVBoxLayout + 固定高度行，不用 QTableWidget

### 时间线 tab 设计

- 保持 QTableWidget 表格布局
- 分类列：文字前加一个小色块（12x12px 圆角矩形），颜色从分类配置读取
- 其他列不变

### 底部按钮栏

- 三个按钮：导出 CSV | 导出 JSON | 关闭
- 用 QHBoxLayout，按钮在右侧
- 导出按钮样式：背景 #0f3460，hover #1a4a8a
- 导出成功后弹一个 QMessageInformation 提示导出路径

## 四、数据流变更

### 现在的数据流

```
plugin.show_dialog()
  → get_today_stats()       → [(分类, 时长), ...]
  → get_today_timeline()    → [(标题, 进程, 分类, 开始时间, 时长), ...]
  → get_week_stats()        → [(分类, 时长), ...]
  → get_month_stats()       → [(分类, 时长), ...]
  → StatsDialog(4 组数据)
```

### 改造后的数据流

```
plugin.show_dialog()
  → get_today_stats()       → [(分类, 时长), ...]
  → get_today_timeline()    → [(标题, 进程, 分类, 开始时间, 时长), ...]
  → get_week_stats()        → [(分类, 时长), ...]
  → get_month_stats()       → [(分类, 时长), ...]
  → get_yesterday_stats()   → [(分类, 时长), ...]   ← 新增
  → kernel.config.get_categories()  → {分类: {icon, color, ...}}  ← 新增
  → StatsDialog(4 组数据 + 昨天数据 + 分类配置)
```

### 新增方法：get_yesterday_stats()

在 plugin.py 中新增，逻辑和 get_today_stats() 一样，只是日期换成昨天。
查询 daily_stats 表（昨天的数据已被聚合到那里），如果没数据则查 activity_log。

## 五、文件改动清单

### 1. plugins/stats/dialog.py（重写）

完全重写，不保留现有代码。新文件结构：

```
StatsDialog(QDialog)
├── STYLESHEET          # 暗色主题样式表
├── __init__()          # 接收 6 组数据（新增昨天数据+分类配置）
├── _create_summary_card()   # 摘要卡片
├── _create_donut_chart()    # 环形图（QPainter 自绘）
├── _create_category_list()  # 分类列表（进度条）
├── _create_stats_tab()      # 组装：摘要+环形图+列表
├── _create_timeline_tab()   # 时间线表格（加颜色）
├── _create_export_buttons() # 导出按钮
└── _export_csv() / _export_json()  # 导出回调
```

新增的内部类/组件：
- DonutChart(QWidget) — 环形图自绘组件，重写 paintEvent
- CategoryRow(QWidget) — 单行分类组件，包含 emoji+名称+进度条+时长
- SummaryCard(QWidget) — 摘要卡片组件

### 2. plugins/stats/plugin.py（小改）

改动点：
- show_dialog() 方法：新增获取昨天数据和分类配置，传给 StatsDialog
- 新增 get_yesterday_stats() 方法（约 20 行）
- show_dialog 的 StatsDialog 构造参数从 4 个增加到 6 个

### 不动的文件

- kernel/config.py — 不改，通过 kernel.config.get_categories() 读取
- kernel/event_bus.py — 不改
- main.py — 不改（show_dialog 调用方式不变）
- plugins/utils.py — 不改

## 六、风险评估与应对方案

### 风险 1：环形图在极端数据下的渲染问题

**场景：** 分类只有 1 个（占比 100%）、分类超过 8 个、某个分类时长为 0
**应对：**
- 只有 1 个分类：画整圆，不画间隙
- 超过 8 个分类：只显示前 7 个 + "其他"合并
- 时长为 0 的分类：不参与环形图绘制，列表中显示但进度条为空
- 环形图用 360 度整圆计算，每个扇区角度 = (时长/总时长) * 360，用浮点数避免累计误差

### 风险 2：昨天无数据（首次使用或新装）

**场景：** daily_stats 和 activity_log 中都没有昨天的数据
**应对：**
- get_yesterday_stats() 返回空列表
- 摘要卡片右列显示"无对比数据"（灰色文字，不显示百分比）
- 不影响其他部分的显示

### 风险 3：plugin.py 传参遗漏

**场景：** show_dialog 传给 StatsDialog 的参数顺序或数量不对
**应对：**
- StatsDialog 用关键字参数（keyword arguments）接收，不用位置参数
- 每个参数给默认值（None 或空列表），即使漏传也不会崩溃
- dialog.py 内部对每个数据源做空值检查

### 风险 4：分类颜色值格式不一致

**场景：** config 中 color 是 [255, 107, 107]（列表），但 QColor 需要 (r, g, b) 元组
**应对：**
- dialog.py 中统一用 QColor(*color) 转换，兼容列表和元组
- 如果 color 缺失或格式错误，fallback 到灰色 (128, 128, 128)

### 风险 5：进度条在极小占比时不可见

**场景：** 某个分类只用了 10 秒，占比 0.1%，进度条几乎看不到
**应对：**
- 进度条最小宽度 4px（即使占比极小也能看到一条线）
- 百分比显示 "< 1%" 而不是 "0.1%"（小于 1% 的统一显示为 "< 1%"）

### 风险 6：QPainter 绘制在高 DPI 屏幕上模糊

**场景：** 2K/4K 屏幕上环形图和进度条可能出现锯齿
**应对：**
- 在 paintEvent 开头调用 painter.setRenderHint(QPainter.Antialiasing)
- 环形图用 QPen 设置为 Qt.FlatCap（平头），避免扇区两端圆弧重叠

### 风险 7：导出功能弹出文件对话框阻塞主线程

**场景：** 点击导出按钮后弹 QFileDialog，如果用户很久不操作
**应对：**
- QFileDialog 是模态对话框，会阻塞但这是正常的（用户在选路径）
- 导出完成后弹 QMessageInformation 提示成功
- 导出失败（权限、磁盘满）用 try-except 捕获，弹 QMessageBox.warning 提示错误

### 风险 8：环形图和列表数据不一致

**场景：** 环形图显示 5 个分类，列表显示 4 个（或反过来）
**应对：**
- 环形图和列表使用同一份数据源（传入的 stats_data）
- 在 __init__ 中统一处理一次，不要各自独立计算

## 七、执行步骤

### 步骤 1：plugin.py 新增 get_yesterday_stats 方法

**改动内容：**
- 在 StatsPlugin 类中新增 get_yesterday_stats() 方法
- 查询逻辑：先查 daily_stats（昨天已被聚合），如果没有就查 activity_log
- 返回格式和 get_today_stats() 一致：[(分类, 时长), ...]

**验证方式：** python3 -m py_compile plugins/stats/plugin.py

**预计耗时：** AI 2 分钟

### 步骤 2：plugin.py 修改 show_dialog 方法

**改动内容：**
- show_dialog 中新增获取昨天数据和分类配置的代码
- StatsDialog 构造参数从 4 个增加到 6 个（新增 yesterday_stats, categories_config）
- 用关键字参数传递，避免位置参数顺序错误

**验证方式：** python3 -m py_compile plugins/stats/plugin.py

**预计耗时：** AI 3 分钟

### 步骤 3：dialog.py 创建基础框架

**改动内容：**
- 重写 __init__，接收 6 组数据
- 写好 STYLESHEET（暗色主题）
- 搭建 tab 结构（4 个 tab）
- 先用占位内容，确保窗口能正常弹出

**验证方式：** python3 -m py_compile plugins/stats/dialog.py

**预计耗时：** AI 5 分钟

### 步骤 4：dialog.py 实现摘要卡片

**改动内容：**
- SummaryCard 组件：三列布局（总时长 / 最常用分类 / 昨天对比）
- 数据计算：从 stats_data 求总时长和最常用分类
- 从 yesterday_stats 计算对比百分比
- 无对比数据时显示灰色提示

**验证方式：** python3 -m py_compile plugins/stats/dialog.py

**预计耗时：** AI 5 分钟

### 步骤 5：dialog.py 实现环形图

**改动内容：**
- DonutChart(QWidget) 组件
- paintEvent 中用 QPainter 绘制圆环
- 扇区角度计算、颜色分配、间隙处理
- 中间显示总时长文字
- 边界情况处理（0 分类、1 分类、空数据）

**验证方式：** python3 -m py_compile plugins/stats/dialog.py

**预计耗时：** AI 8 分钟

### 步骤 6：dialog.py 实现分类列表

**改动内容：**
- CategoryRow(QWidget) 组件：emoji + 名称 + 进度条 + 时长 + 百分比
- 自绘进度条（QWidget + paintEvent），圆角胶囊形状
- 进度条最小宽度 4px
- 列表容器用 QVBoxLayout

**验证方式：** python3 -m py_compile plugins/stats/dialog.py

**预计耗时：** AI 8 分钟

### 步骤 7：dialog.py 组装今日统计 tab

**改动内容：**
- _create_stats_tab()：组装摘要卡片 + 环形图 + 分类列表
- 布局调整：环形图和列表的水平排列
- 确保各组件间距和对齐正确

**验证方式：** python3 -m py_compile plugins/stats/dialog.py

**预计耗时：** AI 5 分钟

### 步骤 8：dialog.py 改造时间线 tab

**改动内容：**
- 保持 QTableWidget 表格
- 分类列加上颜色小色块（用 QTableWidgetItem 的前景色或自定义 delegate）
- 其他列保持不变

**验证方式：** python3 -m py_compile plugins/stats/dialog.py

**预计耗时：** AI 3 分钟

### 步骤 9：dialog.py 实现导出按钮

**改动内容：**
- 底部按钮栏：导出 CSV | 导出 JSON | 关闭
- 导出回调：调用 plugin 的 export_to_csv/export_to_json
- 需要从 plugin 获取 conn 或让 plugin 暴露导出方法
- 成功/失败提示

**注意：** 导出回调需要访问 plugin 实例。当前 dialog 不持有 plugin 引用。
**解决方案：** show_dialog 时把 plugin 自身也传给 dialog，或把导出函数作为回调传入。

**验证方式：** python3 -m py_compile plugins/stats/dialog.py

**预计耗时：** AI 5 分钟

### 步骤 10：整体验证 + 语法检查

**改动内容：**
- 对所有改动文件执行 python3 -m py_compile
- 检查 import 是否完整
- 检查参数传递是否一致

**验证方式：** python3 -m py_compile 对所有 .py 文件

**预计耗时：** AI 2 分钟

### 步骤 11：主人测试

**操作：**
- 在 Windows 下运行 python main.py
- 点击托盘图标 → 查看统计
- 检查：摘要卡片、环形图、分类列表、时间线、导出按钮
- 截图反馈

**预计耗时：** 主人 5 分钟

## 八、总工作量估算

| 角色 | 耗时 |
|------|------|
| 人类开发者 | 3-5 小时 |
| AI（衾衾） | 约 45 分钟（步骤 1-10） |
| 主人测试 | 5 分钟 |

## 九、不做的事

- 不引入 matplotlib/plotly 等外部依赖
- 不改数据库结构
- 不改统计计算逻辑（除了新增 get_yesterday_stats）
- 不做加载动画
- 不做亮色主题
- 不做窗口可拉伸
- 不改其他插件
