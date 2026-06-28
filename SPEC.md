# WindowStatus 项目规格文档

> 最后更新：2026-06-28-16:00
> 基于 devlog 更新至：2026-06-28
> 当前版本：v3.5.0
> 总代码行数：~8500 行（38 个 Python 文件 + 7 个测试文件）

---

## 一、项目简介

WindowStatus 是一个 Windows 桌面窗口状态显示器，监控用户当前使用的应用，自动分类（游戏/办公/摸鱼/开发/工具），并通过悬浮气泡和桌宠显示实时状态。

**技术栈：** Python 3 + PyQt5
**平台：** Windows 10/11
**定位：** 常驻后台轻量工具（内存几十 MB，比 Electron 轻十倍）

---

## 二、核心架构

三层结构，职责分明：

```
┌──────────────────────────────────────────┐
│           main.py（入口 + 组装）           │
│  WindowStatusApp: QApplication + Kernel   │
│  全局异常钩子 + Qt 平台插件路径修复         │
├──────────────────────────────────────────┤
│           Kernel（核心层）                  │
│  ┌───────────┬───────────┬──────────────┐ │
│  │ EventBus  │  Config   │ PluginManager│ │
│  │ 事件总线   │ 配置管理   │ 插件管理器    │ │
│  │ 线程安全   │ RLock锁   │ 拓扑排序加载  │ │
│  └───────────┴───────────┴──────────────┘ │
├──────────────────────────────────────────┤
│           Plugins（插件层）                 │
│  monitor / overlay / desktop_pet /        │
│  rules / stats / settings / tray / about  │
│  各司其职，通过 EventBus 通信              │
└──────────────────────────────────────────┘
```

**关键原则：**
- 插件之间**不直接调用**，只通过 EventBus 通信
- 插件通过 `self._kernel`（私有）访问核心服务
- 插件通过 `get_plugin(name)` 获取其他插件实例（受限接口）
- 一个 UI 元素只由一个插件负责（v3.3.0 教训）

---

## 三、目录结构

```
WindowStatus/
├── main.py                    # 入口（234行）
│   ├── _setup_excepthook()    # 全局异常钩子
│   ├── _fix_qt_plugin_path()  # Qt 平台插件路径修复
│   └── WindowStatusApp        # 主应用类
├── kernel/                    # 核心层（4个文件，~1326行）
│   ├── core.py                # Kernel 类（144行）
│   ├── event_bus.py           # EventBus + Events 常量（245行）
│   ├── config.py              # Config 配置管理（492行）
│   └── plugin_manager.py      # PluginManager 插件加载/卸载（434行）
├── plugins/                   # 插件层（8个插件 + 通用样式模块）
│   ├── base.py                # Plugin 基类（130行）
│   ├── utils.py               # 插件工具函数 + ToggleSwitch 组件（431行）
│   ├── common_styles.py       # 通用样式模块（191行，oklch 配色）
│   ├── monitor/plugin.py      # 窗口监控（282行）
│   ├── overlay/plugin.py      # 悬浮气泡（426行）
│   ├── desktop_pet/
│   │   ├── plugin.py          # 桌宠逻辑（403行）
│   │   └── widget.py          # 桌宠 Widget（219行）
│   ├── rules/plugin.py        # 分类规则（243行）
│   ├── stats/
│   │   ├── plugin.py          # 统计逻辑（1121行）
│   │   └── dialog.py          # 统计弹窗（733行）
│   ├── settings/
│   │   ├── plugin.py          # 设置插件（189行）
│   │   └── dialog.py          # 设置弹窗（820行）
│   ├── tray/plugin.py         # 系统托盘（230行）
│   └── about/plugin.py        # 关于页面（169行）
├── tests/                     # 单元测试（7个文件，~1500行）
│   ├── test_event_bus.py      # EventBus 测试（270行）
│   ├── test_config.py         # Config 测试（265行）
│   ├── test_desktop_pet.py    # 桌宠测试（236行）
│   ├── test_desktop_pet_position.py  # 桌宠位置测试（242行）
│   ├── test_rules.py          # 规则测试（240行）
│   ├── test_state_machine.py  # 状态机测试（175行）
│   └── test_utils.py          # 工具测试（87行）
├── harness/                   # Harness 工程规范
│   ├── SPEC.md                # Harness 工程规范
│   ├── CONSTRAINTS.md         # 代码约束（自动检查）
│   ├── DECISIONS.md           # 决策档案（只增不改）
│   ├── TEST_CONVENTIONS.md    # 测试规范
│   ├── checks.py              # 约束自动检查脚本
│   └── runner.py              # 测试入口
├── docs/plans/                # 执行方案
├── build.py                   # PyInstaller 打包脚本（179行）
├── assets/                    # 资源文件
├── docs/specs/                # 功能规格
├── SPEC.md                    # 本文件
├── CHANGELOG.md               # 版本更新日志
└── README.md                  # 项目说明
```

---

## 四、核心模块详解

### 4.1 Kernel（kernel/core.py）

协调各核心模块的生命周期：

```
__init__(config_path, db_path, log_path)
  ├── 创建 EventBus
  ├── 创建 Config
  ├── 创建 PluginManager
  └── 初始化日志（RotatingFileHandler, 10MB × 3）

set_qt_app(app)
  ├── 设置 QApplication 引用
  ├── 设置主线程引用
  └── 传递给 EventBus（用于跨线程事件分发）

start() → load_plugins()
stop()  → unload_plugins() → off_all_handlers()
```

### 4.2 EventBus（kernel/event_bus.py）

两种事件发送方式：
- `emit(event, **kwargs)` — 同步发送，在调用线程执行
- `emit_to_main(event, **kwargs)` — 通过 `QTimer.singleShot` 转发到主线程（GUI 插件使用）

线程安全：所有公共方法使用 `threading.Lock()` 保护。

### 4.3 Config（kernel/config.py）

- 所有公开方法加 `threading.RLock()`（v3.3.1 修复）
- 支持 `reload()` 方法（进程内重启用）
- 默认配置合并用户配置（deep merge）
- 分类规则内置在 `DEFAULT_CATEGORIES`（游戏/办公/摸鱼/开发/工具）

### 4.4 PluginManager（kernel/plugin_manager.py）

- 自动发现 `plugins/` 目录下的插件
- 每个子目录必须包含 `plugin.py`，其中定义 `PluginClass` 变量
- 拓扑排序加载（`dependencies` 属性确保顺序）
- 关闭顺序：先 `off_all_handlers()` 再逐个 `on_unload()`

---

## 五、插件系统

### 5.1 插件基类（plugins/base.py）

```python
class Plugin:
    name: str              # 插件名称
    version: str           # 版本
    description: str       # 描述
    dependencies: tuple    # 依赖列表
    DEFAULT_CONFIG: dict   # 默认配置

    # 生命周期
    __init__(kernel)       # 注入 Kernel
    on_load()              # 注册事件、初始化资源
    on_enable()            # 恢复功能
    on_disable()           # 暂停功能
    on_unload()            # 注销事件、释放资源

    # 受限接口
    get_plugin(name)       # 获取其他插件
    get_all_plugins()      # 获取所有插件
    main_window            # 主窗口引用
```

### 5.2 插件列表

| 插件 | 文件 | 行数 | 默认启用 | 职责 |
|------|------|------|---------|------|
| monitor | monitor/plugin.py | 282 | ✅ | 监控活动窗口（SetWinEventHook）+ 空闲检测（GetLastInputInfo） |
| rules | rules/plugin.py | 243 | ✅ | 窗口标题/进程名 → 分类匹配 |
| overlay | overlay/plugin.py | 386 | ✅ | 悬浮气泡（QPainter 绘制，支持亮色/暗色主题） |
| desktop_pet | desktop_pet/plugin.py + widget.py | 408+ | ❌ | 桌宠（图片显示、拖拽、位置记忆、跟随气泡） |
| stats | stats/plugin.py + dialog.py | 1039+705 | ✅ | 使用统计（SQLite 存储 + Apple 风格统计弹窗 + 周/月摘要卡片） |
| settings | settings/plugin.py + dialog.py | 604 | ✅ | 设置页面（侧边栏布局、toggle 开关、规则编辑、插件管理） |
| tray | tray/plugin.py | 236 | ✅ | 系统托盘菜单（精简：显示/隐藏/置顶/统计/设置/重启/退出） |
| about | about/plugin.py | — | ✅ | 关于页面（FramelessDialog 深色标题栏） |

### 5.3 事件流

```
monitor ──WINDOW_CHANGED──→ rules ──CATEGORY_MATCHED──→ overlay（更新气泡显示）
                                     ──CATEGORY_MATCHED──→ desktop_pet（更新桌宠状态）
                                     ──CATEGORY_MATCHED──→ stats（记录使用数据）

monitor ──IDLE_DETECTED──→ desktop_pet（切换空闲动画）
monitor ──IDLE_RESUMED──→ desktop_pet（恢复正常动画）

settings ──RULES_RELOAD──→ rules（重新加载规则）
settings ──OVERLAY_SET_THEME──→ overlay（切换主题）

tray ──QUIT──→ main（退出应用）
tray ──RESTART──→ main（进程内重载）
tray ──SHOW_STATS──→ main → stats（显示统计弹窗）
```

### 5.4 插件间耦合关系

```
desktop_pet → overlay（获取气泡位置/尺寸，用于跟随定位）
stats → overlay（无直接依赖，通过 CATEGORY_MATCHED 事件独立工作）
settings → rules + overlay（通过事件，不直接调用）
tray → main（通过事件委托）
```

---

## 六、数据存储

| 类型 | 路径 | 说明 |
|------|------|------|
| 配置文件 | `~/.WindowStatus/config.json` | JSON，插件配置 + 分类规则 + UI 设置 |
| 统计数据库 | `~/.WindowStatus/data.db` | SQLite，存储使用统计 |
| 运行日志 | `~/.WindowStatus/window_status.log` | RotatingFileHandler, 10MB × 3 |
| 备份目录 | `~/.WindowStatus/backups/` | 数据备份 |

打包后资源文件在 `sys._MEIPASS`，用户数据在 `~/.WindowStatus/`。

---

## 七、UI 组件

### 7.1 悬浮气泡（overlay/plugin.py）

- QPainter 纯代码绘制（不用外部素材，版权合规）
- 支持亮色/暗色主题（通过 OVERLAY_SET_THEME 事件切换）
- 小气泡连接：半径 3px 的 drawEllipse，位于大气泡右下角
- 整体边界检测：气泡 + 桌宠作为整体受屏幕边界约束
- 位置可拖拽，记住位置（保存到 config）
- TOPMOST 维护：1 秒定时器 + SetWindowPos(0x0203)

### 7.2 桌宠（desktop_pet/plugin.py + widget.py）

- 图片显示（exe 同目录自定义素材优先，内置兜底）
- 长按 200ms 触发拖拽，拖拽时同步气泡位置
- 位置记忆：退出时保存坐标到 config，启动时恢复
- 状态保护：拖拽中忽略分类匹配事件，避免状态闪烁
- 跟随气泡：气泡移动时桌宠自动跟随
- TOPMOST 维护：1 秒定时器 + SetWindowPos(0x0203)

### 7.3 统计弹窗（stats/dialog.py）

- Apple Screen Time 风格，窗口 750×520
- SummaryCard：三列等分布局（QGridLayout），分隔线与 grid 列对齐
- DonutChart：QPainter 自绘环形图（180×180），FlatCap，2px 间隙，WA_TranslucentBackground
- CategoryRow：emoji + 名称 + 圆角进度条 + 时长 + 百分比
- 周/月 tab 带三列摘要卡片（总时长 + 最常用分类 + vs 上周/上月）
- 参数化 SummaryCard（total_label/compare_label/compare_prefix）

### 7.4 设置弹窗（settings/dialog.py）

- FramelessDialog 无边框圆角弹窗，720×580
- 通用 tab：侧边栏（通用设置/外观/通知）+ QStackedWidget
- ToggleSwitch 自绘组件（40×22 轨道 + 18×18 白色圆形滑块）
- 基本设置：开机自启/关闭时最小化到托盘/窗口置顶
- 悬浮窗：透明度/空闲检测
- 数据管理：导出CSV/JSON/关于
- 插件管理 tab：ToggleSwitch 替代 QCheckBox

### 7.5 关于弹窗（about/plugin.py）

- 继承 FramelessDialog，深色标题栏
- 配色：#121212 底色 + #d97706 琥珀强调

---

## 八、开发环境限制

### WSL 无法启动 Windows GUI 程序

从 WSL 调用 Windows Python 的 `QApplication(sys.argv)` 会卡死，Qt 拿不到 Windows 桌面上下文。纯命令行程序（python -c、pytest、py_compile）没问题，但任何需要 GUI 的操作（创建窗口、截图、pyautogui）都不行。卡点在 QApplication 初始化，不是代码问题。

**工作流：** WSL 负责代码编写 + 语法验证（py_compile），Windows 端负责 GUI 测试 + 打包。

### SDD 文档体系

| 文档 | 用途 | 更新频率 |
|------|------|---------|
| SPEC.md | 项目图纸，稳定 | 收工时同步 |
| DECISIONS.md | 决策档案，只增不改 | 有新决策时 |
| devlog | 日记，每天更新 | 每次改动后 |
| handoff | 便签，交接用 | 上下文紧张时 |

- 所有文档时间戳精确到小时（YYYY-MM-DD-HH:MM）
- SPEC/DECISIONS 头部有"基于 devlog 更新至"水印
- devlog 是原材料，SPEC 和 DECISIONS 从中提炼
- 开工前必读顺序：SPEC（含过期检测）→ DECISIONS → 最近 devlog
- 收工后必写：devlog → 更新 DECISIONS → 更新 SPEC（含时间戳）→ handoff
- 开发日志路径：`~/.hermes/docs/logs/`（WSL），备份到 `C:\Agent\kaifarizhi\`（Windows）

---

## 九、打包与发布

### 9.1 PyInstaller 打包

```bash
# Windows 端执行
python build.py
```

输出：`dist/WindowStatus/WindowStatus.exe`

**关键配置：**
- `main.py` 开头必须有 `_fix_qt_plugin_path()`
- 资源文件路径：打包后用 `sys._MEIPASS`，开发模式用 `os.path.dirname(__file__)`
- 系统托盘图标路径必须用 `sys._MEIPASS`

### 9.2 打包注意事项

- 必须在 Windows 端打包，WSL 下需要 wine
- dev 模式和打包后行为可能不同（任务栏图标、文件路径、权限）
- 打包后单独测试：任务栏行为、数据目录、文件路径、插件开关保存

---

## 十、开发规范

### 10.1 新功能开发流程

```
需求模糊 → grill-me 追问 → 方案对比 → 确认 → 逐步执行
→ py_compile 验证 → 本地测试 → 主人确认 → commit + push
```

### 10.2 插件开发规范

新建插件需要：
1. 创建 `plugins/<name>/plugin.py`，继承 `Plugin`
2. 定义 `name`、`version`、`description`
3. 实现生命周期方法（至少 `on_load` 和 `on_unload`）
4. 在 `plugin_manager.py` 的 `plugin_modules` 列表添加模块路径
5. 在 `build.py` 的 `hiddenimports` 添加打包路径
6. 在 `config.py` 的 `DEFAULT_CONFIG["plugins"]` 添加启用项

### 10.3 TDD 规范

- 重要功能必须先写测试再写代码（桌宠位置记忆用 TDD 方式成功实现）
- 测试文件放在 `tests/` 目录
- 用 `python -m pytest tests/` 运行

---

## 十一、已知踩坑记录

### PyQt5 踩坑

| 编号 | 问题 | 解决方案 |
|------|------|---------|
| P1 | Qt.Tool 在 Win11 上鼠标事件失效 | 需要拖拽的 widget 不加 Qt.Tool |
| P2 | QRectF 在 QtCore 而非 QtGui | `from PyQt5.QtCore import QRectF` |
| P3 | parent.show() 不自动显示子 widget | 每个子 widget 单独调用 show() |
| P4 | exec_() 阻塞事件循环 | 改用 show()，保持引用防 GC |
| P5 | Widget 类没有 event_bus 属性 | 从 plugin 传 event_bus 或从 handler 发 |
| P14 | 事件触发顺序问题 | on_enable 时立即创建 widget，不延迟 |
| P15 | 窗口快速切换事件风暴 | 加防抖（debounce） |
| P13 | QDesktopWidget 已废弃 | 改用 QApplication.primaryScreen().geometry() |
| P27 | 气泡闪到屏幕中间 | 先 hide() → move() → show() |

### QPainter 踩坑

| 编号 | 问题 | 解决方案 |
|------|------|---------|
| P6 | QPainterPath.united() 有接缝 | 放弃尾巴，改用 drawEllipse 小圆点 |
| P7 | addPath/united 合并不可靠 | 用独立的 drawEllipse/drawPolygon 分别绘制 |

### 架构踩坑

| 编号 | 问题 | 解决方案 |
|------|------|---------|
| P8 | 双气泡 bug（两个插件都创建 widget） | 一个 UI 元素只由一个插件负责 |
| P11 | dev 模式和打包后行为不同 | 打包后单独测试 |
| P20 | PyInstaller 下 os.execv 重启失败 | 改为进程内重载 |
| P24 | __pycache__ 导致代码改动不生效 | 在运行端清缓存 |
| P25 | 中文 cmd.exe 吞掉双下划线 | 用 Python 脚本代替内联命令 |

---

## 十二、技术债务

| 编号 | 描述 | 优先级 | 状态 |
|------|------|--------|------|
| 1 | 没有导入功能（只有导出） | 低 | 待定 |
| 2 | 单元测试覆盖不全 | 中 | P3 计划全覆盖 |
| 3 | API 文档缺失 | 低 | 待定 |
| 4 | 大量规则时匹配性能 | 低 | 待定 |
| 5 | 只在 Win10/11 测试过 | 低 | 待定 |
| 6 | 弹窗样式统一 | 高 | ✅ v3.5.0 完成 |
| 7 | 代码清理（空catch/魔法数字） | 中 | ✅ v3.5.0 完成 |

---

## 十三、版本历史摘要

| 版本 | 日期 | 里程碑 |
|------|------|--------|
| v1.0.0 | 2026-05-27 | 单文件原型（1020行） |
| v2.0 | 2026-05-28 | 插件化重构（core/ + plugins/） |
| v3.0.0 | 2026-05-28 | 插件化完善 + PyInstaller 打包 |
| v3.1.0 | 2026-05-28 | 周/月统计 + Idle 检测 + 插件配置 |
| v3.2.0 | 2026-05-29 | 桌面宠物 + 气泡状态栏 |
| v3.3.0 | 2026-05-29 | 气泡改造 + 暗色/亮色主题 |
| v3.3.1 | 2026-05-30 | 架构重构（4项重大修复） |
| v3.3.2 | 2026-05-30 | 桌宠拖拽 + 进程内重启 + 删除气泡拖拽 |
| v3.3.4 | 2026-05-31 | 统计界面重做 + 桌宠记住位置 + SummaryCard 重构 |
| — | 2026-06-03 | 删除 Reminders 插件 |
| v3.4.0 | 2026-06-13 | 视觉重设计（暗色配色/自绘组件/设置侧边栏/功能迁移） |
| v3.5.0 | 2026-06-28 | 弹窗样式统一（oklch配色/common_styles模块）、代码清理（空catch/魔法数字/未使用import） |

---

## 十四、文件路径速查

| 用途 | 路径 |
|------|------|
| 项目根目录 | `C:\Users\秋月\Desktop\WindowStatus\` |
| 数据目录 | `C:\Users\秋月\.WindowStatus\` |
| 配置文件 | `C:\Users\秋月\.WindowStatus\config.json` |
| 统计数据库 | `C:\Users\秋月\.WindowStatus\data.db` |
| 运行日志 | `C:\Users\秋月\.WindowStatus\window_status.log` |
| WSL 开发日志 | `~/.hermes/docs/logs/WindowStatus.md` |
| 日志备份 | `C:\Agent\kaifarizhi\` |

---

*基于 devlog（2026-05-27 ~ 2026-06-07）、handoff 整合版、现有 SPEC.md、源码结构梳理*