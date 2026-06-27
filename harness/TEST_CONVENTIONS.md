# WindowStatus 测试规范

> 所有测试必须遵循此规范，确保一致性和可维护性。

---

## 1. 测试框架

- **框架**：pytest
- **运行命令**：`python -m pytest tests/ -v`
- **覆盖率**：暂不要求，逐步提升

---

## 2. 文件组织

```
tests/
├── test_event_bus.py           # EventBus 单元测试
├── test_config.py              # Config 单元测试
├── test_desktop_pet.py         # 桌宠逻辑测试
├── test_desktop_pet_position.py # 桌宠位置测试
├── test_rules.py               # 分类规则测试
├── test_state_machine.py       # 状态机测试
└── test_utils.py               # 工具函数测试
```

**命名规范**：
- 测试文件：`test_<module>.py`
- 测试类：`Test<Feature>`
- 测试方法：`test_<scenario>_<expected>`

---

## 3. 测试原则

### 3.1 独立性
- 每个测试必须能独立运行
- 不依赖其他测试的执行顺序
- 使用 setUp/tearDown 清理状态

### 3.2 可重复
- 测试结果必须一致
- 不依赖外部状态（网络、文件系统特定状态）
- 使用 mock 隔离外部依赖

### 3.3 快速
- 单个测试应在 1 秒内完成
- 避免真实的 QTimer 等待（用 mock）

---

## 4. PyQt5 测试特殊处理

### 4.1 QApplication 初始化
```python
import sys
from PyQt5.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    """创建全局 QApplication"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
```

### 4.2 Widget 测试
- 使用 `qapp` fixture 确保 QApplication 存在
- 测试 Widget 属性而非视觉效果
- 使用 `QTest` 模拟用户交互（如需要）

### 4.3 事件循环
- 避免在测试中启动真实事件循环
- 使用 `QApplication.processEvents()` 处理待处理事件
- QTimer 用 mock 替代

---

## 5. Mock 策略

### 5.1 Kernel Mock
```python
@pytest.fixture
def mock_kernel():
    """模拟 Kernel 对象"""
    kernel = MagicMock()
    kernel.event_bus = MagicMock()
    kernel.config = MagicMock()
    return kernel
```

### 5.2 EventBus Mock
```python
@pytest.fixture
def mock_event_bus():
    """模拟 EventBus"""
    bus = MagicMock()
    bus.emit = MagicMock()
    bus.on = MagicMock()
    return bus
```

---

## 6. 测试数据

### 6.1 临时目录
```python
@pytest.fixture
def temp_dir(tmp_path):
    """使用 pytest 内置 tmp_path"""
    return tmp_path
```

### 6.2 配置数据
```python
@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        "plugins": {"monitor": True, "overlay": True},
        "categories": {...}
    }
```

---

## 7. 断言规范

### 7.1 属性断言
```python
assert widget.isVisible() is True
assert widget.width() == 100
assert widget.windowTitle() == "Expected Title"
```

### 7.2 事件断言
```python
mock_event_bus.emit.assert_called_once_with(
    "CATEGORY_MATCHED",
    category="游戏",
    title="Test Game"
)
```

### 7.3 异常断言
```python
with pytest.raises(ValueError, match="invalid config"):
    config.load("invalid.json")
```

---

## 8. 运行检查

### 8.1 语法检查
```bash
python -m py_compile kernel/core.py
python -m py_compile plugins/monitor/plugin.py
```

### 8.2 测试运行
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_event_bus.py -v

# 运行特定测试方法
python -m pytest tests/test_event_bus.py::TestEventBus::test_emit -v
```

---

## 9. 约束检查集成

测试运行前自动执行 `checks.py`：
- 约束检查失败 → 阻塞测试运行
- 约束检查通过 → 正常运行测试

```bash
python harness/checks.py && python -m pytest tests/ -v
```

---

*基于 pytest 最佳实践和项目特点*
*更新时间：2026-06-27*
