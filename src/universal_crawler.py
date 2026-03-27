#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用网页爬虫
支持用户自定义 URL、CSS 选择器、爬取数量等
支持高级模式（反反爬虫）
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
import csv

# 导入高级爬虫模块
try:
    from .advanced_crawler import AdvancedCrawler, is_advanced_mode_available
except ImportError:
    from advanced_crawler import AdvancedCrawler, is_advanced_mode_available

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class UniversalCrawler:
    """通用网页爬虫"""
    
    def __init__(self, base_url, output_dir='data/crawled_data', use_advanced_mode=False):
        """
        初始化爬虫
        
        Args:
            base_url: 目标网站的基础 URL
            output_dir: 数据保存目录
            use_advanced_mode: 是否使用高级模式（反反爬虫）
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.use_advanced_mode = use_advanced_mode
        self.advanced_crawler = None
        
        # 标准模式的session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 爬取统计
        self.stats = {
            'total_pages': 0,
            'success_pages': 0,
            'failed_pages': 0,
            'total_items': 0
        }
        
        # 初始化高级模式
        if self.use_advanced_mode:
            if not is_advanced_mode_available():
                logger.warning("高级模式不可用，将使用标准模式")
                self.use_advanced_mode = False
            else:
                logger.info("已启用高级模式（反反爬虫）")
                self.advanced_crawler = AdvancedCrawler(headless=True)
    
    def fetch_page(self, url, timeout=10):
        """
        获取网页内容
        
        Args:
            url: 目标 URL
            timeout: 超时时间（秒）
            
        Returns:
            BeautifulSoup 对象，失败返回 None
        """
        try:
            # 使用高级模式
            if self.use_advanced_mode and self.advanced_crawler:
                soup = self.advanced_crawler.fetch_page(url, wait_time=3, timeout=timeout)
                if soup:
                    self.stats['success_pages'] += 1
                else:
                    self.stats['failed_pages'] += 1
                return soup
            
            # 使用标准模式
            logger.info(f"正在获取: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            self.stats['success_pages'] += 1
            return soup
            
        except Exception as e:
            logger.error(f"获取失败 {url}: {e}")
            self.stats['failed_pages'] += 1
            return None
    
    def extract_data(self, soup, selectors):
        """
        从页面中提取数据
        
        Args:
            soup: BeautifulSoup 对象
            selectors: 选择器字典，格式：{'字段名': 'CSS选择器'}
            
        Returns:
            提取的数据字典
        """
        data = {}
        
        for field_name, selector in selectors.items():
            try:
                # 支持多种提取方式
                if selector.startswith('@'):
                    # 提取属性，格式：selector@attribute
                    parts = selector.split('@')
                    css_selector = parts[0] if parts[0] else None
                    attribute = parts[1] if len(parts) > 1 else None
                    
                    if css_selector:
                        element = soup.select_one(css_selector)
                        if element and attribute:
                            data[field_name] = element.get(attribute, '')
                        else:
                            data[field_name] = ''
                    else:
                        data[field_name] = ''
                else:
                    # 提取文本内容
                    element = soup.select_one(selector)
                    if element:
                        data[field_name] = element.get_text(strip=True)
                    else:
                        data[field_name] = ''
                        
            except Exception as e:
                logger.warning(f"提取字段 {field_name} 失败: {e}")
                data[field_name] = ''
        
        return data
    
    def extract_list_data(self, soup, list_selector, item_selectors):
        """
        从页面中提取列表数据
        
        Args:
            soup: BeautifulSoup 对象
            list_selector: 列表容器的 CSS 选择器
            item_selectors: 每个列表项的字段选择器字典
            
        Returns:
            提取的数据列表
        """
        results = []
        
        try:
            # 找到所有列表项
            items = soup.select(list_selector)
            logger.info(f"找到 {len(items)} 个列表项")
            
            for item in items:
                data = {}
                
                for field_name, selector in item_selectors.items():
                    try:
                        if selector.startswith('@'):
                            # 提取属性
                            parts = selector.split('@')
                            css_selector = parts[0] if parts[0] else None
                            attribute = parts[1] if len(parts) > 1 else None
                            
                            if css_selector:
                                element = item.select_one(css_selector)
                                if element and attribute:
                                    data[field_name] = element.get(attribute, '')
                                else:
                                    data[field_name] = ''
                            else:
                                # 直接从当前元素提取属性
                                data[field_name] = item.get(attribute, '')
                        else:
                            # 提取文本内容
                            element = item.select_one(selector)
                            if element:
                                data[field_name] = element.get_text(strip=True)
                            else:
                                data[field_name] = ''
                                
                    except Exception as e:
                        logger.warning(f"提取字段 {field_name} 失败: {e}")
                        data[field_name] = ''
                
                if data:
                    results.append(data)
                    self.stats['total_items'] += 1
                    
        except Exception as e:
            logger.error(f"提取列表数据失败: {e}")
        
        return results
    
    def crawl_single_page(self, url, selectors):
        """
        爬取单个页面
        
        Args:
            url: 目标 URL
            selectors: 选择器字典
            
        Returns:
            提取的数据
        """
        self.stats['total_pages'] += 1
        
        soup = self.fetch_page(url)
        if not soup:
            return None
        
        data = self.extract_data(soup, selectors)
        return data
    
    def crawl_list_page(self, url, list_selector, item_selectors, max_items=None):
        """
        爬取列表页面
        
        Args:
            url: 目标 URL
            list_selector: 列表容器选择器
            item_selectors: 列表项字段选择器
            max_items: 最大爬取数量
            
        Returns:
            提取的数据列表
        """
        self.stats['total_pages'] += 1
        
        soup = self.fetch_page(url)
        if not soup:
            return []
        
        results = self.extract_list_data(soup, list_selector, item_selectors)
        
        # 限制数量
        if max_items and len(results) > max_items:
            results = results[:max_items]
        
        return results
    
    def crawl_multiple_pages(self, urls, list_selector, item_selectors, 
                            max_items=None, delay=1):
        """
        爬取多个页面
        
        Args:
            urls: URL 列表
            list_selector: 列表容器选择器
            item_selectors: 列表项字段选择器
            max_items: 最大爬取数量（总计）
            delay: 页面之间的延迟（秒）
            
        Returns:
            所有页面提取的数据列表
        """
        all_results = []
        
        for url in urls:
            if max_items and len(all_results) >= max_items:
                logger.info(f"已达到最大爬取数量 {max_items}，停止爬取")
                break
            
            results = self.crawl_list_page(url, list_selector, item_selectors)
            all_results.extend(results)
            
            # 延迟
            if delay > 0 and url != urls[-1]:
                time.sleep(delay)
        
        # 限制总数量
        if max_items and len(all_results) > max_items:
            all_results = all_results[:max_items]
        
        return all_results
    
    def save_to_json(self, data, filename=None):
        """
        保存数据为 JSON 格式
        
        Args:
            data: 要保存的数据
            filename: 文件名（不含扩展名）
            
        Returns:
            保存的文件路径
        """
        if not filename:
            filename = f"crawled_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存 JSON 失败: {e}")
            return None
    
    def save_to_csv(self, data, filename=None):
        """
        保存数据为 CSV 格式
        
        Args:
            data: 要保存的数据（列表）
            filename: 文件名（不含扩展名）
            
        Returns:
            保存的文件路径
        """
        if not data:
            logger.warning("没有数据可保存")
            return None
        
        if not filename:
            filename = f"crawled_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filepath = os.path.join(self.output_dir, f"{filename}.csv")
        
        try:
            # 获取所有字段名
            fieldnames = list(data[0].keys())
            
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存 CSV 失败: {e}")
            return None
    
    def get_stats(self):
        """获取爬取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_pages': 0,
            'success_pages': 0,
            'failed_pages': 0,
            'total_items': 0
        }
    
    def close(self):
        """关闭爬虫，释放资源"""
        if self.advanced_crawler:
            self.advanced_crawler.close()
            self.advanced_crawler = None
    
    def __del__(self):
        """析构函数"""
        self.close()


def main():
    """示例用法"""
    # 示例 1：爬取单个页面
    print("=" * 60)
    print("示例 1：爬取单个页面")
    print("=" * 60)
    
    crawler = UniversalCrawler(
        base_url='https://example.com',
        output_dir='data/example'
    )
    
    # 定义要提取的字段和选择器
    selectors = {
        'title': 'h1',
        'description': 'p.description',
        'author': 'span.author'
    }
    
    # data = crawler.crawl_single_page('https://example.com/page', selectors)
    # print(f"提取的数据: {data}")
    
    # 示例 2：爬取列表页面
    print("\n" + "=" * 60)
    print("示例 2：爬取列表页面")
    print("=" * 60)
    
    list_selector = 'div.item'  # 列表容器
    item_selectors = {
        'title': 'h2.title',
        'price': 'span.price',
        'link': 'a@href'  # 提取 href 属性
    }
    
    # results = crawler.crawl_list_page(
    #     'https://example.com/list',
    #     list_selector,
    #     item_selectors,
    #     max_items=10
    # )
    
    # print(f"提取了 {len(results)} 条数据")
    
    # 保存数据
    # crawler.save_to_json(results, 'example_data')
    # crawler.save_to_csv(results, 'example_data')
    
    # 显示统计
    # stats = crawler.get_stats()
    # print(f"\n爬取统计: {stats}")
    
    print("\n使用说明:")
    print("1. 创建 UniversalCrawler 实例，指定 base_url 和 output_dir")
    print("2. 定义 CSS 选择器来指定要提取的数据")
    print("3. 调用 crawl_single_page 或 crawl_list_page 爬取数据")
    print("4. 使用 save_to_json 或 save_to_csv 保存数据")
    print("\nCSS 选择器示例:")
    print("  'h1' - 提取 h1 标签的文本")
    print("  'div.class' - 提取 class 为 class 的 div 的文本")
    print("  'a@href' - 提取 a 标签的 href 属性")
    print("  'img@src' - 提取 img 标签的 src 属性")


if __name__ == '__main__':
    main()
