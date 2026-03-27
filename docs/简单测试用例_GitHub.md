# 爬虫工具简单测试用例 - GitHub Trending

## 🎯 测试目标
使用一个结构简单的网站验证爬虫工具基本功能

## 🌐 测试网站
**GitHub Trending 页面**
- URL: https://github.com/trending
- 特点: 结构简单、无反爬虫、静态HTML
- 内容: 热门开源项目列表

## 📝 配置参数（复制粘贴即可）

### 1️⃣ URL配置
```
目标URL: https://github.com/trending
爬取模式: ⚫ 列表页面  ⚪ 单个页面
列表容器选择器: article.Box-row
```

### 2️⃣ 字段选择器配置

点击"添加"按钮，依次添加以下字段：

**字段1:**
```
字段名: 项目名称
CSS选择器: h2 a
说明: 项目名称
```

**字段2:**
```
字段名: 项目描述
CSS选择器: p.col-9
说明: 项目描述
```

**字段3:**
```
字段名: 星标数
CSS选择器: span.d-inline-block.float-sm-right
说明: Star数量
```

### 3️⃣ 爬取控制
```
爬取数量: 10 条
请求延迟: 2.0 秒
保存格式: ⚫ JSON  ⚪ CSV
保存位置: data/github_test
```

## ✅ 预期结果

成功爬取10个GitHub热门项目的信息，生成JSON文件包含：
- 项目名称
- 项目描述
- 星标数量

## 🔄 如果这个测试成功

说明你的爬虫工具本身没问题，Flaticon的问题是：
1. 网站使用JavaScript动态加载
2. 需要使用支持JS渲染的爬虫工具

## 💡 Flaticon替代方案

### 推荐: 使用 Icons8 网站

**配置参数：**
```
目标URL: https://icons8.com/icons/set/weather
爬取模式: 列表页面
列表容器: .icon-grid-item
```

**字段选择器：**
```
字段1: 图标图片 → img.icon-img
字段2: 图标名称 → .icon-name
```

---

**建议：先用GitHub测试验证工具正常，再尝试其他图标网站**
