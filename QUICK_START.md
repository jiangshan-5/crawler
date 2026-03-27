# 🚀 快速开始指南

## 5 分钟上手通用爬虫工具

### 第一步：安装依赖

```bash
cd crawler
pip install -r requirements.txt
```

### 第二步：启动程序

**Windows 用户（推荐）：**
```bash
双击运行 run_universal_crawler.bat
```

**或者使用 Python：**
```bash
python src/universal_crawler_gui.py
```

### 第三步：配置爬虫

1. **输入 URL**
   ```
   https://example.com/products
   ```

2. **选择模式**
   - 📋 列表页面（推荐新手）

3. **配置列表容器**
   ```
   div.product-item
   ```

4. **添加字段**（点击 ➕ 添加按钮）
   
   | 字段名 | CSS选择器 | 说明 |
   |--------|-----------|------|
   | title  | h2.title  | 商品标题 |
   | price  | span.price | 商品价格 |
   | link   | a@href    | 商品链接 |

5. **设置参数**
   - 爬取数量：10
   - 请求延迟：2.0 秒
   - 保存格式：JSON

6. **点击 🚀 开始爬取**

### 第四步：查看结果

- 运行日志：实时查看爬取进度
- 数据预览：查看前 5 条数据
- 保存位置：`data/crawled_data/crawled_YYYYMMDD_HHMMSS.json`

## 💡 实用技巧

### 如何找到正确的选择器？

1. 打开目标网页
2. 按 `F12` 打开开发者工具
3. 点击左上角的"选择元素"工具
4. 鼠标悬停在要爬取的内容上
5. 在 Elements 面板中查看 HTML 结构
6. 右键 → Copy → Copy selector

### 常用选择器示例

```css
/* 提取文本 */
h1                    /* 标题 */
div.content           /* 内容 */
p.description         /* 描述 */

/* 提取属性 */
a@href                /* 链接地址 */
img@src               /* 图片地址 */
div@data-id           /* 数据ID */

/* 多层级 */
div.card > h2         /* 直接子元素 */
div.card h2           /* 所有后代元素 */
```

## 🎯 实战案例

### 案例 1：爬取博客文章列表

```
URL: https://blog.example.com
模式: 列表页面
列表容器: article.post

字段配置:
- title: h2.post-title
- author: span.author
- date: time@datetime
- link: a.read-more@href
```

### 案例 2：爬取商品详情

```
URL: https://shop.example.com/product/123
模式: 单个页面

字段配置:
- name: h1.product-name
- price: span.price
- description: div.description
- images: img.gallery@src
```

### 案例 3：爬取图标库

参考 `docs/ICONFONT_天气图标爬取指南.md`

## ❓ 常见问题

### Q: 没有提取到数据？
A: 检查选择器是否正确，使用浏览器开发者工具验证。

### Q: 被网站限制了？
A: 增加请求延迟到 3-5 秒，减少爬取数量。

### Q: 如何爬取需要登录的网站？
A: 目前版本不支持，需要手动添加 Cookie。

### Q: 可以爬取动态加载的内容吗？
A: 目前不支持 JavaScript 渲染，只能爬取静态 HTML。

## 📚 进阶学习

- [完整使用指南](docs/UNIVERSAL_CRAWLER_GUIDE.md)
- [GUI 界面说明](docs/UNIVERSAL_CRAWLER_UI_GUIDE.md)
- [iconfont 爬取教程](docs/ICONFONT_天气图标爬取指南.md)

## 🆘 获取帮助

- 查看文档目录 `docs/`
- 提交 Issue 到 GitHub
- 查看示例代码 `src/main.py`

---

🎉 恭喜！你已经学会了基本使用方法！
