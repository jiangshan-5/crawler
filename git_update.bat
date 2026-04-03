@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ========================================
echo   Git Update Helper (Develop Branch)
echo ========================================
echo.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo This folder is not a Git repository.
    pause
    exit /b 1
)

set "TARGET_BRANCH=develop"

for /f "delims=" %%B in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%B"
if not defined CURRENT_BRANCH set "CURRENT_BRANCH=main"

echo Current branch: %CURRENT_BRANCH%
if not "%CURRENT_BRANCH%"=="%TARGET_BRANCH%" (
    echo.
    echo Warning: You are on branch '%CURRENT_BRANCH%', but target is '%TARGET_BRANCH%'
    echo.
    choice /C YN /M "Do you want to switch to %TARGET_BRANCH% branch"
    if errorlevel 2 (
        echo Operation cancelled.
        pause
        exit /b 0
    )
    echo.
    echo Switching to %TARGET_BRANCH% branch...
    git checkout %TARGET_BRANCH%
    if errorlevel 1 (
        echo Failed to switch branch. Creating new %TARGET_BRANCH% branch...
        git checkout -b %TARGET_BRANCH%
        if errorlevel 1 (
            echo Failed to create branch.
            pause
            exit /b 1
        )
    )
    set "CURRENT_BRANCH=%TARGET_BRANCH%"
    echo Switched to %TARGET_BRANCH% branch.
    echo.
)

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

:ask_commit
set "COMMIT_TITLE="
set "COMMIT_BODY="
set "LINE_COUNT=0"

echo [3/4] Enter commit message (multi-line supported)
echo ------------------------------------------------
echo First line  : Commit title (required)
echo Other lines : Detailed description (optional)
echo Type 'END' on a new line to finish, or press Ctrl+C to cancel
echo ------------------------------------------------
echo.

set /p "COMMIT_TITLE=Title: "
if not defined COMMIT_TITLE (
    echo.
    echo Error: Commit title cannot be empty. Please try again.
    echo.
    goto ask_commit
)

echo.
echo Enter description (type 'END' to finish):
echo.

:read_body_line
set "INPUT_LINE="
set /p "INPUT_LINE=> "

if /i "!INPUT_LINE!"=="END" goto commit_done
if /i "!INPUT_LINE!"=="end" goto commit_done

if defined INPUT_LINE (
    if !LINE_COUNT! EQU 0 (
        set "COMMIT_BODY=!INPUT_LINE!"
    ) else (
        set "COMMIT_BODY=!COMMIT_BODY!
!INPUT_LINE!"
    )
    set /a LINE_COUNT+=1
)

goto read_body_line

:commit_done
echo.
echo ------------------------------------------------
echo Commit Preview:
echo ------------------------------------------------
echo Title: %COMMIT_TITLE%
if defined COMMIT_BODY (
    echo.
    echo Description:
    echo !COMMIT_BODY!
)
echo ------------------------------------------------
echo.

choice /C YN /M "Confirm this commit message"
if errorlevel 2 (
    echo.
    echo Commit cancelled. Please re-enter.
    echo.
    goto ask_commit
)

if defined COMMIT_BODY (
    git commit -m "%COMMIT_TITLE%" -m "!COMMIT_BODY!"
) else (
    git commit -m "%COMMIT_TITLE%"
)

if errorlevel 1 (
    echo Commit failed.
    pause
    exit /b 1
)
echo Commit done.
echo.

echo [4/4] Push to origin/%TARGET_BRANCH%
git push origin %TARGET_BRANCH%
if errorlevel 1 (
    echo.
    echo Push failed. Try pull --rebase first...
    git pull origin %TARGET_BRANCH% --rebase
    if errorlevel 1 (
        echo.
        echo Pull --rebase failed. Please resolve conflicts manually.
        pause
        exit /b 1
    )
    echo Retry push...
    git push origin %TARGET_BRANCH%
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
echo Branch : %TARGET_BRANCH%
echo Title  : %COMMIT_TITLE%
if defined COMMIT_BODY (
    echo Body   : !COMMIT_BODY!
)
echo.
pause
endlocal
