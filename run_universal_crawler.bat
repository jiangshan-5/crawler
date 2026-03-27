@echo off
chcp 65001 >nul
echo ========================================
echo    通用网页爬虫工具 v2.0
echo ========================================
echo.
echo 正在启动...
echo.

python src\universal_crawler_gui.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo 启动失败！
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. Python 未安装或未添加到 PATH
    echo 2. 缺少依赖库
    echo.
    echo 解决方法：
    echo 1. 安装 Python 3.7+
    echo 2. 运行: pip install -r requirements.txt
    echo.
    pause
)
