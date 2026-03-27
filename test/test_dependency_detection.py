#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试依赖检测功能
验证动态检测是否正常工作
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_dynamic_detection():
    """测试动态检测功能"""
    print("=" * 60)
    print("测试依赖检测功能")
    print("=" * 60)
    
    from advanced_crawler import is_advanced_mode_available
    
    # 测试 1: 第一次检测
    print("\n[测试 1] 第一次检测")
    result1 = is_advanced_mode_available()
    print(f"结果: {result1}")
    
    # 测试 2: 第二次检测（应该返回相同结果）
    print("\n[测试 2] 第二次检测")
    result2 = is_advanced_mode_available()
    print(f"结果: {result2}")
    
    # 测试 3: 多次检测
    print("\n[测试 3] 连续检测 5 次")
    results = [is_advanced_mode_available() for _ in range(5)]
    print(f"结果: {results}")
    
    # 验证一致性
    print("\n[验证] 检查结果一致性")
    if all(r == result1 for r in [result2] + results):
        print("✓ 所有检测结果一致")
    else:
        print("✗ 检测结果不一致（异常）")
    
    # 显示依赖状态
    print("\n" + "=" * 60)
    if result1:
        print("✓ 高级模式可用")
        print("  - undetected-chromedriver 已安装")
        print("  - 可以使用反反爬虫功能")
    else:
        print("✗ 高级模式不可用")
        print("  - undetected-chromedriver 未安装")
        print("  - 请运行: pip install setuptools undetected-chromedriver")
    print("=" * 60)
    
    return result1

def test_import_performance():
    """测试导入性能"""
    import time
    
    print("\n" + "=" * 60)
    print("测试导入性能")
    print("=" * 60)
    
    from advanced_crawler import is_advanced_mode_available
    
    # 测试 100 次检测的时间
    iterations = 100
    start_time = time.time()
    
    for _ in range(iterations):
        is_advanced_mode_available()
    
    end_time = time.time()
    elapsed = end_time - start_time
    avg_time = elapsed / iterations * 1000  # 转换为毫秒
    
    print(f"\n检测次数: {iterations}")
    print(f"总耗时: {elapsed:.4f} 秒")
    print(f"平均耗时: {avg_time:.4f} 毫秒/次")
    
    if avg_time < 1:
        print("✓ 性能优秀（< 1ms）")
    elif avg_time < 10:
        print("✓ 性能良好（< 10ms）")
    else:
        print("⚠ 性能一般（>= 10ms）")
    
    print("=" * 60)

def test_module_state():
    """测试模块状态"""
    print("\n" + "=" * 60)
    print("测试模块状态")
    print("=" * 60)
    
    # 检查模块是否已加载
    if 'advanced_crawler' in sys.modules:
        print("✓ advanced_crawler 模块已加载")
    else:
        print("✗ advanced_crawler 模块未加载")
    
    if 'undetected_chromedriver' in sys.modules:
        print("✓ undetected_chromedriver 模块已加载")
    else:
        print("✗ undetected_chromedriver 模块未加载（正常，延迟导入）")
    
    print("=" * 60)

if __name__ == '__main__':
    print("\n🔍 依赖检测测试套件\n")
    
    # 运行测试
    test_dynamic_detection()
    test_import_performance()
    test_module_state()
    
    print("\n✅ 所有测试完成\n")
