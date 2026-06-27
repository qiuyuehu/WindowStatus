# WindowStatus Harness 工程规范

> Harness = 模型之外的一切约束、规范、护栏
> 核心理解：Agent = Model + Harness

---

## 一、Harness 目录结构

```
harness/
├── CONSTRAINTS.md      # 代码约束（自动检查）
├── DECISIONS.md        # 决策档案（只增不改）
├── TEST_CONVENTIONS.md # 测试规范
├── SPEC.md             # 本文件（Harness 工程规范）
├── checks.py           # 约束自动检查脚本
└── runner.py           # 测试入口（约束检查 + 单元测试）
```

---

## 二、核心原则

### 2.1 约束先行
- 代码约束必须在写代码之前定义
- 约束检查失败 → 阻塞测试运行（不是警告）
- 约束来源于踩坑记录，每条约束都有"原因"

### 2.2 决策留痕
- 所有重要技术决策记录在 DECISIONS.md
- 决策只增不改，历史决策保留
- 格式：D-XXX: 标题（日期）+ 决策 + 原因 + 结果

### 2.3 测试驱动
- 重要功能先写测试再写代码
- 测试文件放在 `tests/` 目录
- 测试必须独立、可重复、快速

### 2.4 自动化验证
- `checks.py` 自动检查约束
- `runner.py` 集成约束检查 + 测试运行
- pre-commit hook 调用 checks.py（失败拒绝提交）

---

## 三、约束检查机制

### 3.1 检查流程
```
checks.py 运行
    ↓
扫描所有 .py 文件（排除 harness/ 和 __pycache__）
    ↓
运行所有检查函数
    ↓
有违规？
    ├── 是 → 输出违规详情，返回 exit(1)
    └── 否 → 输出"所有检查通过"，返回 exit(0)
```

### 3.2 白名单机制
- 历史代码文件可以加入白名单
- 白名单文件跳过部分约束检查
- 白名单文件列表在 CONSTRAINTS.md 和 checks.py 中维护

### 3.3 检查项
| 编号 | 约束 | 检查函数 | 严重级别 |
|------|------|----------|----------|
| 1.1 | Widget 创建时机 | check_widget_creation_timing | 违规 |
| 1.2 | Qt.Tool 拖拽限制 | check_qt_tool_drag | 违规 |
| 1.3 | QDesktopWidget 禁用 | check_qdesktop_widget | 违规 |
| 2.3 | 事件处理器 kwargs | check_event_handler_kwargs | 违规 |
| 5.1 | 空 catch 块 | check_empty_except | 违规 |

---

## 四、使用方式

### 4.1 只运行约束检查
```bash
python harness/checks.py
python harness/checks.py --verbose
```

### 4.2 只运行测试
```bash
python harness/runner.py --tests
# 或
python -m pytest tests/ -v
```

### 4.3 运行检查 + 测试
```bash
python harness/runner.py
```

### 4.4 pre-commit hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python harness/checks.py
if [ $? -ne 0 ]; then
    echo "约束检查失败，拒绝提交。"
    exit 1
fi
```

---

## 五、维护指南

### 5.1 添加新约束
1. 在 CONSTRAINTS.md 添加约束描述
2. 在 checks.py 添加检查函数
3. 在 run_checks() 中注册检查函数
4. 测试检查函数是否正确识别违规

### 5.2 更新白名单
1. 在 CONSTRAINTS.md 的白名单部分添加文件
2. 在 checks.py 的 WHITELIST_FILES 列表添加
3. 说明为什么加入白名单（历史原因、重构中等）

### 5.3 记录决策
1. 在 DECISIONS.md 添加新决策
2. 格式：D-XXX: 标题（日期）
3. 包含：决策、原因、方案、结果

---

## 六、与其他规范的关系

### 6.1 与 SPEC.md 的关系
- SPEC.md：项目图纸，描述项目是什么
- harness/SPEC.md：Harness 工程规范，描述如何约束项目开发
- 两者同等重要，开工前必须都读

### 6.2 与 CONSTRAINTS.md 的关系
- CONSTRAINTS.md：具体约束内容
- harness/SPEC.md：约束检查机制和流程
- CONSTRAINTS.md 是 harness/SPEC.md 的执行细节

---

## 七、踩坑记录

### H-001: checks.py 直接调用 sys.exit 会中断 runner
**问题**：checks.py 的 run_checks() 直接调用 sys.exit(1)，导致 runner.py 也被中断
**解决**：run_checks() 返回结果对象，由 main() 决定是否 exit

### H-002: 白名单机制必须双向维护
**问题**：只在 CONSTRAINTS.md 写白名单，checks.py 没有对应列表
**解决**：CONSTRAINTS.md 和 checks.py 的 WHITELIST_FILES 必须同步

---

*基于 FlashLauncher 项目 harness 实践*
*更新时间：2026-06-27*
