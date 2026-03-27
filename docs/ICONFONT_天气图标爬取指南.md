# iconfont.cn 天气图标爬取配置指南

## 第一步：找到天气图标页面

1. 打开浏览器访问：https://www.iconfont.cn
2. 在搜索框输入"天气"或"weather"
3. 找到你想要的图标集合页面
4. 复制完整的 URL（例如：https://www.iconfont.cn/collections/detail?spm=xxx&cid=xxxxx）

## 第二步：分析页面结构（使用浏览器开发者工具）

### 如何查看页面结构：
1. 在图标列表页面按 `F12` 打开开发者工具
2. 点击左上角的"选择元素"按钮（或按 `Ctrl+Shift+C`）
3. 鼠标悬停在图标上，查看 HTML 结构

### 典型的 iconfont.cn 页面结构：

```html
<!-- 列表容器 -->
<ul class="icon-glyph-list">
  <!-- 单个图标项 -->
  <li class="icon-glyph-item">
    <div class="icon-detail">
      <span class="icon">
        <svg>...</svg>
      </span>
      <div class="icon-name">晴天</div>
      <div class="icon-code">&#xe600;</div>
    </div>
  </li>
  <li class="icon-glyph-item">
    <!-- 更多图标... -->
  </li>
</ul>
```

## 第三步：配置通用爬虫 GUI

### URL 配置区域

**目标 URL:**
```
https://www.iconfont.cn/collections/detail?cid=你的集合ID
```
> 提示：从浏览器地址栏复制完整 URL

**爬取模式:**
- 选择：`列表页面` ✓

**列表容器选择器:**
```
li.icon-glyph-item
```
或者（根据实际页面结构）：
```
div.block-icon-list > div
```

### 字段选择器配置

点击"📋 示例"按钮清空，然后点击"➕ 添加"按钮，依次添加以下字段：

#### 字段 1：图标名称
- **字段名**: `name`
- **CSS选择器**: `div.icon-name`
- **说明**: 图标的中文名称

#### 字段 2：图标代码
- **字段名**: `code`
- **CSS选择器**: `div.icon-code`
- **说明**: Unicode 编码

#### 字段 3：图标 ID
- **字段名**: `icon_id`
- **CSS选择器**: `span.icon@data-id`
- **说明**: 图标的唯一 ID（如果有）

#### 字段 4：SVG 内容
- **字段名**: `svg`
- **CSS选择器**: `svg`
- **说明**: SVG 图标代码（可选）

#### 字段 5：预览图
- **字段名**: `preview`
- **CSS选择器**: `img@src`
- **说明**: 预览图片 URL（如果有）

### 爬取控制

**爬取数量:**
```
50
```
> 根据页面实际图标数量调整，建议先设置较小值测试

**请求延迟:**
```
2.0 秒
```
> iconfont.cn 可能有反爬限制，建议设置 2-3 秒延迟

**保存格式:**
- 选择：`JSON` ✓（推荐）
- 或选择：`CSV`

**保存位置:**
```
D:\Project\MyProject\W\crawler\data\iconfont_weather
```
> 点击"浏览..."按钮选择你想保存的文件夹

## 第四步：开始爬取

1. 检查所有配置是否正确
2. 点击 `🚀 开始爬取` 按钮
3. 观察"运行日志"区域的输出
4. 在"数据预览"区域查看提取的数据

## 常见问题和解决方案

### 问题 1：没有提取到数据

**可能原因：**
- 选择器不正确
- 页面需要登录
- 页面使用了动态加载

**解决方案：**
1. 使用浏览器开发者工具重新检查选择器
2. 尝试不同的选择器组合
3. 确保页面已完全加载

### 问题 2：提取的数据不完整

**解决方案：**
- 增加请求延迟（3-5 秒）
- 检查是否需要滚动页面才能加载更多内容
- 某些字段可能不存在，这是正常的

### 问题 3：被网站限制访问

**解决方案：**
- 增加请求延迟到 5 秒以上
- 减少爬取数量
- 分批次爬取
- 考虑使用代理（需要修改爬虫代码）

## 实际示例配置

### 配置 A：基础信息爬取

```
目标 URL: https://www.iconfont.cn/collections/detail?cid=xxxxx
爬取模式: 列表页面
列表容器: li.icon-glyph-item

字段配置：
1. name -> div.icon-name (图标名称)
2. code -> div.icon-code (Unicode)
3. class -> span.icon@class (CSS类名)

爬取数量: 30
延迟: 2.0秒
格式: JSON
```

### 配置 B：完整信息爬取

```
目标 URL: https://www.iconfont.cn/collections/detail?cid=xxxxx
爬取模式: 列表页面
列表容器: li.icon-glyph-item

字段配置：
1. name -> div.icon-name
2. code -> div.icon-code
3. svg -> svg (SVG代码)
4. font_class -> div.font-class
5. unicode -> div.unicode

爬取数量: 50
延迟: 3.0秒
格式: JSON
```

## 提示和技巧

### 1. 如何找到正确的选择器

在浏览器开发者工具中：
1. 右键点击元素 → "检查"
2. 在 Elements 面板中查看 HTML 结构
3. 右键点击元素 → Copy → Copy selector
4. 简化选择器（去掉不必要的层级）

### 2. 选择器语法

- **提取文本**: `div.class-name`
- **提取属性**: `img@src` 或 `a@href`
- **多层级**: `div.parent > span.child`
- **类选择器**: `.class-name`
- **ID选择器**: `#element-id`

### 3. 测试选择器

在浏览器控制台（Console）中测试：
```javascript
// 测试列表容器
document.querySelectorAll('li.icon-glyph-item')

// 测试字段选择器
document.querySelector('li.icon-glyph-item div.icon-name').textContent
```

## 下一步：处理爬取的数据

爬取完成后，你会得到一个 JSON 或 CSV 文件，包含所有图标信息。

### 如果需要下载 SVG 文件

iconfont.cn 的图标通常需要：
1. 登录账号
2. 添加到购物车
3. 下载图标包

通用爬虫主要用于爬取图标的元数据（名称、编码等），实际的图标文件可能需要通过官方渠道下载。

### 如果需要转换为 PNG

可以使用之前的 `svg_to_png_converter.py` 工具：
```bash
cd crawler
python src/svg_to_png_converter.py --input data/iconfont_weather --output data/weather_icons_png
```

## 注意事项

1. **遵守网站使用条款**：确保你的爬取行为符合 iconfont.cn 的使用协议
2. **合理使用**：不要过度频繁地请求，避免给服务器造成压力
3. **版权问题**：iconfont.cn 上的图标可能有不同的授权协议，使用前请确认
4. **反爬机制**：如果遇到验证码或访问限制，请降低爬取频率

## 需要帮助？

如果配置过程中遇到问题：
1. 检查浏览器开发者工具中的实际 HTML 结构
2. 尝试不同的选择器组合
3. 查看运行日志中的错误信息
4. 调整爬取参数（延迟、数量等）
