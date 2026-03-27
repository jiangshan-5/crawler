@echo off
chcp 65001 >nul
echo ========================================
echo    Git 仓库初始化脚本
echo ========================================
echo.

echo [1/7] 初始化 Git 仓库...
git init
if errorlevel 1 (
    echo 错误：Git 初始化失败！请确认已安装 Git。
    pause
    exit /b 1
)
echo ✓ Git 仓库初始化成功
echo.

echo [2/7] 添加所有文件到暂存区...
git add .
echo ✓ 文件添加完成
echo.

echo [3/7] 查看文件状态...
git status
echo.

echo [4/7] 提交到本地仓库...
git commit -m "Initial commit: 通用网页爬虫工具 v2.0"
if errorlevel 1 (
    echo 警告：提交可能失败，请检查是否有文件需要提交
)
echo ✓ 本地提交完成
echo.

echo [5/7] 请输入你的 GitHub 仓库地址
echo 格式: https://github.com/用户名/仓库名.git
set /p REPO_URL="仓库地址: "

if "%REPO_URL%"=="" (
    echo 错误：仓库地址不能为空！
    pause
    exit /b 1
)

echo.
echo [6/7] 添加远程仓库...
git remote add origin %REPO_URL%
if errorlevel 1 (
    echo 警告：远程仓库可能已存在，尝试更新...
    git remote set-url origin %REPO_URL%
)
echo ✓ 远程仓库配置完成
echo.

echo [7/7] 推送到 GitHub...
echo 注意：首次推送可能需要输入 GitHub 用户名和密码/Token
git branch -M main
git push -u origin main
if errorlevel 1 (
    echo.
    echo 错误：推送失败！
    echo 可能的原因：
    echo 1. 需要输入 GitHub 凭据
    echo 2. 远程仓库已有内容
    echo 3. 网络连接问题
    echo.
    echo 请手动执行: git push -u origin main
    pause
    exit /b 1
)

echo.
echo ========================================
echo    ✓ 上传完成！
echo ========================================
echo.
echo 你的项目已成功上传到 GitHub！
echo 仓库地址: %REPO_URL%
echo.
echo 后续更新请使用: git_update.bat
echo.
pause
