#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 爬虫测试脚本
快速测试所有功能是否正常
"""

import sys
import os

def test_imports():
    """测试所有依赖是否已安装"""
    print("=" * 60)
    print("测试 1: 检查依赖库")
    print("=" * 60)
    
    required_modules = {
        'tkinter': 'Tkinter (GUI 框架)',
        'requests': 'Requests (HTTP 请求)',
        'bs4': 'BeautifulSoup4 (HTML 解析)',
        'PIL': 'Pillow (图像处理)',
        'lxml': 'lxml (XML 解析)'
    }
    
    missing = []
    
    for module, name in required_modules.items():
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - 未安装")
            missing.append(module)
    
    if missing:
        print("\n缺少依赖库，请运行:")
        print("pip install -r requirements.txt")
        return False
    
    print("\n✓ 所有依赖库已安装")
    return True

def test_files():
    """测试所有必需文件是否存在"""
    print("\n" + "=" * 60)
    print("测试 2: 检查文件")
    print("=" * 60)
    
    required_files = [
        'src/gui_crawler.py',
        'src/multi_source_icon_crawler.py',
        'src/apply_icons_to_miniapp.py',
        'requirements.txt'
    ]
    
    missing = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - 不存在")
            missing.append(file)
    
    if missing:
        print("\n缺少必需文件！")
        return False
    
    print("\n✓ 所有文件完整")
    return True

def test_crawler_import():
    """测试爬虫模块是否可以导入"""
    print("\n" + "=" * 60)
    print("测试 3: 测试爬虫模块")
    print("=" * 60)
    
    try:
        sys.path.insert(0, 'src')
        from multi_source_icon_crawler import MultiSourceIconCrawler
        print("✓ 爬虫模块导入成功")
        
        # 测试创建实例
        crawler = MultiSourceIconCrawler(output_dir='test_output')
        print("✓ 爬虫实例创建成功")
        
        return True
    except Exception as e:
        print(f"✗ 爬虫模块测试失败: {e}")
        return False

def test_applier_import():
    """测试图标应用模块是否可以导入"""
    print("\n" + "=" * 60)
    print("测试 4: 测试图标应用模块")
    print("=" * 60)
    
    try:
        sys.path.insert(0, 'src')
        from apply_icons_to_miniapp import IconApplier
        print("✓ 图标应用模块导入成功")
        
        # 测试创建实例
        applier = IconApplier()
        print("✓ 图标应用实例创建成功")
        
        return True
    except Exception as e:
        print(f"✗ 图标应用模块测试失败: {e}")
        return False

def test_gui_import():
    """测试 GUI 模块是否可以导入"""
    print("\n" + "=" * 60)
    print("测试 5: 测试 GUI 模块")
    print("=" * 60)
    
    try:
        sys.path.insert(0, 'src')
        from gui_crawler import IconCrawlerGUI
        print("✓ GUI 模块导入成功")
        
        return True
    except Exception as e:
        print(f"✗ GUI 模块测试失败: {e}")
        return False

def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "图标爬虫 GUI 测试工具" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    tests = [
        ("依赖库检查", test_imports),
        ("文件完整性检查", test_files),
        ("爬虫模块测试", test_crawler_import),
        ("图标应用模块测试", test_applier_import),
        ("GUI 模块测试", test_gui_import)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 发生异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n下一步:")
        print("  1. 运行 GUI: python src/gui_crawler.py")
        print("  2. 或双击: run_gui.bat")
        print("  3. 打包 EXE: python build_exe.py")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误信息")
        print("\n建议:")
        print("  1. 安装依赖: pip install -r requirements.txt")
        print("  2. 检查文件完整性")
        print("  3. 重新运行测试")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        print("\n按任意键退出...")
        input()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(1)
