# 🕷️ 通用网页爬虫工具

一个功能强大、界面美观的通用网页爬虫工具，支持自定义 URL、CSS 选择器、爬取数量等配置。

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.6+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ 特性

- 🎨 **现代化 GUI 界面** - 美观易用的图形界面，支持响应式布局
- 🌐 **通用爬虫引擎** - 支持任意网页的数据提取
- ⚙️ **灵活配置** - 自定义 CSS 选择器、爬取模式、延迟等
- 📊 **实时日志** - 彩色日志输出，实时查看爬取进度
- 💾 **多格式导出** - 支持 JSON 和 CSV 格式
- 🔄 **响应式设计** - 窗口大小自适应，所有组件始终可见
- 🎯 **多源图标爬取** - 内置多个图标网站爬虫（Feather Icons、Heroicons 等）

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

### 基础使用

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
   - 保存格式：JSON 或 CSV
   - 保存位置：数据保存的文件夹

5. **开始爬取**
   - 点击"🚀 开始爬取"按钮
   - 在运行日志中查看进度
   - 在数据预览中查看结果

### CSS 选择器语法

- **提取文本**: `h1` 或 `div.title`
- **提取属性**: `a@href` 或 `img@src`
- **多层级**: `div.parent > span.child`
- **类选择器**: `.class-name`
- **ID选择器**: `#element-id`

### 示例配置

查看 `docs/ICONFONT_天气图标爬取指南.md` 了解完整的配置示例。

## 📚 文档

- [通用爬虫使用指南](docs/UNIVERSAL_CRAWLER_GUIDE.md)
- [GUI 界面使用说明](docs/UNIVERSAL_CRAWLER_UI_GUIDE.md)
- [iconfont.cn 爬取指南](docs/ICONFONT_天气图标爬取指南.md)
- [界面美化说明](GUI美化说明.md)
- [响应式布局说明](界面优化完成.md)

## 🛠️ 项目结构

```
crawler/
├── src/                          # 源代码目录
│   ├── universal_crawler.py      # 通用爬虫核心模块
│   ├── universal_crawler_gui.py  # GUI 界面（美化版）
│   ├── multi_source_icon_crawler.py  # 多源图标爬虫
│   ├── gui_crawler.py            # 图标爬虫 GUI
│   ├── apply_icons_to_miniapp.py # 图标应用工具
│   └── ...                       # 其他工具脚本
├── docs/                         # 文档目录
│   ├── UNIVERSAL_CRAWLER_GUIDE.md
│   ├── UNIVERSAL_CRAWLER_UI_GUIDE.md
│   └── ICONFONT_天气图标爬取指南.md
├── data/                         # 数据目录（爬取结果）
├── tests/                        # 测试目录
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

### 2. GUI 界面 (universal_crawler_gui.py)
- 现代化蓝色主题
- 响应式布局设计
- 实时日志输出
- 数据预览功能

### 3. 多源图标爬虫 (multi_source_icon_crawler.py)
- 支持 5+ 图标网站
- 批量下载图标
- 自动分类保存

### 4. 图标处理工具
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

```python
from universal_crawler import UniversalCrawler

# 创建爬虫实例
crawler = UniversalCrawler(
    base_url="https://example.com",
    output_dir="data/output"
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
```

### 批量爬取

参考 `src/main.py` 中的批量爬取示例。

## 🐛 常见问题

### 1. 没有提取到数据
- 检查 CSS 选择器是否正确
- 使用浏览器开发者工具验证选择器
- 确认页面是否需要登录
- 检查是否为动态加载内容

### 2. 被网站限制访问
- 增加请求延迟
- 减少爬取数量
- 分批次爬取
- 考虑使用代理

### 3. 程序运行错误
- 确认 Python 版本 >= 3.6
- 检查依赖是否完整安装
- 查看错误日志定位问题

## 📝 开发计划

- [ ] 支持更多导出格式（Excel、XML）
- [ ] 添加代理支持
- [ ] 支持 JavaScript 渲染页面
- [ ] 添加定时任务功能
- [ ] 支持数据库存储
- [ ] 添加深色模式
- [ ] 支持自定义主题

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

- GitHub: [你的 GitHub]
- Email: [你的邮箱]

---

⭐ 如果这个项目对你有帮助，请给个 Star！
