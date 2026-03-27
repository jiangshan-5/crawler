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
git push
if errorlevel 1 (
    echo.
    echo 错误：推送失败！
    echo 尝试先拉取远程更新...
    git pull --rebase
    echo 再次推送...
    git push
)

echo.
echo ========================================
echo    ✓ 更新完成！
echo ========================================
echo.
pause
