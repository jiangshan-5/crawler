@echo off
setlocal EnableExtensions
chcp 65001 >nul

REM Always run from the project root (where this .bat lives)
cd /d "%~dp0"

echo ========================================
echo   Universal Crawler Launcher (Modern)
echo ========================================
echo.

set "PY_CMD="
set "PY_LABEL="
set "PY_KIND="

if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
    set "PY_LABEL=.venv\Scripts\python.exe"
    set "PY_KIND=exe"
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set "PY_CMD=py -3"
        set "PY_LABEL=py -3"
        set "PY_KIND=cmd"
    ) else (
        where python >nul 2>nul
        if %errorlevel%==0 (
            set "PY_CMD=python"
            set "PY_LABEL=python"
            set "PY_KIND=exe"
        )
    )
)

if not defined PY_CMD goto NO_PYTHON

echo Using interpreter: %PY_LABEL%
echo Starting GUI...
echo.
if "%PY_KIND%"=="exe" (
    call "%PY_CMD%" src\universal_crawler_gui_modern.py
) else (
    call %PY_CMD% src\universal_crawler_gui_modern.py
)
set "EXIT_CODE=%errorlevel%"

if not "%EXIT_CODE%"=="0" goto START_FAIL
goto DONE

:NO_PYTHON
echo ERROR: Python not found.
echo.
echo Install Python 3.10+ or create .venv first.
echo Then run:
echo   pip install -r requirements.txt
echo.
pause
exit /b 1

:START_FAIL
echo.
echo ========================================
echo Startup failed (exit code: %EXIT_CODE%)
echo ========================================
echo.
echo Common fixes:
echo 1. Install base deps:
echo    pip install -r requirements.txt
echo.
echo 2. If you need advanced mode:
echo    pip install -r requirements-advanced.txt
echo.
echo 3. Run this script again.
echo.
pause
exit /b %EXIT_CODE%

:DONE
endlocal
