# Bug修复：高级模式依赖检测问题

## 问题描述

用户在使用自动安装功能安装 `undetected-chromedriver` 后，重启程序仍然提示"未安装"，需要重新下载。

## 问题分析

### 根本原因

1. **Python 3.12+ 移除了 distutils 模块**
   - `undetected-chromedriver` 依赖 `distutils` 模块
   - Python 3.12+ 已将 `distutils` 从标准库中移除
   - 需要先安装 `setuptools` 来提供 `distutils` 兼容层

2. **模块导入时机问题**
   - 原实现在模块导入时检测依赖可用性并缓存结果
   - 即使安装了依赖，重启前缓存的状态仍然是"不可用"
   - 模块重载（`importlib.reload()`）虽然能刷新模块，但增加了复杂性

### 用户环境

- Python 版本：3.14.3
- 操作系统：Windows
- 问题表现：安装成功后重启仍提示未安装

## 解决方案

### 1. 修复安装流程（已实现）

在 `universal_crawler_gui.py` 的 `_install_dependency()` 方法中：

```python
def _install_dependency(self):
    """在后台线程中安装依赖"""
    import subprocess
    
    try:
        # 步骤 1: 安装 setuptools（为 Python 3.12+ 提供 distutils）
        self.log("步骤 1/2: 安装 setuptools...", "INFO")
        process1 = subprocess.Popen(
            [sys.executable, '-m', 'pip', 'install', 'setuptools'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 实时输出日志
        for line in process1.stdout:
            line = line.strip()
            if line:
                self.log(f"  {line}", "INFO")
        
        return_code1 = process1.wait()
        
        if return_code1 != 0:
            stderr1 = process1.stderr.read()
            self.log(f"setuptools 安装失败: {stderr1}", "WARNING")
            # 继续尝试安装 undetected-chromedriver
        else:
            self.log("✓ setuptools 安装成功", "SUCCESS")
        
        # 步骤 2: 安装 undetected-chromedriver
        self.log("步骤 2/2: 安装 undetected-chromedriver...", "INFO")
        process2 = subprocess.Popen(
            [sys.executable, '-m', 'pip', 'install', 'undetected-chromedriver'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # ... 后续处理
```

**关键改进**：
- 分两步安装：先 `setuptools`，再 `undetected-chromedriver`
- 即使 `setuptools` 安装失败也继续尝试（可能已安装）
- 实时显示安装进度

### 2. 改进依赖检测机制（本次修复）

#### 修改 `advanced_crawler.py`

**原实现**（静态检测）：
```python
try:
    import undetected_chromedriver as uc
    ADVANCED_MODE_AVAILABLE = True
except ImportError:
    ADVANCED_MODE_AVAILABLE = False

def is_advanced_mode_available():
    return ADVANCED_MODE_AVAILABLE
```

**新实现**（动态检测）：
```python
def _check_availability():
    """检查依赖是否可用"""
    try:
        import undetected_chromedriver as uc
        return True
    except ImportError as e:
        logger.warning(f"undetected-chromedriver 未安装，高级模式不可用: {e}")
        return False

ADVANCED_MODE_AVAILABLE = _check_availability()

def is_advanced_mode_available():
    """检查高级模式是否可用（动态检测）"""
    # 每次调用都重新检测，确保能检测到新安装的依赖
    try:
        import undetected_chromedriver as uc
        return True
    except ImportError:
        return False
```

**关键改进**：
- `is_advanced_mode_available()` 每次调用都动态检测
- 不依赖模块级缓存的状态
- 能够立即检测到新安装的依赖

#### 简化 GUI 检测逻辑

**原实现**（复杂的模块重载）：
```python
def check_advanced_mode_availability(self):
    try:
        import importlib
        import sys
        
        if 'advanced_crawler' in sys.modules:
            import advanced_crawler
            importlib.reload(advanced_crawler)
            from advanced_crawler import is_advanced_mode_available
        else:
            from advanced_crawler import is_advanced_mode_available
        
        # ... 检测逻辑
```

**新实现**（简洁直接）：
```python
def check_advanced_mode_availability(self):
    try:
        from advanced_crawler import is_advanced_mode_available
        
        if is_advanced_mode_available():
            self.advanced_tip_label.config(text="✓ 可用", foreground="green")
        else:
            self.advanced_tip_label.config(
                text="✗ 需要安装: pip install undetected-chromedriver",
                foreground="red"
            )
            self.advanced_mode_var.set(False)
    except Exception as e:
        self.advanced_tip_label.config(text="✗ 不可用", foreground="red")
        self.advanced_mode_var.set(False)
```

**关键改进**：
- 移除了复杂的模块重载逻辑
- 依赖 `is_advanced_mode_available()` 的动态检测
- 代码更简洁、更易维护

同样简化了 `on_advanced_mode_toggle()` 方法。

## 技术细节

### 为什么动态检测有效？

1. **Python 的 import 缓存机制**
   - Python 会缓存已导入的模块在 `sys.modules` 中
   - 但每次 `import` 语句执行时，Python 会先检查模块是否存在
   - 如果模块不存在（ImportError），不会影响后续的 import 尝试

2. **动态检测的优势**
   - 每次调用都尝试导入，能立即检测到新安装的包
   - 不需要手动重载模块
   - 代码更简单，逻辑更清晰

3. **性能考虑**
   - `import` 语句在模块已缓存时非常快（纳秒级）
   - 只有在模块不存在时才会有额外开销（try-except）
   - 对于 GUI 应用，这个开销完全可以忽略

### Python 3.12+ distutils 问题

从 Python 3.12 开始，`distutils` 被移除：
- **官方说明**：PEP 632 – Deprecate distutils module
- **替代方案**：使用 `setuptools` 提供的兼容层
- **影响**：依赖 `distutils` 的旧包需要先安装 `setuptools`

## 测试验证

### 测试场景 1：全新安装

```bash
# 1. 确保依赖未安装
pip uninstall -y undetected-chromedriver setuptools

# 2. 启动程序，勾选高级模式
# 3. 选择"自动安装"
# 4. 等待安装完成
# 5. 重启程序
# 6. 勾选高级模式 -> 应该直接启用，不再提示安装
```

### 测试场景 2：动态检测

```python
# 测试动态检测功能
import sys
sys.path.insert(0, 'crawler/src')

from advanced_crawler import is_advanced_mode_available

# 第一次检测
print(f"Test 1: {is_advanced_mode_available()}")

# 第二次检测（应该返回相同结果）
print(f"Test 2: {is_advanced_mode_available()}")
```

预期输出：
```
Test 1: True
Test 2: True
```

### 测试场景 3：Python 版本兼容性

在不同 Python 版本测试：
- Python 3.10：应该正常工作（distutils 仍在标准库）
- Python 3.12+：需要 setuptools，自动安装流程会处理
- Python 3.14：已验证工作正常

## 相关文件

- `crawler/src/advanced_crawler.py` - 核心依赖检测逻辑
- `crawler/src/universal_crawler_gui.py` - GUI 检测和安装逻辑
- `crawler/requirements.txt` - 依赖声明

## 后续建议

1. **更新 requirements.txt**
   ```
   setuptools>=65.0.0  # Python 3.12+ 需要
   undetected-chromedriver>=3.5.0
   ```

2. **添加 Python 版本检查**
   ```python
   import sys
   if sys.version_info >= (3, 12):
       # 提示用户可能需要 setuptools
       pass
   ```

3. **改进错误提示**
   - 如果安装失败，提供更详细的错误信息
   - 针对 Python 3.12+ 用户，明确说明 setuptools 的作用

## 版本信息

- 修复版本：v2.0.2
- 修复日期：2026-03-27
- 影响范围：高级模式依赖检测和自动安装功能
