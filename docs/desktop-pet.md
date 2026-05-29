# 桌宠插件文档

## 概述

桌宠插件（desktop_pet）是WindowStatus的一个扩展插件，它在Overlay悬浮窗旁边显示一个可爱的二次元角色，根据当前窗口分类切换不同的姿态。

## 功能特性

- **状态切换**：根据窗口分类自动切换桌宠姿态
  - 坐着：办公、开发、学习
  - 兴奋：游戏、娱乐、社交
  - 打瞌睡：摸鱼、空闲
  - 待机：其他
- **位置配置**：支持在Overlay上方或下方显示
- **跟随移动**：桌宠会跟随Overlay一起移动
- **图片缓存**：使用缓存机制提高性能
- **事件驱动**：通过事件系统与Overlay插件解耦通信

## 配置说明

### 默认配置

```python
DEFAULT_CONFIG = {
    "enabled": False,       # 默认关闭
    "position": "top",      # 桌宠在Overlay的上方或下方
}
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| enabled | bool | False | 是否启用桌宠插件 |
| position | str | "top" | 桌宠位置，可选值："top"（上方）、"bottom"（下方） |

## 使用方法

### 启用插件

1. 打开WindowStatus设置
2. 切换到"插件管理"标签
3. 勾选"desktop_pet"插件
4. 重启应用

### 配置位置

1. 打开WindowStatus设置
2. 切换到"通用"标签
3. 在"桌宠位置"下拉框中选择"上方"或"下方"
4. 点击"保存"

## 素材要求

桌宠素材需要放在 `plugins/desktop_pet/assets/` 目录下，包含以下文件：

| 文件名 | 说明 |
|--------|------|
| sit.png | 坐着姿态 |
| walk.png | 兴奋姿态 |
| sleep.png | 打瞌睡姿态 |
| idle.png | 待机姿态 |
| drag.png | 拖拽姿态（暂未使用） |

### 素材规格

- 格式：PNG
- 尺寸：256x256 像素
- 背景：透明
- 风格：二次元动漫风格

## 架构设计

### 插件依赖

- 依赖：overlay（Overlay悬浮窗插件）

### 事件监听

| 事件 | 说明 |
|------|------|
| CATEGORY_MATCHED | 窗口分类匹配完成 |
| OVERLAY_POSITION_CHANGED | Overlay位置变化 |
| OVERLAY_MOVED | Overlay被拖动 |

### 类结构

```
DesktopPetPlugin (plugin.py)
├── on_load() - 插件加载
├── on_enable() - 插件启用
├── on_disable() - 插件禁用
├── on_unload() - 插件卸载
├── _create_pet() - 创建桌宠
├── _position_next_to_overlay() - 计算桌宠位置
├── _follow_overlay() - 跟随Overlay移动
├── _on_category_matched() - 处理分类事件
├── _on_overlay_position_changed() - 处理位置变化
├── _on_overlay_moved() - 处理拖动事件
└── set_pet_position() - 设置桌宠位置

DesktopPetWidget (widget.py)
├── __init__() - 初始化
├── _load_images() - 加载图片（带缓存）
├── _set_state() - 设置状态
├── update_category() - 更新分类
├── paintEvent() - 绘制桌宠
├── showEvent() - 显示事件
├── hideEvent() - 隐藏事件
└── moveEvent() - 移动事件
```

## 开发说明

### 添加新状态

1. 在 `STATE_TO_IMAGE` 中添加新状态和图片文件名的映射
2. 在 `CATEGORY_TO_STATE` 中添加分类到新状态的映射
3. 准备对应的图片素材

### 修改位置计算

位置计算逻辑在 `_position_next_to_overlay()` 方法中：

```python
# 水平居中
x = overlay_x + (overlay_width - pet_size.width()) // 2

if position == "top":
    # 桌宠在Overlay上方，重叠一点
    y = overlay_y - pet_size.height() + 50
else:  # bottom
    # 桌宠在Overlay下方，重叠一点
    y = overlay_y + overlay_height - 50
```

重叠量（50像素）可以根据需要调整。

## 测试

运行单元测试：

```bash
cd WindowStatus
python -m pytest tests/test_desktop_pet.py -v
```

## 已知问题

1. 桌宠插件默认关闭，需要手动开启
2. 拖拽状态（drag）暂未使用
3. 图片缓存在插件卸载时不会自动清理

## 更新日志

### v2.0.0 (2026-05-29)

- 重构为事件驱动架构
- 添加图片缓存机制
- 添加配置验证
- 添加插件依赖声明
- 添加单元测试
- 完善文档

### v1.0.0 (2026-05-28)

- 初始版本
- 支持基本的状态切换
- 支持位置配置
