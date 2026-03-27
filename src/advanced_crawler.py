#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级爬虫模块 - 支持反反爬虫
使用 undetected-chromedriver 绕过 Cloudflare、DataDome 等反爬虫系统
"""

import logging
import time
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# 延迟导入，避免未安装时报错
def _check_availability():
    """检查依赖是否可用"""
    try:
        import undetected_chromedriver as uc
        return True
    except ImportError as e:
        logger.warning(f"undetected-chromedriver 未安装，高级模式不可用: {e}")
        return False

ADVANCED_MODE_AVAILABLE = _check_availability()


class AdvancedCrawler:
    """高级爬虫 - 支持JavaScript渲染和反爬虫绕过"""
    
    def __init__(self, headless=True):
        """
        初始化高级爬虫
        
        Args:
            headless: 是否使用无头模式
        """
        self.driver = None
        self.headless = headless
        
        if not ADVANCED_MODE_AVAILABLE:
            raise ImportError(
                "高级模式需要安装 undetected-chromedriver\n"
                "请运行: pip install undetected-chromedriver"
            )
    
    def start(self):
        """启动浏览器"""
        if self.driver:
            return
        
        try:
            # 导入 undetected_chromedriver
            import undetected_chromedriver as uc
            
            logger.info("正在启动高级爬虫引擎...")
            options = uc.ChromeOptions()
            
            if self.headless:
                options.add_argument('--headless=new')
            
            # 优化选项
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            self.driver = uc.Chrome(options=options, use_subprocess=False)
            logger.info("高级爬虫引擎启动成功")
            
        except Exception as e:
            logger.error(f"启动高级爬虫失败: {e}")
            raise
    
    def fetch_page(self, url, wait_time=3, timeout=30):
        """
        获取网页内容（支持JavaScript渲染）
        
        Args:
            url: 目标URL
            wait_time: 页面加载后等待时间（秒）
            timeout: 超时时间（秒）
            
        Returns:
            BeautifulSoup对象，失败返回None
        """
        if not self.driver:
            self.start()
        
        try:
            logger.info(f"[高级模式] 正在获取: {url}")
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(timeout)
            
            # 访问页面
            self.driver.get(url)
            
            # 等待JavaScript执行
            time.sleep(wait_time)
            
            # 获取渲染后的HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            logger.info(f"[高级模式] 页面获取成功，HTML长度: {len(html)}")
            return soup
            
        except Exception as e:
            logger.error(f"[高级模式] 获取失败 {url}: {e}")
            return None
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("高级爬虫引擎已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器失败: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """上下文管理器支持"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器支持"""
        self.close()
    
    def __del__(self):
        """析构函数"""
        self.close()


def is_advanced_mode_available():
    """检查高级模式是否可用（动态检测）"""
    # 每次调用都重新检测，确保能检测到新安装的依赖
    try:
        import undetected_chromedriver as uc
        return True
    except ImportError:
        return False
