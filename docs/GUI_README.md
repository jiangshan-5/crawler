# 图标爬虫 GUI 工具 🎨

一个简单易用的图形界面工具，用于从多个免费图标网站爬取图标并应用到你的小程序项目。

## 快速开始 ⚡

### 方法 1：双击运行（推荐）

```
双击 run_gui.bat
```

### 方法 2：命令行运行

```bash
cd crawler
python src/gui_crawler.py
```

## 功能特点 ✨

- 🎯 **多源爬取** - 支持 5 个免费图标网站
- 🖼️ **实时预览** - 彩色日志实时显示进度
- 🚀 **一键应用** - 直接应用到小程序项目
- 🎨 **自动转换** - SVG 自动转换为 PNG（40x40）
- 🔄 **多线程** - 后台下载，界面不卡顿
- 💾 **批量处理** - 支持多个关键词批量下载

## 界面说明 📱

### 左侧：配置区域

1. **选择图标来源**
   - ✅ Feather Icons（推荐）
   - ✅ Heroicons（推荐）
   - ⚠️ Iconmonstr
   - ⚠️ Icons8
   - ⚠️ Flaticon

2. **搜索关键词**
   - 每行一个关键词
   - 默认：list、add、chart、settings

3. **下载数量**
   - 每个关键词下载几个图标
   - 范围：1-10

4. **输出目录**
   - 图标保存位置
   - 默认：data/icons_comparison

### 右侧：日志区域

- 实时显示爬取进度
- 彩色日志（INFO/SUCCESS/WARNING/ERROR）
- 自动滚动到最新消息

### 底部：操作按钮

- 🚀 **开始爬取** - 开始下载图标
- ⏹ **停止** - 中止当前爬取
- 📱 **应用到小程序** - 将图标应用到项目

## 使用流程 📋

### 1. 爬取图标

1. 启动 GUI 工具
2. 勾选图标来源（推荐 Feather + Heroicons）
3. 输入关键词（每行一个）
4. 设置下载数量
5. 点击"🚀 开始爬取"
6. 等待完成提示

### 2. 应用到小程序

1. 点击"📱 应用到小程序"
2. 选择图标来源（推荐 Feather）
3. 输入要应用的图标名称（空格分隔）
   - 例如：`list add chart settings`
4. 点击"应用"
5. 等待转换完成

### 3. 查看效果

```bash
cd ../accounting-miniapp
npm run dev:mp-weixin
```

在微信开发者工具中重新导入项目，查看新图标！

## 推荐配置 ⭐

### 最佳图标来源

**Feather Icons** 和 **Heroicons**
- ✅ 100% 开源免费
- ✅ 简洁美观
- ✅ 100% 成功率
- ✅ SVG 格式

### 常用关键词

| 关键词 | 说明 | Feather | Heroicons |
|--------|------|---------|-----------|
| list | 列表 | ✅ | ✅ |
| add | 添加 | ✅ (plus) | ✅ (plus) |
| chart | 图表 | ✅ (bar-chart-2) | ✅ (chart-bar) |
| settings | 设置 | ✅ | ✅ (cog) |
| home | 首页 | ✅ | ✅ |
| user | 用户 | ✅ | ✅ |
| menu | 菜单 | ✅ | ✅ (bars-3) |
| search | 搜索 | ✅ | ✅ (magnifying-glass) |

## 输出结果 📦

### 爬取结果

```
data/icons_comparison/
├── feather/
│   ├── list.svg
│   ├── add.svg
│   ├── chart.svg
│   └── settings.svg
├── heroicons/
│   ├── list.svg
│   ├── add.svg
│   ├── chart.svg
│   └── settings.svg
├── icon_comparison_results.json
└── comparison.html
```

### 应用结果

```
accounting-miniapp/src/static/icons/
├── list.png              # 灰色版本（未激活）
├── list-active.png       # 绿色版本（激活）
├── add.png
├── add-active.png
├── chart.png
├── chart-active.png
├── settings.png
└── settings-active.png
```

## 打包成 EXE 📦

如果你想分享给没有 Python 环境的朋友：

### 1. 安装打包工具

```bash
pip install pyinstaller
```

### 2. 运行打包脚本

```bash
python build_exe.py
```

### 3. 获取 EXE

```
dist/IconCrawler.exe
```

双击即可运行，无需 Python！

## 故障排除 🔧

### 问题 1：GUI 无法启动

**症状**：双击 run_gui.bat 后闪退

**解决方法**：
```bash
# 检查 Python 是否安装
python --version

# 安装依赖
pip install -r requirements.txt

# 手动运行
python src/gui_crawler.py
```

### 问题 2：下载失败

**症状**：日志显示 ERROR

**解决方法**：
1. 检查网络连接
2. 只勾选 Feather Icons 和 Heroicons
3. 关闭 VPN（如果开启）
4. 减少下载数量

### 问题 3：应用失败

**症状**：点击"应用到小程序"后报错

**解决方法**：
1. 确保已经爬取了图标
2. 检查小程序目录路径是否正确
3. 确保图标名称正确（不要加 .svg 后缀）

### 问题 4：图标显示不正确

**症状**：小程序中图标显示异常

**解决方法**：
1. 重新编译小程序
2. 清除微信开发者工具缓存
3. 重新导入项目

## 技术细节 🔬

### 依赖库

- **requests** - HTTP 请求
- **beautifulsoup4** - HTML 解析
- **Pillow** - 图像处理
- **lxml** - XML 解析
- **tkinter** - GUI 框架（Python 标准库）

### 图标转换

1. 下载 SVG 文件
2. 解析 SVG 内容
3. 使用 PIL 绘制图标
4. 生成两个版本：
   - 灰色 (#7A7E83) - 未激活
   - 绿色 (#3cc51f) - 激活
5. 保存为 40x40 PNG

### 支持的图标类型

- ✅ 列表图标（横线）
- ✅ 添加图标（加号）
- ✅ 图表图标（柱状图）
- ✅ 设置图标（齿轮）
- ✅ 首页图标（房子）
- ✅ 用户图标（人形）
- ✅ 搜索图标（放大镜）
- ✅ 心形图标

## 文件说明 📄

```
crawler/
├── src/
│   ├── gui_crawler.py              # GUI 主程序
│   ├── multi_source_icon_crawler.py # 爬虫核心
│   └── apply_icons_to_miniapp.py   # 图标应用工具
├── run_gui.bat                      # Windows 启动脚本
├── build_exe.py                     # EXE 打包脚本
├── requirements.txt                 # Python 依赖
├── GUI_README.md                    # 本文件
├── GUI_PACKAGE_GUIDE.md            # 打包详细指南
└── GUI_CRAWLER_SUMMARY.md          # 完成总结
```

## 更新日志 📝

### v1.0 (2024-03-27)
- ✅ 初始版本发布
- ✅ 支持 5 个图标来源
- ✅ GUI 界面
- ✅ 实时日志
- ✅ 一键应用到小程序
- ✅ 支持打包成 EXE

## 许可证 📜

MIT License - 自由使用、修改和分发

## 支持 💬

如有问题，请查看：
- `GUI_PACKAGE_GUIDE.md` - 详细打包指南
- `GUI_CRAWLER_SUMMARY.md` - 完整功能说明
- `QUICK_START.md` - 命令行版本使用指南

---

**享受爬取图标的乐趣！** 🎨✨
