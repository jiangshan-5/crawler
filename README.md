# 🕷️ 通用网页爬虫工具

一个功能强大、界面美观的通用网页爬虫工具，支持自定义 URL、CSS 选择器、爬取数量等配置。

**🎯 快速模板功能！** 内置常见网站模板，一键应用配置，10秒开始爬取！

![Version](https://img.shields.io/badge/version-2.1.1-blue)
![Python](https://img.shields.io/badge/python-3.6+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## ✨ 特性

- 🎨 **现代化 GUI 界面** - 美观易用的图形界面，支持响应式布局
- 🎯 **快速模板功能** - 内置 Flaticon、GitHub、Hacker News 等常见网站模板，一键应用
- 🌐 **通用爬虫引擎** - 支持任意网页的数据提取
- 🛡️ **高级模式** - 绕过 Cloudflare/DataDome 等反爬虫系统，支持 JavaScript 动态渲染
- ⚙️ **灵活配置** - 自定义 CSS 选择器、爬取模式、延迟等
- 📊 **实时日志** - 彩色日志输出，实时查看爬取进度
- 💾 **多格式导出** - 支持 JSON 和 CSV 格式
- 🔄 **响应式设计** - 窗口大小自适应，所有组件始终可见
- 🎯 **多源图标爬取** - 内置多个图标网站爬虫（Feather Icons、Heroicons 等）
- 🔄 **智能降级** - 高级模式不可用时自动切换到标准模式
- 🚀 **一键自动安装** - 高级模式依赖自动安装，无需手动配置

## 📸 界面预览

### 主界面
- 蓝色现代化主题
- 左侧配置区域 + 右侧日志预览
- 实时数据预览

### 功能区域
- URL 配置：支持列表页面和单个页面模式
- 字段选择器：可视化管理 CSS 选择器
- 爬取控制：数量、延迟、格式、保存位置
- 运行日志：彩色日志，实时输出
- 数据预览：JSON 格式预览前 5 条数据

## 🚀 快速开始

### 环境要求

- Python 3.6+
- Windows 10/11 (其他系统未测试)

### 安装依赖

```bash
cd crawler
pip install -r requirements.txt
```

**可选：安装高级模式（反反爬虫）**

**方式1: 自动安装（推荐）⭐**
1. 启动工具后勾选"高级模式"
2. 在弹出对话框中点击【是】
3. 等待自动安装完成
4. 重启程序

**方式2: 手动安装**
```bash
pip install setuptools
pip install undetected-chromedriver
```

> 高级模式可以绕过Cloudflare、DataDome等反爬虫系统，支持JavaScript动态渲染

### 运行程序

**方式 1：Python 直接运行**
```bash
python src/universal_crawler_gui.py
```

**方式 2：使用批处理文件 (Windows)**
```bash
run_universal_crawler.bat
```

## 📖 使用指南

### 快速开始：使用模板

**最简单的方式！** 使用内置模板，10秒开始爬取：

1. **启动工具**
   ```bash
   run_universal_crawler.bat
   ```

2. **选择模板**
   - 在"🎯 快速模板"下拉框中选择网站（如 Flaticon、GitHub Trending）
   - 点击【📋 应用】按钮

3. **开始爬取**
   - 直接点击【🚀 开始爬取】
   - 或根据需要修改 URL 和配置

**内置模板**：
- ✅ Flaticon 图标网站
- ✅ GitHub 趋势
- ✅ Hacker News
- ✅ Product Hunt

详细说明请查看 [快速模板使用说明](docs/快速模板使用说明.md)

---

### 基础使用（手动配置）

1. **输入目标 URL**
   - 在"目标 URL"框中输入要爬取的网页地址

2. **选择爬取模式**
   - 📋 列表页面：爬取多个项目（如商品列表、文章列表）
   - 📄 单个页面：爬取单个页面的数据

3. **配置选择器**
   - 点击"➕ 添加"按钮添加字段
   - 字段名：数据的名称（如 title、price）
   - CSS选择器：提取数据的选择器（如 h1、span.price）
   - 说明：可选的字段说明

4. **设置爬取参数**
   - 爬取数量：要爬取的条目数量
   - 请求延迟：每次请求之间的延迟（秒）
   - 🛡️ 高级模式：勾选以启用反反爬虫功能（可选）
   - 保存格式：JSON 或 CSV
   - 保存位置：数据保存的文件夹

5. **开始爬取**
   - 点击"🚀 开始爬取"按钮
   - 在运行日志中查看进度
   - 在数据预览中查看结果

### 高级模式使用

**何时使用高级模式？**
- ✅ 网站有 Cloudflare、DataDome 等反爬虫保护
- ✅ 内容通过 JavaScript 动态加载
- ✅ 标准模式无法获取数据
- ❌ 简单静态网站（不需要，标准模式更快）

### 使用步骤：**
1. ~~安装依赖：`pip install undetected-chromedriver`~~ **不再需要！**
2. ~~重启爬虫工具~~
3. 勾选"🛡️ 高级模式"选项
4. **首次使用时点击【是】自动安装** ⭐
5. 等待安装完成并重启
6. 再次勾选高级模式开始爬取

**性能对比：**
| 特性 | 标准模式 | 高级模式 |
|------|---------|---------|
| 速度 | ⚡⚡⚡⚡⚡ 极快 | ⚡⚡ 较慢 |
| JS渲染 | ❌ | ✅ |
| 反爬虫绕过 | ❌ | ✅ |
| 成功率 | 60-70% | 95-99% |

详细说明请查看 [高级模式使用指南](docs/高级模式使用指南.md)

### CSS 选择器语法

- **提取文本**: `h1` 或 `div.title`
- **提取属性**: `a@href` 或 `img@src`
- **多层级**: `div.parent > span.child`
- **类选择器**: `.class-name`
- **ID选择器**: `#element-id`

### 示例配置

**使用模板（推荐）**：
1. 选择"Flaticon 图标网站"模板
2. 点击【应用】
3. 点击【开始爬取】

**手动配置**：
查看 [Flaticon 测试用例](docs/FLATICON_测试用例.md) 了解完整的配置示例。

## 📚 文档

**📖 [完整文档索引](docs/文档索引.md)** - 查看所有文档  
**📝 [更新日志](docs/CHANGELOG.md)** - 查看版本历史

### 快速开始
- [快速模板使用说明](docs/快速模板使用说明.md) ⭐ 推荐
- [快速开始（基础）](docs/QUICK_START.md)
- [快速开始（高级模式）](docs/QUICK_START_高级模式.md)
- [使用说明（含自动安装）](docs/使用说明_自动安装.md)

### 使用指南
- [通用爬虫使用指南](docs/UNIVERSAL_CRAWLER_GUIDE.md)
- [高级模式使用指南](docs/高级模式使用指南.md)
- [GUI 界面使用说明](docs/GUI_README.md)

### 测试用例
- [Flaticon 测试用例](docs/FLATICON_测试用例.md)
- [GitHub 测试用例](docs/简单测试用例_GitHub.md)
- [选择器调试指南](docs/FLATICON_选择器调试指南.md)

### 技术文档
- [反反爬虫技术研究](docs/反反爬虫技术研究与升级方案.md)
- [自动安装功能说明](docs/自动安装功能说明.md)
- [模板修复说明](docs/模板修复说明_Flaticon.md)
- [实现完成总结](docs/实现完成总结.md)

### 升级说明
- [升级完成](docs/升级完成.md)
- [新功能通知](docs/新功能通知.txt)

## 🛠️ 项目结构

```
crawler/
├── src/                          # 源代码目录
│   ├── universal_crawler.py      # 通用爬虫核心模块（支持高级模式）
│   ├── universal_crawler_gui.py  # GUI 界面（美化版 + 高级模式 + 快速模板）
│   ├── advanced_crawler.py       # 高级爬虫模块（反反爬虫）
│   ├── website_templates.py      # 网站模板配置
│   ├── multi_source_icon_crawler.py  # 多源图标爬虫
│   ├── apply_icons_to_miniapp.py # 图标应用工具
│   └── ...                       # 其他工具脚本
├── docs/                         # 文档目录
│   ├── 快速模板使用说明.md       # 模板功能说明 ⭐
│   ├── 高级模式使用指南.md       # 高级模式详细说明
│   ├── 反反爬虫技术研究与升级方案.md  # 技术研究文档
│   ├── FLATICON_测试用例.md      # Flaticon 测试文档
│   └── ...                       # 其他文档
├── data/                         # 数据目录（爬取结果）
├── test/                         # 测试脚本
├── requirements.txt              # Python 依赖
├── README.md                     # 项目说明
├── .gitignore                    # Git 忽略文件
└── run_universal_crawler.bat     # Windows 启动脚本
```

## 🎯 功能模块

### 1. 通用爬虫 (universal_crawler.py)
- 支持列表页面和单页面爬取
- 自定义 CSS 选择器
- 支持属性提取（@href、@src 等）
- 统计信息输出
- 支持高级模式切换

### 2. 高级爬虫 (advanced_crawler.py)
- 使用 undetected-chromedriver 绕过反爬虫
- 支持 JavaScript 动态渲染
- 模拟真实浏览器行为
- 自动处理页面加载和等待
- 支持无头模式（headless）

### 3. GUI 界面 (universal_crawler_gui.py)
- 现代化蓝色主题
- 响应式布局设计
- 实时日志输出
- 数据预览功能
- 高级模式开关和状态提示
- 快速模板功能

### 4. 网站模板 (website_templates.py)
- 预配置常见网站选择器
- 一键应用模板配置
- 支持自定义扩展

### 5. 多源图标爬虫 (multi_source_icon_crawler.py)
- 支持 5+ 图标网站
- 批量下载图标
- 自动分类保存

### 6. 图标处理工具
- SVG 转 PNG
- 图标颜色转换
- 批量应用到项目

## ⚙️ 配置说明

### 爬取模式

**列表页面模式**：
- 适用于：商品列表、文章列表、图标列表等
- 需要配置：列表容器选择器 + 字段选择器

**单个页面模式**：
- 适用于：详情页、单篇文章等
- 只需配置：字段选择器

### 延迟设置

建议根据目标网站调整：
- 小型网站：1-2 秒
- 中型网站：2-3 秒
- 大型网站：3-5 秒
- 有反爬机制：5+ 秒

## 🔧 高级功能

### 命令行使用

**标准模式：**
```python
from universal_crawler import UniversalCrawler

# 创建爬虫实例
crawler = UniversalCrawler(
    base_url="https://example.com",
    output_dir="data/output",
    use_advanced_mode=False  # 标准模式
)

# 爬取列表页面
results = crawler.crawl_list_page(
    url="https://example.com/list",
    list_selector="div.item",
    field_selectors={
        "title": "h2",
        "link": "a@href",
        "image": "img@src"
    },
    max_items=50
)

# 保存数据
crawler.save_to_json(results, "output")
crawler.close()  # 释放资源
```

**高级模式（反反爬虫）：**
```python
from universal_crawler import UniversalCrawler

# 创建爬虫实例（启用高级模式）
crawler = UniversalCrawler(
    base_url="https://protected-site.com",
    output_dir="data/output",
    use_advanced_mode=True  # 启用高级模式
)

# 爬取受保护的网站
results = crawler.crawl_list_page(
    url="https://protected-site.com/list",
    list_selector="div.item",
    field_selectors={
        "title": "h2",
        "link": "a@href"
    },
    max_items=20
)

# 保存数据
crawler.save_to_json(results, "output")
crawler.close()  # 重要：关闭浏览器
```

**使用上下文管理器（推荐）：**
```python
from advanced_crawler import AdvancedCrawler

# 自动管理资源
with AdvancedCrawler(headless=True) as crawler:
    soup = crawler.fetch_page("https://protected-site.com")
    # 处理数据...
# 自动关闭浏览器
```

### 批量爬取

参考 `src/main.py` 中的批量爬取示例。

## 🐛 常见问题

### 1. 没有提取到数据
- 检查 CSS 选择器是否正确
- 使用浏览器开发者工具验证选择器
- 确认页面是否需要登录
- 🆕 **尝试启用高级模式**（可能是 JS 动态加载）

### 2. 被网站限制访问
- 增加请求延迟
- 减少爬取数量
- 分批次爬取
- 🆕 **启用高级模式绕过反爬虫**

### 3. 高级模式不可用
- ~~运行 `pip install undetected-chromedriver`~~ **不再需要！**
- **勾选高级模式时点击【是】自动安装** ⭐
- 等待安装完成后重启工具
- 如果自动安装失败，手动运行：
  ```bash
  pip install setuptools
  pip install undetected-chromedriver
  ```

### 4. 高级模式启动慢
- 首次使用会下载 ChromeDriver（正常现象）
- 后续使用会使用缓存，速度正常

### 5. 程序运行错误
- 确认 Python 版本 >= 3.6
- 检查依赖是否完整安装
- 查看错误日志定位问题
- 运行 `python test_advanced_mode.py` 测试

## 📝 开发计划

- [x] 支持 JavaScript 渲染页面（高级模式）✅
- [x] 绕过反爬虫系统（高级模式）✅
- [x] 快速模板功能 ✅
- [x] 一键自动安装依赖 ✅
- [ ] 支持更多导出格式（Excel、XML）
- [ ] 添加代理支持
- [ ] 添加定时任务功能
- [ ] 支持数据库存储
- [ ] 添加深色模式
- [ ] 支持自定义主题
- [ ] 智能检测（自动切换高级模式）
- [ ] 验证码识别
- [ ] 更多网站模板

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👨‍💻 作者

[你的名字]

## 🙏 致谢

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析
- [Requests](https://requests.readthedocs.io/) - HTTP 请求
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - GUI 框架

## 📮 联系方式

- GitHub: [https://github.com/jiangshan-5]
- Email: [2874504001@qq.com]

---

⭐ 如果这个项目对你有帮助，请给个 Star！
