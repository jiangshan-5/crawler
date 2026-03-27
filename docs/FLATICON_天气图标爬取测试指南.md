# Flaticon 天气图标爬取测试指南

## 📋 测试目标
使用通用网页爬虫工具从 Flaticon 网站爬取天气相关图标

## 🌐 目标网站信息
- **网站名称**: Flaticon
- **目标页面**: https://www.flaticon.com/free-icons/weather
- **图标数量**: 260,468+ 免费天气图标
- **支持格式**: PNG, SVG, EPS, PSD

## 🚀 启动爬虫工具

### 方法一：双击启动脚本
直接双击 `run_universal_crawler.bat` 文件

### 方法二：命令行启动
```bash
cd crawler
python src/universal_crawler_gui.py
```

## 📝 爬虫配置参数

### 1️⃣ 基本信息
| 配置项 | 填写内容 |
|--------|----------|
| **目标URL** | `https://www.flaticon.com/free-icons/weather` |
| **爬取深度** | `1` 或 `2`（建议从1开始测试） |
| **保存目录** | `data/flaticon_weather_icons` |

### 2️⃣ 内容选择器（CSS Selector）

根据 Flaticon 网站结构，可以尝试以下选择器：

**图标容器选择器：**
```css
.icon--item
```
或
```css
.bj-icon
```
或
```css
[data-icon-id]
```

**图标图片选择器：**
```css
img.icon--item__img
```
或
```css
img[loading="lazy"]
```

**图标标题选择器：**
```css
.icon--item__title
```

### 3️⃣ 下载设置
| 配置项 | 建议值 | 说明 |
|--------|--------|------|
| **下载图片** | ✅ 勾选 | 下载图标图片 |
| **下载延迟** | `2-3秒` | 避免请求过快被封 |
| **最大下载数** | `20-50` | 测试时建议少量 |
| **User-Agent** | 使用默认 | 模拟浏览器访问 |

### 4️⃣ 高级选项（可选）
```
请求头设置：
- Referer: https://www.flaticon.com/
- Accept: image/webp,image/apng,image/*,*/*;q=0.8
```

## 🎯 测试步骤

### Step 1: 启动工具
1. 双击 `run_universal_crawler.bat`
2. 等待GUI界面打开

### Step 2: 填写基本配置
1. **目标URL**: 粘贴 `https://www.flaticon.com/free-icons/weather`
2. **爬取深度**: 输入 `1`
3. **保存目录**: 输入 `data/flaticon_weather_icons`

### Step 3: 配置选择器
1. 点击"内容选择器"区域
2. 尝试填写：
   - 容器选择器: `.icon--item`
   - 图片选择器: `img.icon--item__img`
   - 标题选择器: `.icon--item__title`

### Step 4: 设置下载选项
1. ✅ 勾选"下载图片"
2. 设置延迟: `2` 秒
3. 设置最大下载数: `20`（测试用）

### Step 5: 开始爬取
1. 点击"开始爬取"按钮
2. 观察进度条和日志输出
3. 等待爬取完成

### Step 6: 查看结果
1. 打开 `crawler/data/flaticon_weather_icons/` 目录
2. 检查下载的图标文件
3. 查看生成的 JSON 数据文件

## 📊 预期结果

### 成功标志
- ✅ 成功访问目标页面
- ✅ 解析出图标列表
- ✅ 下载图标图片到本地
- ✅ 生成包含图标信息的 JSON 文件
- ✅ 日志显示"爬取完成"

### 输出文件
```
crawler/data/flaticon_weather_icons/
├── images/              # 下载的图标图片
│   ├── weather_icon_1.png
│   ├── weather_icon_2.png
│   └── ...
├── results.json         # 爬取结果数据
└── crawler.log          # 爬取日志
```

## ⚠️ 常见问题

### 问题1: 无法访问网站
**原因**: 网络连接问题或被网站限制
**解决方案**:
- 检查网络连接
- 增加请求延迟（3-5秒）
- 更换 User-Agent

### 问题2: 选择器无效
**原因**: CSS选择器不正确
**解决方案**:
1. 打开浏览器访问目标页面
2. 按 F12 打开开发者工具
3. 使用"选择元素"工具查看实际的HTML结构
4. 更新选择器配置

### 问题3: 图片下载失败
**原因**: 图片URL格式或权限问题
**解决方案**:
- 检查图片URL是否完整
- 添加 Referer 请求头
- 尝试不同的图片格式（PNG/SVG）

### 问题4: 下载速度慢
**原因**: 请求延迟设置过大
**解决方案**:
- 适当减少延迟时间（但不要低于1秒）
- 增加并发数（高级功能）

## 🔍 调试技巧

### 1. 查看网页源代码
```bash
# 在浏览器中访问目标页面
# 右键 -> 查看网页源代码
# 搜索 "icon" 或 "weather" 关键词
```

### 2. 测试选择器
在浏览器控制台中测试：
```javascript
// 测试容器选择器
document.querySelectorAll('.icon--item').length

// 测试图片选择器
document.querySelectorAll('img.icon--item__img').length
```

### 3. 查看爬虫日志
```bash
# 日志文件位置
crawler/logs/crawler_YYYYMMDD_HHMMSS.log
```

## 📈 进阶测试

### 测试场景1: 小批量测试
- 深度: 1
- 最大下载: 10
- 目的: 验证配置正确性

### 测试场景2: 中等批量测试
- 深度: 1
- 最大下载: 50
- 目的: 测试稳定性

### 测试场景3: 大批量爬取
- 深度: 2
- 最大下载: 200
- 目的: 获取更多图标

## 💡 优化建议

1. **首次测试**: 使用小批量（10-20个）验证配置
2. **观察日志**: 实时查看爬取进度和错误信息
3. **调整参数**: 根据实际情况调整延迟和深度
4. **遵守规则**: 不要过于频繁请求，避免被封IP

## 📞 技术支持

如果遇到问题：
1. 查看 `crawler/logs/` 目录下的日志文件
2. 检查 `crawler/README.md` 文档
3. 参考 `crawler/docs/UNIVERSAL_CRAWLER_GUIDE.md`

## ✅ 测试检查清单

- [ ] 已安装 Python 3.7+
- [ ] 已安装依赖库（requirements.txt）
- [ ] 已启动爬虫GUI工具
- [ ] 已填写目标URL
- [ ] 已配置选择器
- [ ] 已设置下载选项
- [ ] 已开始爬取
- [ ] 已查看结果文件
- [ ] 测试成功 ✨

---

**祝测试顺利！** 🎉

如有问题，请查看日志文件或调整配置参数。
