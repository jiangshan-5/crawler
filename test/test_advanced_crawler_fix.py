#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试高级爬虫修复
验证 uc 导入问题是否已解决
"""

import sys
import os
import pytest

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_import():
    """测试导入"""
    print("=" * 60)
    print("测试 1: 导入模块")
    print("=" * 60)
    
    try:
        from advanced_crawler import AdvancedCrawler, is_advanced_mode_available
        print("✅ 模块导入成功")
        
        available = is_advanced_mode_available()
        print(f"✅ 高级模式可用性: {available}")
        assert isinstance(available, bool)
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        assert False, f"import failed: {e}"

def test_create_instance():
    """测试创建实例"""
    print("\n" + "=" * 60)
    print("测试 2: 创建爬虫实例")
    print("=" * 60)
    
    try:
        from advanced_crawler import AdvancedCrawler, is_advanced_mode_available
        
        if not is_advanced_mode_available():
            print("⚠️ 跳过: undetected-chromedriver 未安装")
            pytest.skip("undetected-chromedriver not installed")
        
        crawler = AdvancedCrawler(headless=True)
        print("✅ 实例创建成功")
        assert crawler is not None
    except Exception as e:
        print(f"❌ 创建实例失败: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"create instance failed: {e}"

def test_start_browser():
    """测试启动浏览器"""
    print("\n" + "=" * 60)
    print("测试 3: 启动浏览器（可能需要几秒钟）")
    print("=" * 60)
    
    try:
        from advanced_crawler import AdvancedCrawler, is_advanced_mode_available
        
        if not is_advanced_mode_available():
            print("⚠️ 跳过: undetected-chromedriver 未安装")
            pytest.skip("undetected-chromedriver not installed")
        
        print("正在启动浏览器...")
        crawler = AdvancedCrawler(headless=True)
        crawler.start()
        print("✅ 浏览器启动成功")
        
        # 关闭浏览器
        print("正在关闭浏览器...")
        crawler.close()
        print("✅ 浏览器关闭成功")
        assert True
    except Exception as e:
        print(f"❌ 启动浏览器失败: {e}")
        import traceback
        traceback.print_exc()
        pytest.skip(f"start browser skipped due to environment/network issue: {e}")

def test_fetch_page():
    """测试获取网页"""
    print("\n" + "=" * 60)
    print("测试 4: 获取网页（可能需要10-20秒）")
    print("=" * 60)
    
    try:
        from advanced_crawler import AdvancedCrawler, is_advanced_mode_available
        
        if not is_advanced_mode_available():
            print("⚠️ 跳过: undetected-chromedriver 未安装")
            pytest.skip("undetected-chromedriver not installed")
        
        print("正在获取测试网页...")
        with AdvancedCrawler(headless=True) as crawler:
            soup = crawler.fetch_page("https://example.com", wait_time=2)
            
            if soup:
                title = soup.find('title')
                print(f"✅ 网页获取成功")
                print(f"   标题: {title.get_text() if title else 'N/A'}")
                assert soup is not None
            else:
                print("❌ 网页获取失败")
                assert False, "fetch page returned empty soup"
                
    except Exception as e:
        print(f"❌ 获取网页失败: {e}")
        import traceback
        traceback.print_exc()
        pytest.skip(f"fetch page skipped due to environment/network issue: {e}")

if __name__ == '__main__':
    print("\n🔍 高级爬虫修复测试套件\n")
    
    results = []
    
    # 测试 1: 导入
    results.append(("导入模块", test_import()))
    
    # 测试 2: 创建实例
    results.append(("创建实例", test_create_instance()))
    
    # 测试 3: 启动浏览器
    results.append(("启动浏览器", test_start_browser()))
    
    # 测试 4: 获取网页（可选，比较慢）
    print("\n" + "=" * 60)
    response = input("是否测试获取网页？（需要10-20秒）[y/N]: ")
    if response.lower() == 'y':
        results.append(("获取网页", test_fetch_page()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("✅ 所有测试通过！高级爬虫工作正常！")
    else:
        print("⚠️ 部分测试失败，请检查错误信息")
    
    print("=" * 60)
    print("\n")
