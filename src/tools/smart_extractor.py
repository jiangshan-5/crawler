#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能内容提取器
支持多种自动提取方法，降低爬虫使用难度
"""

import requests
import logging
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)


class SmartExtractor:
    """智能内容提取器 - 自动识别和提取网页主要内容"""
    
    def __init__(self, method='auto', jina_api_key=None):
        """
        初始化智能提取器
        
        Args:
            method: 提取方法
                - 'auto': 自动选择最佳方法（推荐）
                - 'trafilatura': 使用 Trafilatura（离线、免费）
                - 'jina': 使用 Jina Reader API（在线、免费）
                - 'readability': 使用 ReadabiliPy
            jina_api_key: Jina API Key（可选，提高速率限制）
        """
        self.method = method
        self.jina_api_key = jina_api_key
        
        # 检查依赖
        self.trafilatura_available = self._check_trafilatura()
        self.readability_available = self._check_readability()
    
    def _check_trafilatura(self):
        """检查 Trafilatura 是否可用"""
        try:
            import trafilatura
            return True
        except ImportError:
            logger.warning("Trafilatura 未安装，运行: pip install trafilatura")
            return False
    
    def _check_readability(self):
        """检查 ReadabiliPy 是否可用"""
        try:
            from readabilipy import simple_json_from_html_string
            return True
        except ImportError:
            logger.warning("ReadabiliPy 未安装，运行: pip install readabilipy")
            return False
    
    def extract(self, url, output_format='markdown') -> Optional[str]:
        """
        智能提取网页内容
        
        Args:
            url: 目标 URL
            output_format: 输出格式 ('markdown', 'json', 'text')
            
        Returns:
            提取的内容，失败返回 None
        """
        if self.method == 'auto':
            return self._extract_auto(url, output_format)
        elif self.method == 'trafilatura':
            return self._extract_with_trafilatura(url, output_format)
        elif self.method == 'jina':
            return self._extract_with_jina(url, output_format)
        elif self.method == 'readability':
            return self._extract_with_readability(url, output_format)
        else:
            logger.error(f"未知的提取方法: {self.method}")
            return None
    
    def _extract_auto(self, url, output_format):
        """自动选择最佳提取方法"""
        # 优先级: Trafilatura > Jina > Readability
        
        # 1. 尝试 Trafilatura（最快、离线）
        if self.trafilatura_available:
            logger.info("使用 Trafilatura 提取...")
            result = self._extract_with_trafilatura(url, output_format)
            if result and self._validate_content(result):
                logger.info("✓ Trafilatura 提取成功")
                return result
        
        # 2. 尝试 Jina Reader（在线、强大）
        logger.info("使用 Jina Reader 提取...")
        result = self._extract_with_jina(url, output_format)
        if result and self._validate_content(result):
            logger.info("✓ Jina Reader 提取成功")
            return result
        
        # 3. 尝试 ReadabiliPy
        if self.readability_available:
            logger.info("使用 ReadabiliPy 提取...")
            result = self._extract_with_readability(url, output_format)
            if result and self._validate_content(result):
                logger.info("✓ ReadabiliPy 提取成功")
                return result
        
        logger.error("所有提取方法都失败")
        return None
    
    def _extract_with_trafilatura(self, url, output_format):
        """使用 Trafilatura 提取"""
        if not self.trafilatura_available:
            return None
        
        try:
            import trafilatura
            
            # 下载网页
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                logger.error("下载网页失败")
                return None
            
            # 提取内容
            if output_format == 'json':
                result = trafilatura.extract(
                    downloaded,
                    output_format='json',
                    with_metadata=True,
                    include_comments=False,
                    include_tables=True
                )
            else:
                result = trafilatura.extract(
                    downloaded,
                    output_format=output_format,
                    include_comments=False,
                    include_tables=True
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Trafilatura 提取失败: {e}")
            return None
    
    def _extract_with_jina(self, url, output_format):
        """使用 Jina Reader API 提取"""
        try:
            # 构建请求
            jina_url = f"https://r.jina.ai/{url}"
            headers = {}
            
            if self.jina_api_key:
                headers['Authorization'] = f'Bearer {self.jina_api_key}'
            
            # 根据输出格式设置请求头
            if output_format == 'json':
                headers['Accept'] = 'application/json'
            elif output_format == 'markdown':
                headers['Accept'] = 'text/markdown'
            else:
                headers['Accept'] = 'text/plain'
            
            # 发送请求
            response = requests.get(jina_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            logger.error(f"Jina Reader 提取失败: {e}")
            return None
    
    def _extract_with_readability(self, url, output_format):
        """使用 ReadabiliPy 提取"""
        if not self.readability_available:
            return None
        
        try:
            from readabilipy import simple_json_from_html_string
            
            # 下载网页
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # 提取内容
            article = simple_json_from_html_string(
                response.text,
                use_readability=True
            )
            
            if output_format == 'json':
                return json.dumps(article, ensure_ascii=False, indent=2)
            elif output_format == 'markdown':
                # 简单转换为 Markdown
                title = article.get('title', '')
                content = article.get('plain_text', '')
                return f"# {title}\n\n{content}"
            else:
                return article.get('plain_text', '')
            
        except Exception as e:
            logger.error(f"ReadabiliPy 提取失败: {e}")
            return None
    
    def _validate_content(self, content):
        """验证提取的内容是否有效"""
        if not content:
            return False
        
        # 检查长度
        if len(content) < 50:
            return False
        
        # 检查是否包含常见的无效内容
        invalid_keywords = ['404', 'not found', 'access denied', 'page not found']
        content_lower = content.lower()
        if any(kw in content_lower for kw in invalid_keywords):
            return False
        
        return True
    
    def extract_structured(self, url, fields: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        提取结构化数据（实验性功能）
        
        Args:
            url: 目标 URL
            fields: 要提取的字段描述
                例如: {'title': '文章标题', 'author': '作者名', 'date': '发布日期'}
            
        Returns:
            提取的结构化数据字典
        """
        # 先提取主要内容
        content = self.extract(url, output_format='text')
        if not content:
            return None
        
        # TODO: 使用 AI 或规则提取结构化数据
        # 这里可以集成 LLM API 来智能提取
        
        logger.warning("结构化提取功能尚未实现，返回原始内容")
        return {
            'url': url,
            'content': content,
            'fields': fields
        }


def demo_trafilatura():
    """演示 Trafilatura 用法"""
    print("=" * 60)
    print("演示 1: Trafilatura - 自动提取文章内容")
    print("=" * 60)
    
    try:
        import trafilatura
        
        # 测试 URL
        url = "https://en.wikipedia.org/wiki/Web_scraping"
        
        print(f"\n目标 URL: {url}")
        print("正在提取...")
        
        # 下载
        downloaded = trafilatura.fetch_url(url)
        
        # 提取为 Markdown
        result = trafilatura.extract(
            downloaded,
            output_format='markdown',
            include_comments=False,
            include_tables=True
        )
        
        if result:
            print(f"\n✓ 提取成功！")
            print(f"内容长度: {len(result)} 字符")
            print(f"\n前 500 字符预览:")
            print("-" * 60)
            print(result[:500])
            print("-" * 60)
        else:
            print("✗ 提取失败")
    
    except ImportError:
        print("✗ Trafilatura 未安装")
        print("安装命令: pip install trafilatura")
    except Exception as e:
        print(f"✗ 错误: {e}")


def demo_jina():
    """演示 Jina Reader 用法"""
    print("\n" + "=" * 60)
    print("演示 2: Jina Reader API - 零配置提取")
    print("=" * 60)
    
    try:
        # 测试 URL
        url = "https://en.wikipedia.org/wiki/Web_scraping"
        
        print(f"\n目标 URL: {url}")
        print("正在提取...")
        
        # 调用 Jina Reader API
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=30)
        response.raise_for_status()
        
        result = response.text
        
        if result:
            print(f"\n✓ 提取成功！")
            print(f"内容长度: {len(result)} 字符")
            print(f"\n前 500 字符预览:")
            print("-" * 60)
            print(result[:500])
            print("-" * 60)
        else:
            print("✗ 提取失败")
    
    except Exception as e:
        print(f"✗ 错误: {e}")


def demo_smart_extractor():
    """演示智能提取器"""
    print("\n" + "=" * 60)
    print("演示 3: 智能提取器 - 自动选择最佳方法")
    print("=" * 60)
    
    extractor = SmartExtractor(method='auto')
    
    # 测试 URL
    url = "https://en.wikipedia.org/wiki/Web_scraping"
    
    print(f"\n目标 URL: {url}")
    print("正在智能提取...")
    
    result = extractor.extract(url, output_format='markdown')
    
    if result:
        print(f"\n✓ 提取成功！")
        print(f"内容长度: {len(result)} 字符")
        print(f"\n前 500 字符预览:")
        print("-" * 60)
        print(result[:500])
        print("-" * 60)
    else:
        print("✗ 提取失败")


def main():
    """运行所有演示"""
    print("\n🤖 智能内容提取器演示")
    print("自动提取网页内容，无需手动编写选择器！\n")
    
    # 演示 1: Trafilatura
    demo_trafilatura()
    
    # 演示 2: Jina Reader
    demo_jina()
    
    # 演示 3: 智能提取器
    demo_smart_extractor()
    
    print("\n" + "=" * 60)
    print("📚 使用建议")
    print("=" * 60)
    print("\n1. 提取文章/博客: 使用 Trafilatura 或 Jina Reader")
    print("2. 提取产品列表: 使用手动选择器（更精确）")
    print("3. 快速测试: 使用 Jina Reader（零配置）")
    print("4. 生产环境: 使用 Trafilatura（免费、稳定）")
    
    print("\n安装依赖:")
    print("  pip install trafilatura      # 推荐")
    print("  pip install readabilipy       # 可选")


if __name__ == '__main__':
    main()
