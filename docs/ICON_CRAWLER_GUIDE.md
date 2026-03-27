# 图标爬虫使用指南

这个爬虫可以从 iconfont.cn 免费图标库下载图标，用于美化你的小程序。

## 快速开始

### 1. 安装依赖

```bash
cd crawler
pip install -r requirements.txt
```

### 2. 运行爬虫

```bash
python src/icon_crawler.py
```

爬虫会自动：
- 搜索所需的图标（列表、添加、图表、设置）
- 下载灰色版本（未激活状态）
- 下载绿色版本（激活状态）
- 保存到小程序的图标目录：`../accounting-miniapp/src/static/icons/`

### 3. 重新编译小程序

```bash
cd ../accounting-miniapp
npm run dev:mp-weixin
```

### 4. 在微信开发者工具中查看效果

重新导入项目，现在应该能看到漂亮的图标了！

## 功能特性

- ✅ 自动搜索图标
- ✅ 下载 PNG 格式（40x40px）
- ✅ 支持自定义颜色
- ✅ 自动生成激活/未激活两个版本
- ✅ 直接保存到小程序目录
- ✅ 完整的日志记录

## 自定义下载

如果你想下载其他图标，可以修改 `icon_crawler.py` 中的 `icons_needed` 字典：

```python
icons_needed = {
    'list': '列表',      # 文件名: 搜索关键词
    'add': '添加',
    'chart': '图表',
    'settings': '设置',
    'user': '用户',      # 添加新图标
    'home': '首页'
}
```

## 自定义颜色

修改下载函数中的颜色参数：

```python
# 灰色版本
self.download_icon_png(icon_id, filename, size=40, color='7A7E83')

# 绿色版本
self.download_icon_png(icon_id, filename, size=40, color='3cc51f')

# 其他颜色示例：
# 红色: 'FF0000'
# 蓝色: '0000FF'
# 黑色: '000000'
```

## 自定义尺寸

修改 `size` 参数：

```python
# 40x40 像素（默认）
crawler.download_icons_for_miniapp(icons_needed, size=40)

# 80x80 像素
crawler.download_icons_for_miniapp(icons_needed, size=80)
```

## 下载的文件

运行后会在 `accounting-miniapp/src/static/icons/` 目录下生成：

- `list.png` - 列表图标（灰色）
- `list-active.png` - 列表图标（绿色）
- `add.png` - 添加图标（灰色）
- `add-active.png` - 添加图标（绿色）
- `chart.png` - 图表图标（灰色）
- `chart-active.png` - 图表图标（绿色）
- `settings.png` - 设置图标（灰色）
- `settings-active.png` - 设置图标（绿色）

## 日志文件

日志保存在 `logs/icon_crawler_YYYYMMDD.log`

## 常见问题

### Q: 下载失败怎么办？
A: 检查网络连接，确保能访问 iconfont.cn

### Q: 图标不满意怎么办？
A: 修改搜索关键词，或者手动从 iconfont.cn 选择图标 ID

### Q: 如何使用图标 ID 下载？
A: 修改代码，直接使用 `download_icon_png(icon_id, ...)`

### Q: 支持其他图标网站吗？
A: 目前只支持 iconfont.cn，其他网站需要修改代码

## 注意事项

1. 请遵守 iconfont.cn 的使用条款
2. 下载的图标仅供个人学习使用
3. 商业使用请确认图标的授权协议
4. 避免频繁请求，代码中已添加延迟

## 高级用法

### 批量下载多个图标

```python
# 创建爬虫实例
crawler = IconCrawler(output_dir='data/icons')

# 搜索图标
icons = crawler.search_icons_iconfont('购物车', page=1, page_size=20)

# 下载前 5 个图标
for i, icon in enumerate(icons[:5]):
    icon_id = icon['id']
    icon_name = f"cart_{i}"
    crawler.download_icon_png(icon_id, icon_name, size=40, color='000000')
    time.sleep(0.5)
```

### 下载 SVG 格式

```python
# SVG 格式可以无损缩放
crawler.download_icon_svg(icon_id, 'my_icon')
```

## 许可证

本爬虫代码采用 MIT 许可证。
下载的图标版权归原作者所有，请遵守相应的授权协议。
