#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本 - 将 GUI 爬虫打包成 Windows EXE
使用 PyInstaller
"""

import os
import sys
import subprocess
import shutil

def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("\n正在安装 PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller 安装成功")
            return True
        except Exception as e:
            print(f"✗ PyInstaller 安装失败: {e}")
            return False

def build_exe():
    """构建 EXE"""
    print("\n" + "=" * 60)
    print("开始打包图标爬虫 GUI 为 EXE")
    print("=" * 60)
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        print("\n请手动安装 PyInstaller: pip install pyinstaller")
        return False
    
    # 打包参数
    script_path = "src/gui_crawler.py"
    output_name = "IconCrawler"
    
    # PyInstaller 命令
    cmd = [
        "pyinstaller",
        "--name", output_name,
        "--onefile",  # 打包成单个文件
        "--windowed",  # 不显示控制台窗口
        "--clean",  # 清理临时文件
        "--noconfirm",  # 不询问确认
        # 添加数据文件
        "--add-data", "src/multi_source_icon_crawler.py;.",
        "--add-data", "src/apply_icons_to_miniapp.py;.",
        # 隐藏导入
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "requests",
        "--hidden-import", "bs4",
        # 图标（如果有的话）
        # "--icon", "icon.ico",
        script_path
    ]
    
    print("\n执行命令:")
    print(" ".join(cmd))
    print()
    
    try:
        # 执行打包
        subprocess.check_call(cmd)
        
        print("\n" + "=" * 60)
        print("✓ 打包成功！")
        print("=" * 60)
        print(f"\nEXE 文件位置: dist/{output_name}.exe")
        print(f"文件大小: {os.path.getsize(f'dist/{output_name}.exe') / 1024 / 1024:.2f} MB")
        print("\n使用说明:")
        print(f"  1. 双击运行 dist/{output_name}.exe")
        print("  2. 选择图标来源和关键词")
        print("  3. 点击'开始爬取'按钮")
        print("  4. 等待下载完成")
        print("  5. 点击'应用到小程序'按钮")
        print("\n注意事项:")
        print("  - 首次运行可能需要几秒钟启动")
        print("  - 需要网络连接才能下载图标")
        print("  - 杀毒软件可能会误报，请添加信任")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        return False

def clean_build_files():
    """清理构建文件"""
    print("\n清理构建文件...")
    
    dirs_to_remove = ["build", "__pycache__"]
    files_to_remove = [f"{output_name}.spec" for output_name in ["IconCrawler"]]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  删除: {dir_name}/")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"  删除: {file_name}")
    
    print("✓ 清理完成")

def main():
    """主函数"""
    print("图标爬虫 GUI 打包工具")
    print("=" * 60)
    
    # 检查是否在正确的目录
    if not os.path.exists("src/gui_crawler.py"):
        print("✗ 错误: 请在 crawler 目录下运行此脚本")
        return
    
    # 构建 EXE
    success = build_exe()
    
    if success:
        # 询问是否清理构建文件
        try:
            response = input("\n是否清理构建文件？(y/n): ").strip().lower()
            if response == 'y':
                clean_build_files()
        except KeyboardInterrupt:
            print("\n\n已取消")
    
    print("\n完成！")

if __name__ == '__main__':
    main()
