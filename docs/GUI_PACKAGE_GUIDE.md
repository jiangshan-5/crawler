# 图标爬虫 GUI 打包指南

## 快速开始

### 1. 测试 GUI 应用

```bash
cd crawler
python src/gui_crawler.py
```

GUI 界面应该会弹出，包含以下功能：
- 选择图标来源（Feather Icons、Heroicons 等）
- 输入搜索关键词
- 设置下载数量
- 选择输出目录
- 实时日志显示
- 应用到小程序功能

### 2. 安装打包工具

```bash
pip install pyinstaller
```

### 3. 打包成 EXE

#### 方法一：使用自动打包脚本（推荐）

```bash
python build_exe.py
```

这个脚本会：
- 自动检查并安装 PyInstaller
- 配置打包参数
- 生成单文件 EXE
- 显示文件大小和位置
- 提供清理选项

#### 方法二：手动打包

```bash
pyinstaller --name IconCrawler ^
  --onefile ^
  --windowed ^
  --clean ^
  --noconfirm ^
  --add-data "src/multi_source_icon_crawler.py;." ^
  --add-data "src/apply_icons_to_miniapp.py;." ^
  --hidden-import PIL._tkinter_finder ^
  --hidden-import requests ^
  --hidden-import bs4 ^
  src/gui_crawler.py
```

### 4. 运行 EXE

打包完成后，EXE 文件位于：
```
crawler/dist/IconCrawler.exe
```

双击运行即可使用。

## 打包说明

### 打包参数解释

- `--name IconCrawler`: 输出文件名
- `--onefile`: 打包成单个 EXE 文件
- `--windowed`: 不显示控制台窗口（纯 GUI）
- `--clean`: 清理临时文件
- `--noconfirm`: 不询问确认
- `--add-data`: 添加依赖的 Python 文件
- `--hidden-import`: 添加隐式导入的模块

### 文件大小

预计 EXE 文件大小：30-50 MB

这是因为包含了：
- Python 解释器
- Tkinter GUI 库
- requests、BeautifulSoup、Pillow 等依赖
- 所有爬虫逻辑

### 兼容性

- Windows 7 及以上
- 不需要安装 Python
- 不需要安装任何依赖
- 独立运行

## 使用指南

### GUI 界面说明

1. **配置区域（左侧）**
   - 选择图标来源：勾选要爬取的网站
   - 搜索关键词：每行一个关键词
   - 下载数量：每个关键词下载几个图标
   - 输出目录：图标保存位置

2. **日志区域（右侧）**
   - 实时显示爬取进度
   - 彩色日志（INFO/SUCCESS/WARNING/ERROR）
   - 自动滚动

3. **操作按钮**
   - 🚀 开始爬取：开始下载图标
   - ⏹ 停止：中止当前爬取
   - 📱 应用到小程序：将图标应用到项目

### 推荐来源

✅ **Feather Icons**（推荐）
- 开源免费
- 简洁美观
- 100% 成功率

✅ **Heroicons**（推荐）
- Tailwind CSS 团队开发
- 开源免费
- 100% 成功率

⚠️ **其他来源**
- Iconmonstr、Icons8、Flaticon 可能需要 API 密钥或有访问限制

### 应用到小程序

1. 点击"应用到小程序"按钮
2. 选择图标来源（推荐 Feather）
3. 输入要应用的图标名称（如：list add chart settings）
4. 点击"应用"
5. 重新编译小程序：
   ```bash
   cd ../accounting-miniapp
   npm run dev:mp-weixin
   ```
6. 在微信开发者工具中查看效果

## 常见问题

### Q: 杀毒软件报毒怎么办？
A: PyInstaller 打包的 EXE 可能被误报，请添加到信任列表。

### Q: EXE 启动很慢？
A: 首次启动需要解压临时文件，正常现象。

### Q: 下载失败怎么办？
A: 
- 检查网络连接
- 尝试使用 Feather Icons 或 Heroicons（最稳定）
- 查看日志区域的错误信息

### Q: 如何减小 EXE 文件大小？
A: 可以使用 `--onedir` 代替 `--onefile`，会生成一个文件夹，但启动更快。

## 开发说明

### 项目结构

```
crawler/
├── src/
│   ├── gui_crawler.py              # GUI 主程序
│   ├── multi_source_icon_crawler.py # 爬虫核心
│   └── apply_icons_to_miniapp.py   # 图标应用工具
├── build_exe.py                     # 打包脚本
├── requirements.txt                 # Python 依赖
└── dist/
    └── IconCrawler.exe             # 打包后的 EXE
```

### 依赖库

```
requests>=2.31.0
beautifulsoup4>=4.12.0
Pillow>=10.0.0
lxml>=4.9.0
```

### 修改和重新打包

1. 修改 `src/gui_crawler.py` 或其他源文件
2. 运行 `python build_exe.py` 重新打包
3. 测试新的 EXE

## 分发

打包完成后，只需要分发 `dist/IconCrawler.exe` 文件即可。

用户无需安装：
- Python
- 任何依赖库
- 任何配置

双击即可运行！
