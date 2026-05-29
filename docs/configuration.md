# 配置文件说明

WindowStatus 使用 JSON 格式的配置文件，位于 `~/.WindowStatus/config.json`。

## 目录

- [配置文件位置](#配置文件位置)
- [配置项说明](#配置项说明)
- [分类规则配置](#分类规则配置)
- [提醒配置](#提醒配置)
- [插件配置](#插件配置)
- [桌宠配置](#桌宠配置)
- [日志配置](#日志配置)
- [配置迁移](#配置迁移)

---

## 配置文件位置

| 平台 | 路径 |
|------|------|
| Windows | `C:\Users\<用户名>\.WindowStatus\config.json` |
| WSL | `/mnt/c/Users/<用户名>/.WindowStatus/config.json` |

其他相关文件：

| 文件 | 说明 |
|------|------|
| `data.db` | 统计数据库（SQLite） |
| `window_status.log` | 运行日志 |

---

## 配置项说明

### 基本配置

```json
{
    "version": "3.1.0",
    "opacity": 0.9,
    "always_on_top": true,
    "position": "top-right"
}
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `version` | string | `"3.1.0"` | 配置文件版本号（自动管理） |
| `opacity` | float | `0.9` | 悬浮窗透明度（0.0-1.0） |
| `always_on_top` | bool | `true` | 是否置顶显示 |
| `position` | string | `"top-right"` | 悬浮窗启动位置 |

### position 可选值

| 值 | 说明 |
|----|------|
| `"top-left"` | 左上角 |
| `"top-right"` | 右上角 |
| `"bottom-left"` | 左下角 |
| `"bottom-right"` | 右下角 |
| `"custom"` | 自定义（手动拖拽后自动切换） |

---

## 分类规则配置

```json
{
    "categories": {
        "游戏": {
            "icon": "🎮",
            "color": [255, 107, 107],
            "rules": [
                {"type": "process", "pattern": "steam.exe"},
                {"type": "title", "pattern": "*原神*"}
            ]
        },
        "办公": {
            "icon": "📊",
            "color": [78, 205, 196],
            "rules": [
                {"type": "process", "pattern": "EXCEL.EXE"}
            ]
        }
    }
}
```

### 分类配置项

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `icon` | string | 分类图标（emoji） |
| `color` | array | 分类颜色 `[R, G, B]` |
| `rules` | array | 匹配规则列表 |

### 规则类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `process` | 匹配进程名（不区分大小写） | `"chrome.exe"` |
| `title` | 匹配窗口标题（支持通配符） | `"*YouTube*"` |

### 通配符语法

| 符号 | 说明 | 示例 |
|------|------|------|
| `*` | 匹配任意字符 | `"*Chrome*"` 匹配包含 Chrome 的标题 |
| `?` | 匹配单个字符 | `"file?.txt"` 匹配 file1.txt, file2.txt 等 |

### 内置分类

WindowStatus 内置了 5 个分类：

| 分类 | 图标 | 颜色 |
|------|------|------|
| 游戏 | 🎮 | [255, 107, 107] |
| 办公 | 📊 | [78, 205, 196] |
| 摸鱼 | 🐟 | [255, 230, 109] |
| 开发 | 💻 | [168, 230, 207] |
| 工具 | 🔧 | [149, 165, 166] |

未匹配到任何规则的窗口会归类为"其他"。

---

## 提醒配置

```json
{
    "reminders": {
        "游戏": {
            "enabled": true,
            "interval_minutes": 60,
            "message": "已经连续玩了 {minutes} 分钟，该活动活动了！"
        },
        "办公": {
            "enabled": true,
            "interval_minutes": 45,
            "message": "已经连续办公 {minutes} 分钟，休息一下吧！"
        },
        "摸鱼": {
            "enabled": true,
            "interval_minutes": 30,
            "message": "已经连续摸鱼 {minutes} 分钟了，休息一下眼睛吧！"
        },
        "_default": {
            "enabled": false,
            "interval_minutes": 45,
            "message": "已经连续工作 {minutes} 分钟，喝口水休息一下！"
        }
    }
}
```

### 提醒配置项

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `enabled` | bool | 是否启用该分类的提醒 |
| `interval_minutes` | int | 提醒间隔（分钟） |
| `message` | string | 提醒消息模板 |

### 消息模板变量

| 变量 | 说明 |
|------|------|
| `{minutes}` | 已使用的分钟数 |

### 默认配置

`_default` 是未配置的分类的默认提醒设置。

---

## 插件配置

```json
{
    "plugins": {
        "monitor": true,
        "overlay": true,
        "tray": true,
        "stats": true,
        "rules": true,
        "about": true,
        "settings": true,
        "reminders": true,
        "desktop_pet": false
    }
}
```

### 插件列表

| 插件名 | 说明 | 默认状态 |
|--------|------|----------|
| `monitor` | 窗口监控 | 启用 |
| `overlay` | 悬浮窗 | 启用 |
| `tray` | 系统托盘 | 启用 |
| `stats` | 使用统计 | 启用 |
| `rules` | 分类规则 | 启用 |
| `about` | 关于窗口 | 启用 |
| `settings` | 设置窗口 | 启用 |
| `reminders` | 分类提醒 | 启用 |
| `desktop_pet` | 桌宠 | 禁用 |

### 启用/禁用插件

修改 `plugins` 配置后，需要重启程序才能生效。

---

## 桌宠配置

```json
{
    "desktop_pet": {
        "size": 128,
        "opacity": 1.0,
        "position": "bottom-right",
        "linkage": true,
        "animation_speed": 0.15
    }
}
```

### 桌宠配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `size` | int | `128` | 桌宠尺寸（像素） |
| `opacity` | float | `1.0` | 透明度（0.0-1.0） |
| `position` | string | `"bottom-right"` | 启动位置 |
| `linkage` | bool | `true` | 是否启用分类联动 |
| `animation_speed` | float | `0.15` | 动画帧切换速度（秒） |

### 联动模式

启用联动后，桌宠会根据当前窗口分类自动切换状态：

| 分类 | 桌宠状态 |
|------|----------|
| 游戏 | 兴奋（走路） |
| 办公 | 认真（坐下） |
| 摸鱼 | 打瞌睡（睡觉） |
| 开发 | 认真（坐下） |
| 工具 | 普通（待机） |

---

## 日志配置

```json
{
    "logging": {
        "level": "INFO",
        "file": "window_status.log",
        "max_size": 10485760,
        "backup_count": 3
    }
}
```

### 日志配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `level` | string | `"INFO"` | 日志级别 |
| `file` | string | `"window_status.log"` | 日志文件名 |
| `max_size` | int | `10485760` | 单个日志文件最大大小（字节，默认 10MB） |
| `backup_count` | int | `3` | 保留的旧日志文件数量 |

### 日志级别

| 级别 | 说明 |
|------|------|
| `DEBUG` | 调试信息（最详细） |
| `INFO` | 一般信息 |
| `WARNING` | 警告 |
| `ERROR` | 错误 |
| `CRITICAL` | 严重错误 |

---

## 配置迁移

WindowStatus 支持自动配置迁移：

- **v2.0 → v3.0**：旧版 `enabled_plugins` 列表自动转换为 `plugins` 字典
- **新增配置项**：自动合并默认配置，不会覆盖用户已有的配置

### 手动重置配置

如果配置文件损坏，可以删除 `config.json`，程序会自动创建默认配置：

```bash
# Windows
del %USERPROFILE%\.WindowStatus\config.json

# WSL
rm ~/.WindowStatus/config.json
```

---

## 完整配置示例

```json
{
    "version": "3.1.0",
    "opacity": 0.9,
    "always_on_top": true,
    "position": "top-right",
    "categories": {
        "游戏": {
            "icon": "🎮",
            "color": [255, 107, 107],
            "rules": [
                {"type": "process", "pattern": "steam.exe"},
                {"type": "process", "pattern": "EpicGamesLauncher.exe"}
            ]
        },
        "办公": {
            "icon": "📊",
            "color": [78, 205, 196],
            "rules": [
                {"type": "process", "pattern": "EXCEL.EXE"},
                {"type": "process", "pattern": "WINWORD.EXE"}
            ]
        }
    },
    "plugins": {
        "monitor": true,
        "overlay": true,
        "tray": true,
        "stats": true,
        "rules": true,
        "about": true,
        "settings": true,
        "reminders": true,
        "desktop_pet": false
    },
    "reminders": {
        "游戏": {"enabled": true, "interval_minutes": 60},
        "办公": {"enabled": true, "interval_minutes": 45},
        "摸鱼": {"enabled": true, "interval_minutes": 30},
        "_default": {"enabled": false, "interval_minutes": 45}
    },
    "desktop_pet": {
        "size": 128,
        "opacity": 1.0,
        "position": "bottom-right",
        "linkage": true,
        "animation_speed": 0.15
    },
    "logging": {
        "level": "INFO",
        "file": "window_status.log",
        "max_size": 10485760,
        "backup_count": 3
    }
}
```

---

更多信息请参考源代码中的 `kernel/config.py`。
