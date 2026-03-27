# 快速开始 - 多源图标爬虫

## 🚀 一分钟上手

### 1. 最简单的用法

```bash
cd crawler
python src/multi_source_icon_crawler.py --sources feather
```

这会从 Feather Icons 下载默认的 4 个图标（list, add, chart, settings）。

### 2. 指定你想要的图标

```bash
python src/multi_source_icon_crawler.py --sources feather --keywords home menu user
```

下载 home、menu、user 三个图标。

### 3. 从多个来源对比

```bash
python src/multi_source_icon_crawler.py --sources feather heroicons --keywords heart
```

从 Feather 和 Heroicons 各下载一个心形图标，方便对比选择。

## 📋 常用命令

### 为小程序下载导航图标

```bash
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords home search cart user settings
```

### 下载社交媒体图标

```bash
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords heart star share message like
```

### 下载操作图标

```bash
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords add edit delete save upload download
```

### 下载文件图标

```bash
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords file folder image video music
```

## 🎯 推荐配置

### 配置 1: 快速下载（推荐新手）

```bash
python src/multi_source_icon_crawler.py --sources feather --limit 1
```

- 只用 Feather Icons
- 每个关键词 1 个图标
- 速度最快

### 配置 2: 对比选择（推荐设计师）

```bash
python src/multi_source_icon_crawler.py --sources feather heroicons --limit 2
```

- 两个来源对比
- 每个关键词 2 个选择
- 方便挑选最佳

### 配置 3: 全面收集（推荐图标库）

```bash
python src/multi_source_icon_crawler.py \
  --sources feather heroicons \
  --keywords home user search settings menu cart heart star share message \
  --limit 3
```

- 10 个常用图标
- 每个 3 个选择
- 共 60 个图标

## 📖 参数说明

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| --sources | -s | 指定来源 | `--sources feather` |
| --keywords | -k | 指定关键词 | `--keywords home user` |
| --limit | -l | 下载数量 | `--limit 5` |
| --output | -o | 输出目录 | `--output my_icons` |
| --help | -h | 查看帮助 | `--help` |

## 🌟 可用的图标来源

| 来源 | 代码 | 特点 | 推荐度 |
|------|------|------|--------|
| Feather Icons | `feather` | 极简、开源 | ⭐⭐⭐⭐⭐ |
| Heroicons | `heroicons` | 专业、开源 | ⭐⭐⭐⭐⭐ |
| Iconmonstr | `iconmonstr` | 免费 | ⭐⭐⭐ |
| Icons8 | `icons8` | 部分免费 | ⭐⭐ |
| Flaticon | `flaticon` | 需要登录 | ⭐ |

**推荐使用**: `feather` 和 `heroicons`（开源，成功率 100%）

## 💡 实用技巧

### 技巧 1: 批量下载

创建一个文本文件 `icons.txt`，列出所有需要的图标：
```
home
user
search
settings
menu
cart
heart
star
```

然后运行：
```bash
python src/multi_source_icon_crawler.py --sources feather --keywords $(cat icons.txt)
```

### 技巧 2: 保存到不同目录

```bash
# 导航图标
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords home user search \
  --output data/nav_icons

# 操作图标
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords add edit delete \
  --output data/action_icons
```

### 技巧 3: 查看帮助

```bash
python src/multi_source_icon_crawler.py --help
```

## 📂 下载的文件在哪里？

默认保存在：
```
crawler/data/icons_comparison/
├── feather/          # Feather Icons 的 SVG 文件
├── heroicons/        # Heroicons 的 SVG 文件
└── comparison.html   # 对比页面
```

## 🔍 如何查看下载的图标？

### 方法 1: 浏览器查看

1. 打开文件资源管理器
2. 进入 `crawler/data/icons_comparison/feather/`
3. 双击 SVG 文件

### 方法 2: VS Code 预览

1. 在 VS Code 中打开 SVG 文件
2. 右键 → "Open Preview"

### 方法 3: 对比页面

打开 `data/icons_comparison/comparison.html`（如果生成成功）

## ❓ 常见问题

### Q: 下载失败怎么办？

A: 使用推荐的来源：
```bash
python src/multi_source_icon_crawler.py --sources feather heroicons
```

### Q: 如何下载更多图标？

A: 增加关键词：
```bash
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords home user search settings menu cart heart star share message
```

### Q: SVG 如何转 PNG？

A: 使用在线工具：
- https://cloudconvert.com/svg-to-png
- https://svgtopng.com/

### Q: 如何应用到小程序？

A: 
1. 转换 SVG 为 PNG（40x40）
2. 修改颜色（灰色 #7A7E83，绿色 #3cc51f）
3. 复制到 `accounting-miniapp/src/static/icons/`
4. 重新编译：`npm run dev:mp-weixin`

## 🎉 完整示例

```bash
# 1. 下载图标
cd crawler
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords list add chart settings \
  --limit 1

# 2. 查看下载的图标
cd data/icons_comparison/feather
ls

# 3. 在浏览器中打开查看
start list.svg
start add.svg
start chart.svg
start settings.svg
```

## 📚 更多信息

- 详细使用指南：`CRAWLER_USAGE_GUIDE.md`
- 多源爬取总结：`MULTI_SOURCE_CRAWL_SUMMARY.md`
- 查看图标指南：`VIEW_ICONS_GUIDE.md`

---

**开始使用吧！** 🚀

最简单的命令：
```bash
python src/multi_source_icon_crawler.py --sources feather
```
