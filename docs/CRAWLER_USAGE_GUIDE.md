# 多源图标爬虫使用指南

## 功能特性

✅ 支持多个免费图标网站
✅ 可指定爬取的来源
✅ 可自定义搜索关键词
✅ 可控制下载数量
✅ 自动生成对比页面

## 快速开始

### 基本用法

```bash
# 爬取所有来源的默认图标
python src/multi_source_icon_crawler.py
```

## 命令行参数

### --sources / -s (指定来源)

选择要爬取的图标网站：

```bash
# 只爬取 Feather Icons
python src/multi_source_icon_crawler.py --sources feather

# 爬取 Feather 和 Heroicons
python src/multi_source_icon_crawler.py --sources feather heroicons

# 爬取所有来源（默认）
python src/multi_source_icon_crawler.py --sources all
```

**可用的来源：**
- `flaticon` - Flaticon.com（需要登录，可能失败）
- `icons8` - Icons8.com（部分免费，API 可能变化）
- `iconmonstr` - Iconmonstr.com（完全免费）
- `feather` - Feather Icons（开源，推荐）✅
- `heroicons` - Heroicons（开源，推荐）✅
- `all` - 所有来源（默认）

### --keywords / -k (指定关键词)

自定义要搜索的图标关键词：

```bash
# 搜索单个关键词
python src/multi_source_icon_crawler.py --keywords home

# 搜索多个关键词
python src/multi_source_icon_crawler.py --keywords home user search menu

# 默认关键词（如果不指定）
# list, add, chart, settings
```

### --limit / -l (下载数量)

控制每个关键词下载的图标数量：

```bash
# 每个关键词下载 5 个图标
python src/multi_source_icon_crawler.py --limit 5

# 每个关键词下载 1 个图标（最快）
python src/multi_source_icon_crawler.py --limit 1

# 默认是 3 个
```

### --output / -o (输出目录)

指定图标保存的目录：

```bash
# 保存到自定义目录
python src/multi_source_icon_crawler.py --output my_icons

# 默认目录
# data/icons_comparison
```

## 使用示例

### 示例 1: 只爬取开源图标库

```bash
python src/multi_source_icon_crawler.py --sources feather heroicons
```

**说明**：只爬取 Feather Icons 和 Heroicons，这两个是开源的，成功率最高。

### 示例 2: 为导航栏下载图标

```bash
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords home search user settings menu
```

**说明**：从 Feather Icons 下载导航栏常用的 5 个图标。

### 示例 3: 快速下载单个图标

```bash
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords heart \
  --limit 1
```

**说明**：从 Feather Icons 快速下载 1 个心形图标。

### 示例 4: 批量下载多种图标

```bash
python src/multi_source_icon_crawler.py \
  --sources feather heroicons \
  --keywords home user search settings menu cart heart star \
  --limit 2
```

**说明**：从两个来源各下载 8 个关键词的图标，每个关键词 2 个，共 32 个图标。

### 示例 5: 保存到指定目录

```bash
python src/multi_source_icon_crawler.py \
  --sources feather \
  --keywords list add chart \
  --output ../accounting-miniapp/temp_icons
```

**说明**：直接保存到小程序的临时目录。

## 输出结果

### 目录结构

```
data/icons_comparison/
├── feather/              # Feather Icons
│   ├── list.svg
│   ├── add.svg
│   └── ...
├── heroicons/            # Heroicons
│   ├── list.svg
│   ├── add.svg
│   └── ...
├── comparison.html       # 对比页面
└── icon_comparison_results.json  # 结果数据
```

### 查看结果

1. **打开对比页面**
   ```bash
   # 在浏览器中打开
   start data/icons_comparison/comparison.html
   ```

2. **查看 SVG 文件**
   - 进入对应的来源目录
   - 双击 SVG 文件在浏览器中查看

3. **查看结果数据**
   ```bash
   # 查看 JSON 格式的详细结果
   cat data/icons_comparison/icon_comparison_results.json
   ```

## 推荐配置

### 配置 1: 快速获取高质量图标（推荐）

```bash
python src/multi_source_icon_crawler.py \
  --sources feather heroicons \
  --keywords list add chart settings \
  --limit 1
```

**优点**：
- 只爬取开源库，成功率 100%
- 速度快
- 图标质量高

### 配置 2: 获取更多选择

```bash
python src/multi_source_icon_crawler.py \
  --sources feather heroicons \
  --limit 3
```

**优点**：
- 每个关键词有 3 个选择
- 可以对比不同风格

### 配置 3: 尝试所有来源

```bash
python src/multi_source_icon_crawler.py --sources all
```

**优点**：
- 尝试所有可能的来源
- 获取最多的图标

**缺点**：
- 部分来源可能失败
- 速度较慢

## 常见问题

### Q1: 某些来源下载失败？

**A:** 这是正常的，部分网站有反爬虫机制或需要登录。推荐只使用 `feather` 和 `heroicons`：

```bash
python src/multi_source_icon_crawler.py --sources feather heroicons
```

### Q2: 如何下载更多图标？

**A:** 增加关键词和数量：

```bash
python src/multi_source_icon_crawler.py \
  --keywords home user search settings menu cart heart star \
  --limit 5
```

### Q3: 下载的是 SVG，如何转换为 PNG？

**A:** 使用在线工具：
- https://cloudconvert.com/svg-to-png
- https://svgtopng.com/

或者使用我提供的转换脚本（需要额外依赖）。

### Q4: 如何查看帮助信息？

**A:** 运行：

```bash
python src/multi_source_icon_crawler.py --help
```

### Q5: 爬取速度太慢？

**A:** 减少来源和数量：

```bash
python src/multi_source_icon_crawler.py \
  --sources feather \
  --limit 1
```

## 高级用法

### 批量处理脚本

创建一个批处理文件 `download_icons.bat`：

```batch
@echo off
echo 下载导航图标...
python src/multi_source_icon_crawler.py --sources feather --keywords home user search settings

echo 下载操作图标...
python src/multi_source_icon_crawler.py --sources feather --keywords add edit delete save

echo 下载社交图标...
python src/multi_source_icon_crawler.py --sources feather --keywords heart star share message

echo 完成！
pause
```

### Python 脚本调用

```python
import subprocess

# 定义要下载的图标组
icon_groups = {
    'navigation': ['home', 'user', 'search', 'settings'],
    'actions': ['add', 'edit', 'delete', 'save'],
    'social': ['heart', 'star', 'share', 'message']
}

for group_name, keywords in icon_groups.items():
    print(f"下载 {group_name} 图标...")
    cmd = [
        'python', 'src/multi_source_icon_crawler.py',
        '--sources', 'feather',
        '--keywords', *keywords,
        '--output', f'data/icons_{group_name}'
    ]
    subprocess.run(cmd)
```

## 最佳实践

1. **优先使用开源库**
   ```bash
   --sources feather heroicons
   ```

2. **明确关键词**
   - 使用英文关键词
   - 使用常见的图标名称
   - 避免过于复杂的描述

3. **控制下载数量**
   - 开发阶段：`--limit 1`（快速）
   - 选择阶段：`--limit 3`（对比）
   - 收集阶段：`--limit 5`（全面）

4. **合理使用延迟**
   - 代码中已内置延迟
   - 避免频繁请求同一网站

5. **保存结果**
   - 下载后及时备份
   - 记录使用的关键词和来源

## 总结

这个爬虫工具可以帮你：
- ✅ 快速获取多个来源的图标
- ✅ 灵活控制爬取范围
- ✅ 自动生成对比页面
- ✅ 支持批量下载

推荐配置：
```bash
python src/multi_source_icon_crawler.py \
  --sources feather heroicons \
  --keywords list add chart settings \
  --limit 2
```

这样可以快速获取高质量的图标，并有多个选择进行对比！
