@echo off
goto __git_update_main_v2
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

goto :eof

:__git_update_main_v2
setlocal
chcp 65001 >nul

echo ========================================
echo   Git Update Helper
echo ========================================
echo.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo This folder is not a Git repository.
    pause
    exit /b 1
)

for /f "delims=" %%B in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%B"
if not defined CURRENT_BRANCH set "CURRENT_BRANCH=main"

echo [1/4] Current status
git status
echo.

echo [2/4] Stage all changes
git add -A
if errorlevel 1 (
    echo Stage failed.
    pause
    exit /b 1
)
echo Stage done.
echo.

git diff --cached --quiet
if not errorlevel 1 (
    echo No staged changes to commit.
    pause
    exit /b 0
)

:ask_commit_v2
set "COMMIT_MSG="
echo [3/4] Enter what changed in this update
set /p "COMMIT_MSG=Commit message: "
if not defined COMMIT_MSG (
    echo Commit message cannot be empty. Please try again.
    echo.
    goto ask_commit_v2
)

git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo Commit failed.
    pause
    exit /b 1
)
echo Commit done.
echo.

echo [4/4] Push to origin/%CURRENT_BRANCH%
git push origin %CURRENT_BRANCH%
if errorlevel 1 (
    echo.
    echo Push failed. Try pull --rebase first...
    git pull origin %CURRENT_BRANCH% --rebase
    if errorlevel 1 (
        echo.
        echo Pull --rebase failed. Please resolve conflicts manually.
        pause
        exit /b 1
    )
    echo Retry push...
    git push origin %CURRENT_BRANCH%
    if errorlevel 1 (
        echo.
        echo Push still failed. Please check network, permissions, or conflicts.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo   Done
echo ========================================
echo Branch : %CURRENT_BRANCH%
echo Message: %COMMIT_MSG%
echo.
pause
endlocal
