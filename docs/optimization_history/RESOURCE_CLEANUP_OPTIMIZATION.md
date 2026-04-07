# 资源清理逻辑优化说明

## ✅ 已完成的优化

### 1. UniversalCrawlerV2 类优化

#### 改进点：
- ✅ 添加 `_closed` 标志防止重复清理
- ✅ 增强 `close()` 方法，清理所有资源
- ✅ 清理线程局部存储（thread-local sessions）
- ✅ 改进异常处理，确保清理过程不会失败
- ✅ 添加详细的日志记录
- ✅ 改进 `__del__` 方法，添加警告日志
- ✅ 改进 `__exit__` 方法，确保上下文管理器正常工作

#### 优化后的代码结构：

```python
def __init__(self, ...):
    self._closed = False  # 添加关闭标志
    # ... 其他初始化代码

def close(self):
    """Close all resources and cleanup."""
    if getattr(self, '_closed', False):
        return  # 防止重复清理
    
    self._closed = True
    logger.info(f'[cleanup] closing crawler instance {id(self)}')
    
    # 1. 关闭高级爬虫
    if self.advanced_crawler:
        try:
            self.advanced_crawler.close()
        except Exception as e:
            logger.warning(f'[cleanup] failed to close advanced crawler: {e}')
        finally:
            self.advanced_crawler = None
    
    # 2. 关闭主 session
    if getattr(self, 'session', None):
        try:
            self.session.close()
        except Exception as e:
            logger.warning(f'[cleanup] failed to close main session: {e}')
        finally:
            self.session = None
    
    # 3. 清理线程局部存储
    if hasattr(self, '_thread_local'):
        try:
            if hasattr(self._thread_local, 'session'):
                try:
                    self._thread_local.session.close()
                except Exception as e:
                    logger.warning(f'[cleanup] failed to close thread-local session: {e}')
                delattr(self._thread_local, 'session')
        except Exception as e:
            logger.warning(f'[cleanup] failed to cleanup thread-local storage: {e}')
    
    # 4. 清理缓存
    try:
        self._primed_domains.clear()
    except Exception as e:
        logger.warning(f'[cleanup] failed to clear caches: {e}')

def __del__(self):
    """Destructor to ensure cleanup."""
    try:
        if not getattr(self, '_closed', True):
            logger.warning(f'[cleanup] crawler {id(self)} not explicitly closed')
            self.close()
    except Exception as e:
        logger.error(f'[cleanup] error in __del__: {e}')

def __exit__(self, exc_type, exc_val, exc_tb):
    """Context manager exit with cleanup."""
    self.close()
    return False
```

### 2. AdvancedCrawler 类优化（需要手动应用）

由于文件编码问题，以下是 `advanced_crawler.py` 的优化代码，需要手动替换：

```python
def close(self, force=False):
    """Close browser and cleanup resources."""
    if not self.driver:
        return

    if self.reuse_browser and not force and self._release_shared_driver():
        return

    driver = self.driver
    self.driver = None
    self._pool_attached = False
    entry = self.__class__._shared_pool.get(self._shared_key)
    if entry and entry.get("driver") is driver:
        self.__class__._shared_pool.pop(self._shared_key, None)

    try:
        driver.quit()
        logger.info(f"[advanced] browser engine closed ({self.engine_name})")
    except Exception as e:
        logger.error(f"[advanced] browser close failed: {e}")
    finally:
        driver = None  # 确保引用被清除

def __enter__(self):
    self.start()
    return self

def __exit__(self, exc_type, exc_val, exc_tb):
    """Context manager exit with cleanup."""
    try:
        self.close()
    except Exception as e:
        logger.error(f"[advanced] error during context exit: {e}")
    return False

def __del__(self):
    """Destructor to ensure cleanup."""
    try:
        if self.driver is not None:
            logger.warning(f"[advanced] browser not explicitly closed, cleaning up in __del__")
            self.close(force=True)
    except Exception as e:
        logger.error(f"[advanced] error in __del__: {e}")
```

## 📊 优化效果

### 改进前的问题：
1. ❌ Session 可能未正确关闭
2. ❌ 浏览器实例可能泄漏
3. ❌ 线程局部存储未清理
4. ❌ 缺少重复清理保护
5. ❌ 异常可能导致清理失败
6. ❌ 缺少详细的清理日志

### 改进后的优势：
1. ✅ 防止重复清理（`_closed` 标志）
2. ✅ 所有资源都被正确清理
3. ✅ 异常不会中断清理过程
4. ✅ 详细的日志记录便于调试
5. ✅ 支持上下文管理器（`with` 语句）
6. ✅ 析构函数作为最后的保障

## 🎯 使用建议

### 推荐用法（使用上下文管理器）：

```python
# 方式 1：使用 with 语句（推荐）
with UniversalCrawlerV2(base_url='https://example.com') as crawler:
    results = crawler.crawl_list_page(...)
    # 自动清理资源

# 方式 2：手动管理
crawler = UniversalCrawlerV2(base_url='https://example.com')
try:
    results = crawler.crawl_list_page(...)
finally:
    crawler.close()  # 确保清理
```

### 不推荐的用法：

```python
# ❌ 不推荐：依赖析构函数清理
crawler = UniversalCrawlerV2(base_url='https://example.com')
results = crawler.crawl_list_page(...)
# 没有显式调用 close()，依赖 __del__
```

## 🔍 测试验证

可以通过以下方式验证资源清理：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 测试 1：正常清理
with UniversalCrawlerV2(base_url='https://example.com') as crawler:
    pass
# 应该看到 "[cleanup] closing crawler instance" 日志

# 测试 2：异常情况下的清理
try:
    with UniversalCrawlerV2(base_url='https://example.com') as crawler:
        raise Exception("Test exception")
except:
    pass
# 应该看到清理日志，即使发生异常

# 测试 3：重复清理保护
crawler = UniversalCrawlerV2(base_url='https://example.com')
crawler.close()
crawler.close()  # 第二次调用应该立即返回，不会重复清理
```

## 📝 后续优化建议

1. **添加资源监控**：
   - 跟踪打开的连接数
   - 监控内存使用
   - 记录资源泄漏

2. **添加超时机制**：
   - 清理操作添加超时
   - 避免清理过程卡死

3. **添加资源池**：
   - Session 复用
   - 连接池管理
   - 浏览器实例池

4. **添加健康检查**：
   - 定期检查资源状态
   - 自动清理僵尸资源

## ✅ 总结

本次优化显著改进了爬虫的资源管理：
- 防止资源泄漏
- 提高程序稳定性
- 便于问题排查
- 符合 Python 最佳实践

建议在生产环境中使用上下文管理器（`with` 语句）来确保资源正确清理。
