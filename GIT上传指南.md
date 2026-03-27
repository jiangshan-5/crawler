# Git 上传指南

## 准备工作

### 1. 安装 Git

如果还没有安装 Git，请先安装：

**Windows:**
- 下载：https://git-scm.com/download/win
- 安装后打开 Git Bash

**验证安装:**
```bash
git --version
```

### 2. 配置 Git

首次使用需要配置用户信息：

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

## 创建 GitHub 仓库

### 方式 1：在 GitHub 网站创建

1. 登录 GitHub (https://github.com)
2. 点击右上角 "+" → "New repository"
3. 填写仓库信息：
   - Repository name: `universal-web-crawler` (或其他名字)
   - Description: `一个功能强大的通用网页爬虫工具`
   - Public/Private: 选择公开或私有
   - ❌ 不要勾选 "Initialize this repository with a README"
4. 点击 "Create repository"

### 方式 2：使用 GitHub CLI

```bash
gh repo create universal-web-crawler --public --description "通用网页爬虫工具"
```

## 上传步骤

### 第一次上传（初始化仓库）

在 `crawler` 目录下执行以下命令：

```bash
# 1. 进入项目目录
cd D:\Project\MyProject\W\crawler

# 2. 初始化 Git 仓库
git init

# 3. 添加所有文件到暂存区
git add .

# 4. 查看状态（可选）
git status

# 5. 提交到本地仓库
git commit -m "Initial commit: 通用网页爬虫工具 v2.0"

# 6. 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/universal-web-crawler.git

# 7. 推送到 GitHub
git push -u origin main
```

如果遇到 `main` 分支不存在的错误，使用：
```bash
git branch -M main
git push -u origin main
```

### 后续更新

当你修改了代码后，使用以下命令更新：

```bash
# 1. 查看修改的文件
git status

# 2. 添加修改的文件
git add .
# 或者添加特定文件
git add src/universal_crawler_gui.py

# 3. 提交修改
git commit -m "描述你的修改内容"

# 4. 推送到 GitHub
git push
```

## 常用 Git 命令

### 查看状态
```bash
git status              # 查看当前状态
git log                 # 查看提交历史
git log --oneline       # 简洁的提交历史
```

### 分支操作
```bash
git branch              # 查看所有分支
git branch dev          # 创建 dev 分支
git checkout dev        # 切换到 dev 分支
git checkout -b feature # 创建并切换到 feature 分支
git merge dev           # 合并 dev 分支到当前分支
```

### 撤销操作
```bash
git checkout -- file.py # 撤销文件的修改
git reset HEAD file.py  # 取消暂存
git reset --hard HEAD   # 撤销所有修改（危险！）
```

### 远程操作
```bash
git remote -v           # 查看远程仓库
git pull                # 拉取远程更新
git push                # 推送到远程
git clone <url>         # 克隆仓库
```

## 提交信息规范

建议使用以下格式：

```
类型: 简短描述

详细描述（可选）
```

**类型：**
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例：**
```bash
git commit -m "feat: 添加深色模式支持"
git commit -m "fix: 修复选择器解析错误"
git commit -m "docs: 更新 README 使用说明"
```

## .gitignore 说明

已创建 `.gitignore` 文件，以下内容不会被上传：

- `__pycache__/` - Python 缓存
- `*.pyc` - 编译的 Python 文件
- `venv/` - 虚拟环境
- `data/` - 爬取的数据
- `*.log` - 日志文件
- `.vscode/` - IDE 配置
- `*.exe` - 可执行文件

## 常见问题

### 1. 推送时要求输入用户名密码

**解决方案 1：使用 Personal Access Token**

1. GitHub 设置 → Developer settings → Personal access tokens
2. Generate new token
3. 选择权限：repo
4. 复制生成的 token
5. 推送时使用 token 作为密码

**解决方案 2：使用 SSH**

```bash
# 生成 SSH 密钥
ssh-keygen -t rsa -b 4096 -C "你的邮箱@example.com"

# 复制公钥
cat ~/.ssh/id_rsa.pub

# 在 GitHub 设置 → SSH and GPG keys → New SSH key
# 粘贴公钥

# 修改远程仓库地址为 SSH
git remote set-url origin git@github.com:你的用户名/universal-web-crawler.git
```

### 2. 文件太大无法上传

GitHub 单个文件限制 100MB，如果有大文件：

```bash
# 从 Git 中移除大文件
git rm --cached 大文件.exe

# 添加到 .gitignore
echo "大文件.exe" >> .gitignore

# 提交修改
git commit -m "移除大文件"
```

### 3. 推送被拒绝

```bash
# 先拉取远程更新
git pull origin main --rebase

# 再推送
git push origin main
```

### 4. 合并冲突

```bash
# 查看冲突文件
git status

# 手动编辑冲突文件，解决冲突

# 标记为已解决
git add 冲突文件.py

# 继续合并
git commit
```

## 推荐的工作流程

### 功能开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发并提交
git add .
git commit -m "feat: 添加新功能"

# 3. 切换回主分支
git checkout main

# 4. 合并功能分支
git merge feature/new-feature

# 5. 推送到远程
git push origin main

# 6. 删除功能分支（可选）
git branch -d feature/new-feature
```

### Bug 修复流程

```bash
# 1. 创建修复分支
git checkout -b fix/bug-description

# 2. 修复并提交
git add .
git commit -m "fix: 修复某个 bug"

# 3. 合并回主分支
git checkout main
git merge fix/bug-description

# 4. 推送
git push origin main
```

## GitHub 仓库优化

### 添加 README 徽章

在 README.md 顶部添加：

```markdown
![GitHub stars](https://img.shields.io/github/stars/你的用户名/universal-web-crawler)
![GitHub forks](https://img.shields.io/github/forks/你的用户名/universal-web-crawler)
![GitHub issues](https://img.shields.io/github/issues/你的用户名/universal-web-crawler)
![Python](https://img.shields.io/badge/python-3.6+-blue)
```

### 添加 Topics

在 GitHub 仓库页面：
1. 点击 "About" 旁边的设置图标
2. 添加 topics: `python`, `web-scraping`, `crawler`, `gui`, `tkinter`

### 创建 Release

```bash
# 1. 创建标签
git tag -a v2.0 -m "Release version 2.0"

# 2. 推送标签
git push origin v2.0
```

然后在 GitHub 网站上创建 Release。

## 下一步

上传完成后，你可以：

1. 在 README 中添加项目截图
2. 编写详细的使用文档
3. 添加示例代码
4. 创建 Wiki 页面
5. 设置 GitHub Pages 展示项目

## 参考资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 帮助文档](https://docs.github.com)
- [Git 教程 - 廖雪峰](https://www.liaoxuefeng.com/wiki/896043488029600)
