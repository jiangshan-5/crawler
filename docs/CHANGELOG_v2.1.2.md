# 更新日志 v2.1.2

**发布日期**: 2026-04-03  
**版本**: 2.1.2  
**状态**: 稳定版

---

## 🎉 版本亮点

本次更新主要聚焦于**稳定性**和**用户体验**优化，修复了多个关键问题，并增强了停止控制功能。

---

## 🆕 新功能

### 1. 停止控制功能
- ⏹️ 支持随时停止爬取操作
- 📊 提供详细的 3 步停止流程日志
- ⏱️ 响应时间：1-30 秒（取决于当前操作）
- 💡 停止状态实时反馈

**使用方式**:
- 点击"⏹ 停止"按钮
- 查看日志了解停止进度
- 等待当前操作完成

**相关文档**: [停止按钮修复](docs/optimization_history/STOP_BUTTON_FIX.md)

---

## 🔧 优化改进

### 1. 资源清理优化
- 🧹 添加 `_closed` 标志防止重复清理
- 🔄 增强 `close()` 方法，清理所有资源：
  - Advanced crawler（浏览器实例）
  - 主 session（HTTP 连接）
  - 线程本地 session
  - 缓存数据
- 📝 添加详细的清理日志
- 🛡️ 改进错误处理，防止清理失败

**影响**: 防止内存泄漏，提高长时间运行的稳定性

**相关文档**: [资源清理优化](docs/optimization_history/RESOURCE_CLEANUP_OPTIMIZATION.md)

### 2. 停止机制增强
在关键循环中添加停止检查点：

- 📄 **多页面爬取循环** (`crawl_multiple_pages`)
  - 每次爬取新页面前检查停止标志
  - 立即中断循环，避免继续爬取

- 🖼️ **图片下载循环** (`save_images`)
  - 每完成一个图片下载后检查
  - 取消所有未开始的下载任务
  - 节省带宽和时间

- 📚 **小说章节爬取** (`_crawl_biquuge_chapters_parallel`)
  - 采样阶段停止检查
  - 重试采样阶段停止检查
  - 并发下载阶段停止检查
  - 三重保障，确保及时响应

**停止响应时间**:
- 循环迭代中：< 1 秒
- 并发任务中：1-10 秒
- 网络请求中：5-30 秒（受限于 requests 库）

**相关文档**: [停止机制增强](docs/optimization_history/STOP_MECHANISM_ENHANCEMENT.md)

### 3. 连接错误处理优化
- 🔌 优雅处理浏览器关闭时的连接错误
- ⚠️ 将 ConnectionResetError 等错误降级为警告
- 📊 改善日志输出的可读性
- 🛡️ 避免误报错误信息

**影响**: 减少无意义的错误日志，提高日志可读性

**相关文档**: [停止按钮修复](docs/optimization_history/STOP_BUTTON_FIX.md)

---

## 🐛 Bug 修复

### 1. 停止按钮无响应
**问题**: 点击停止按钮后，爬虫继续运行，无法停止

**原因**: 
- 缺少停止标志检查
- 没有在关键循环中检查停止状态

**解决方案**:
- 添加 `_stop_requested` 标志
- 在 GUI 的 6 个位置添加停止检查
- 在爬虫核心的关键循环中添加停止检查

**相关文档**: [停止按钮修复](docs/optimization_history/STOP_BUTTON_FIX.md)

### 2. Lambda 闭包 NameError
**问题**: 点击停止按钮时出现 `NameError: cannot access free variable 'exc' where it is not associated with a value`

**原因**: 
- Lambda 函数中的变量闭包问题
- 变量在回调执行时已超出作用域

**解决方案**:
- 使用默认参数捕获变量值
- 修改 `lambda: ...error_msg` 为 `lambda msg=error_msg: ...msg`
- 修复了 4 处 Lambda 闭包问题

**相关文档**: [Lambda 闭包修复](docs/optimization_history/LAMBDA_CLOSURE_FIX.md)

### 3. 资源泄漏问题
**问题**: 长时间运行后内存占用持续增长

**原因**:
- 资源未正确释放
- 重复清理导致错误
- 线程本地资源未清理

**解决方案**:
- 添加 `_closed` 标志防止重复清理
- 清理所有类型的资源
- 改进错误处理

**相关文档**: [资源清理优化](docs/optimization_history/RESOURCE_CLEANUP_OPTIMIZATION.md)

---

## 📚 文档更新

### 1. 创建优化历史文档文件夹
- 📁 创建 `docs/optimization_history/` 文件夹
- 📝 移动所有优化文档到该文件夹
- 🗂️ 便于代码回溯和历史追踪

### 2. 添加优化历史索引
- 📋 创建 `docs/optimization_history/README.md`
- 📅 包含所有优化的详细索引
- ⏰ 提供优化时间线
- 📖 提供文档模板和使用说明

### 3. 更新项目 README
- ✨ 添加"最近更新"部分
- 🔗 添加优化历史文档链接
- 📊 更新版本号到 2.1.2
- 🎯 更新功能特性列表
- 🐛 更新常见问题解答

---

## 📊 影响范围

### 修改的文件
1. `src/universal_crawler_v2.py` - 爬虫核心
2. `src/universal_crawler_gui.py` - GUI 界面
3. `src/advanced_crawler.py` - 高级爬虫
4. `README.md` - 项目说明
5. `docs/optimization_history/` - 优化历史文档（新增）

### 新增的文件
1. `docs/optimization_history/README.md` - 优化历史索引
2. `docs/optimization_history/RESOURCE_CLEANUP_OPTIMIZATION.md`
3. `docs/optimization_history/STOP_BUTTON_FIX.md`
4. `docs/optimization_history/LAMBDA_CLOSURE_FIX.md`
5. `docs/optimization_history/STOP_MECHANISM_ENHANCEMENT.md`
6. `CHANGELOG_v2.1.2.md` - 本更新日志

---

## 🔄 升级指南

### 从 v2.1.1 升级到 v2.1.2

**无需额外操作**，直接使用新版本即可。

**建议操作**:
1. 查看 [优化历史文档](docs/optimization_history/README.md) 了解所有改进
2. 测试停止按钮功能
3. 如遇到问题，查看对应的优化文档

---

## ⚠️ 已知限制

### 停止功能限制
1. **网络请求中无法立即停止**
   - 必须等待请求完成或超时（5-30秒）
   - 这是 Python requests 库的限制

2. **数据处理中无法立即停止**
   - 必须等待当前数据处理完成（1-5秒）
   - 数据处理是同步操作

3. **并发任务的取消限制**
   - 已开始的任务无法强制中断
   - 只能取消未开始的任务

### 解决方案
- 大多数情况下，停止会在 1-30 秒内完成
- 如需立即停止，可以关闭程序（不推荐）

---

## 🎯 下一步计划

### v2.2.0 计划功能
- [ ] 支持更多导出格式（Excel、XML）
- [ ] 添加代理支持
- [ ] 添加定时任务功能
- [ ] 断点续爬功能
- [ ] 爬取进度保存

### 长期计划
- [ ] 支持数据库存储
- [ ] 添加深色模式
- [ ] 支持自定义主题
- [ ] 智能检测（自动切换高级模式）
- [ ] 验证码识别
- [ ] 更多网站模板

---

## 🙏 致谢

感谢所有使用和反馈的用户！

---

## 📮 反馈

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- Email: 2874504001@qq.com

---

**完整更新历史**: [docs/optimization_history/README.md](docs/optimization_history/README.md)
