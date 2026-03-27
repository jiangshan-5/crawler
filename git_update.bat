@echo off
chcp 65001 >nul
echo ========================================
echo    Git 更新推送脚本
echo ========================================
echo.

echo [1/4] 查看当前状态...
git status
echo.

echo [2/4] 添加所有修改的文件...
git add .
echo ✓ 文件添加完成
echo.

echo [3/4] 请输入提交信息
set /p COMMIT_MSG="提交信息: "

if "%COMMIT_MSG%"=="" (
    set COMMIT_MSG=Update: 更新代码
    echo 使用默认提交信息: %COMMIT_MSG%
)

git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo 警告：没有需要提交的更改
    pause
    exit /b 0
)
echo ✓ 本地提交完成
echo.

echo [4/4] 推送到 GitHub...
git push origin main
if errorlevel 1 (
    echo.
    echo ❌ 推送失败！
    echo 尝试先拉取远程更新...
    git pull origin main --rebase
    if errorlevel 1 (
        echo.
        echo ❌ 拉取失败！可能存在冲突，请手动解决。
        pause
        exit /b 1
    )
    echo 再次推送...
    git push origin main
    if errorlevel 1 (
        echo.
        echo ❌ 推送仍然失败！请检查：
        echo 1. 网络连接是否正常
        echo 2. GitHub 凭据是否正确
        echo 3. 是否有权限推送到该仓库
        pause
        exit /b 1
    )
)

echo ✓ 推送成功！

echo.
echo ========================================
echo    ✓ 更新完成！
echo ========================================
echo.
echo 你的修改已成功推送到 GitHub
echo 仓库地址: https://github.com/jiangshan-5/crawler
echo.
pause
