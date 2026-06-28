# P1 Bug 修复方案：统计弹窗打开失败

## 前置条件

- 项目路径：`C:\Users\秋月\Desktop\WindowStatus`
- 代码规范：Python 3、PyQt5、注释用中文
- 测试运行：`python3 harness/checks.py && python3 -m pytest tests/ -v`
- 开工前必读：`plugins/stats/plugin.py`、`plugins/stats/dialog.py`、`plugins/common_styles.py`
- 禁止事项：不改其他文件，不重构

---

## Bug 1：COLOR_ERROR 未定义

**错误信息**：`NameError: name 'COLOR_ERROR' is not defined`

**位置**：`plugins/stats/dialog.py` line 143

**原因**：P1 重构时从 `common_styles` 导入了 `COLOR_ERROR`，但实际 `common_styles.py` 里没有定义 `COLOR_ERROR`。

**修复**：

### Task 1.1：在 common_styles.py 添加 COLOR_ERROR

**Files:**
- Modify: `plugins/common_styles.py`

**完成标准：**
- [ ] `COLOR_ERROR` 已定义（红色，oklch 0.6, 0.2, 25）
- [ ] 语法检查通过

**Step 1: 在状态色区域添加**

```python
# 状态色
COLOR_SUCCESS = oklch_to_qcolor(0.7, 0.15, 145)  # 绿色
COLOR_WARNING = oklch_to_qcolor(0.75, 0.15, 70)  # 黄色
COLOR_ERROR = oklch_to_qcolor(0.6, 0.2, 25)  # 红色
```

**Step 2: 验证**

Run: `python3 -m py_compile plugins/common_styles.py`
Expected: 无输出

---

## Bug 2：no such column: year

**错误信息**：`no such column: year`

**位置**：`plugins/stats/plugin.py` line 870-875

**原因**：`get_last_month_stats()` 查询 `monthly_stats` 表时用了 `WHERE year = ? AND month = ?`，但表结构只有 `month` 列（格式 "YYYY-MM"），没有 `year` 列。

**表结构**：
```sql
CREATE TABLE IF NOT EXISTS monthly_stats (
    month TEXT,           -- 格式 "YYYY-MM"
    category TEXT,
    total_duration INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    PRIMARY KEY (month, category)
)
```

**修复**：

### Task 2.1：修复 get_last_month_stats() SQL 查询

**Files:**
- Modify: `plugins/stats/plugin.py:870-875`

**完成标准：**
- [ ] SQL 查询用 `WHERE month = ?`，参数用 `strftime("%Y-%m")`
- [ ] 语法检查通过
- [ ] 打开统计弹窗不再报错

**Step 1: 修改 SQL 查询**

```python
# 原来（错误）
cursor.execute('''
    SELECT category, total_duration
    FROM monthly_stats
    WHERE year = ? AND month = ?
    ORDER BY total_duration DESC
''', (last_month_start.year, last_month_start.month))

# 改为（正确）
cursor.execute('''
    SELECT category, total_duration
    FROM monthly_stats
    WHERE month = ?
    ORDER BY total_duration DESC
''', (last_month_start.strftime("%Y-%m"),))
```

**Step 2: 验证**

Run: `python3 -m py_compile plugins/stats/plugin.py`
Expected: 无输出

---

## CC 注意事项

1. **只改方案里明确列出的代码** — 不要主动优化其他部分
2. **保留原有注释** — 不要删除已有的中文注释
3. **改动范围最小化** — 只改这两个 bug，不要扩大到其他文件
4. **不要自动 git commit** — 由主人决定何时提交

---

## 验收标准

1. `python3 harness/checks.py` 约束检查 0 违规
2. `python3 -m py_compile plugins/common_styles.py plugins/stats/dialog.py plugins/stats/plugin.py` 语法检查通过
3. 手动测试：打开统计弹窗不再报错

---

*编写时间：2026-06-28*
