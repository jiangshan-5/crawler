#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级模式测试脚本
用于验证反反爬虫功能是否正常工作
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_import():
    """测试1: 检查依赖是否安装"""
    print("=" * 60)
    print("测试1: 检查依赖安装")
    print("=" * 60)
    
    try:
        import undetected_chromedriver as uc
        print("✓ undetected-chromedriver 已安装")
        print(f"  版本: {uc.__version__ if hasattr(uc, '__version__') else '未知'}")
        return True
    except ImportError:
        print("✗ undetected-chromedriver 未安装")
        print("\n请运行: pip install undetected-chromedriver")
        return False

def test_advanced_crawler():
    """测试2: 测试高级爬虫模块"""
    print("\n" + "=" * 60)
    print("测试2: 测试高级爬虫模块")
    print("=" * 60)
    
    try:
        from advanced_crawler import AdvancedCrawler, is_advanced_mode_available
        
        if not is_advanced_mode_available():
            print("✗ 高级模式不可用")
            return False
        
        print("✓ 高级爬虫模块导入成功")
        print("✓ 高级模式可用")
        return True
        
    except Exception as e:
        print(f"✗ 高级爬虫模块测试失败: {e}")
        return False

def test_basic_crawl():
    """测试3: 测试基础爬取功能"""
    print("\n" + "=" * 60)
    print("测试3: 测试标准模式爬取")
    print("=" * 60)
    
    try:
        from universal_crawler import UniversalCrawler
        
        crawler = UniversalCrawler(
            base_url='https://example.com',
            output_dir='data/test',
            use_advanced_mode=False
        )
        
        print("✓ 标准模式爬虫创建成功")
        
        # 测试爬取
        soup = crawler.fetch_page('https://example.com', timeout=10)
        if soup:
            print("✓ 标准模式爬取成功")
            print(f"  页面标题: {soup.title.string if soup.title else '无'}")
            crawler.close()
            return True
        else:
            print("✗ 标准模式爬取失败")
            return False
            
    except Exception as e:
        print(f"✗ 标准模式测试失败: {e}")
        return False

def test_advanced_crawl():
    """测试4: 测试高级模式爬取"""
    print("\n" + "=" * 60)
    print("测试4: 测试高级模式爬取")
    print("=" * 60)
    
    try:
        from universal_crawler import UniversalCrawler
        from advanced_crawler import is_advanced_mode_available
        
        if not is_advanced_mode_available():
            print("⊘ 跳过：高级模式不可用")
            return True
        
        print("正在启动高级模式...")
        print("（首次使用会下载ChromeDriver，请耐心等待）")
        
        crawler = UniversalCrawler(
            base_url='https://example.com',
            output_dir='data/test',
            use_advanced_mode=True
        )
        
        print("✓ 高级模式爬虫创建成功")
        
        # 测试爬取
        print("正在测试爬取...")
        soup = crawler.fetch_page('https://example.com', timeout=30)
        
        if soup:
            print("✓ 高级模式爬取成功")
            print(f"  页面标题: {soup.title.string if soup.title else '无'}")
            print(f"  HTML长度: {len(str(soup))}")
            crawler.close()
            return True
        else:
            print("✗ 高级模式爬取失败")
            crawler.close()
            return False
            
    except Exception as e:
        print(f"✗ 高级模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "高级模式功能测试" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # 测试1: 依赖检查
    results.append(("依赖安装", test_import()))
    
    # 测试2: 模块导入
    results.append(("模块导入", test_advanced_crawler()))
    
    # 测试3: 标准模式
    results.append(("标准模式", test_basic_crawl()))
    
    # 测试4: 高级模式
    results.append(("高级模式", test_advanced_crawl()))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:15} {status}")
    
    # 总结
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有测试通过！高级模式已就绪！")
        print("\n下一步:")
        print("1. 运行 run_universal_crawler.bat 启动GUI")
        print("2. 勾选'高级模式'选项")
        print("3. 开始爬取受保护的网站")
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        if not results[0][1]:
            print("\n请先安装依赖:")
            print("pip install undetected-chromedriver")

if __name__ == '__main__':
    main()
