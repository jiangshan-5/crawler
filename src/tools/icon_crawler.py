#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标爬虫 - 从免费图标资源库下载图标
支持从 iconfont.cn 搜索和下载图标
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import logging
from datetime import datetime
from PIL import Image
from io import BytesIO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/icon_crawler_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class IconCrawler:
    """图标爬虫类"""
    
    def __init__(self, output_dir='data/icons'):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
    def search_icons_iconfont(self, keyword, page=1, page_size=20):
        """
        在 iconfont.cn 搜索图标
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
        
        Returns:
            图标列表
        """
        try:
            # iconfont.cn 的搜索 API
            url = 'https://www.iconfont.cn/api/icon/search.json'
            params = {
                'q': keyword,
                'page': page,
                'pageSize': page_size,
                't': int(time.time() * 1000)
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 200:
                icons = data.get('data', {}).get('icons', [])
                logger.info(f"搜索 '{keyword}' 找到 {len(icons)} 个图标")
                return icons
            else:
                logger.error(f"搜索失败: {data.get('message')}")
                return []
                
        except Exception as e:
            logger.error(f"搜索图标失败: {e}")
            return []
    
    def download_icon_svg(self, icon_id, icon_name, save_path=None):
        """
        下载 SVG 格式图标
        
        Args:
            icon_id: 图标 ID
            icon_name: 图标名称
            save_path: 保存路径
        
        Returns:
            保存的文件路径
        """
        try:
            # iconfont.cn 的 SVG 下载地址
            url = f'https://www.iconfont.cn/api/icon/getIconSVG.json'
            params = {
                'id': icon_id,
                't': int(time.time() * 1000)
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 200:
                svg_content = data.get('data', '')
                
                if not save_path:
                    save_path = os.path.join(self.output_dir, f'{icon_name}.svg')
                
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                
                logger.info(f"✓ 下载成功: {save_path}")
                return save_path
            else:
                logger.error(f"下载失败: {data.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"下载图标失败 {icon_name}: {e}")
            return None
    
    def download_icon_png(self, icon_id, icon_name, size=40, color='000000', save_path=None):
        """
        下载 PNG 格式图标
        
        Args:
            icon_id: 图标 ID
            icon_name: 图标名称
            size: 图标尺寸（像素）
            color: 图标颜色（十六进制，不带#）
            save_path: 保存路径
        
        Returns:
            保存的文件路径
        """
        try:
            # iconfont.cn 的 PNG 下载地址
            url = f'https://www.iconfont.cn/api/icon/getIconPNG.json'
            params = {
                'id': icon_id,
                'size': size,
                'color': color,
                't': int(time.time() * 1000)
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 200:
                # 获取图片 URL
                img_url = data.get('data', '')
                
                if img_url:
                    # 下载图片
                    img_response = self.session.get(img_url, timeout=10)
                    img_response.raise_for_status()
                    
                    if not save_path:
                        save_path = os.path.join(self.output_dir, f'{icon_name}.png')
                    
                    with open(save_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    logger.info(f"✓ 下载成功: {save_path}")
                    return save_path
                else:
                    logger.error(f"未获取到图片 URL")
                    return None
            else:
                logger.error(f"下载失败: {data.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"下载图标失败 {icon_name}: {e}")
            return None
    
    def download_icons_for_miniapp(self, keywords_dict, size=40):
        """
        为小程序下载所需的图标
        
        Args:
            keywords_dict: 关键词字典 {文件名: 搜索关键词}
            size: 图标尺寸
        
        Returns:
            下载结果
        """
        results = {}
        
        for filename, keyword in keywords_dict.items():
            logger.info(f"\n正在搜索: {keyword}")
            
            # 搜索图标
            icons = self.search_icons_iconfont(keyword, page=1, page_size=10)
            
            if not icons:
                logger.warning(f"未找到 '{keyword}' 相关图标")
                results[filename] = None
                continue
            
            # 选择第一个图标
            icon = icons[0]
            icon_id = icon.get('id')
            icon_name = icon.get('name', filename)
            
            logger.info(f"选择图标: {icon_name} (ID: {icon_id})")
            
            # 下载灰色版本（未激活）
            gray_path = os.path.join(self.output_dir, f'{filename}.png')
            self.download_icon_png(icon_id, filename, size=size, color='7A7E83', save_path=gray_path)
            time.sleep(0.5)  # 避免请求过快
            
            # 下载绿色版本（激活）
            green_path = os.path.join(self.output_dir, f'{filename}-active.png')
            self.download_icon_png(icon_id, f'{filename}-active', size=size, color='3cc51f', save_path=green_path)
            time.sleep(0.5)
            
            results[filename] = {
                'normal': gray_path,
                'active': green_path,
                'icon_id': icon_id,
                'icon_name': icon_name
            }
        
        return results
    
    def save_results(self, results, filename='icon_download_results.json'):
        """保存下载结果"""
        filepath = os.path.join('data', filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("图标爬虫启动 - 为小程序下载图标")
    logger.info("=" * 60)
    
    # 创建爬虫实例
    crawler = IconCrawler(output_dir='../accounting-miniapp/src/static/icons')
    
    # 定义需要下载的图标
    # 格式: {文件名: 搜索关键词}
    icons_needed = {
        'list': '列表',
        'add': '添加',
        'chart': '图表',
        'settings': '设置'
    }
    
    logger.info(f"\n需要下载的图标: {list(icons_needed.keys())}")
    logger.info(f"输出目录: {crawler.output_dir}\n")
    
    # 下载图标
    results = crawler.download_icons_for_miniapp(icons_needed, size=40)
    
    # 保存结果
    crawler.save_results(results)
    
    # 统计结果
    success_count = sum(1 for v in results.values() if v is not None)
    logger.info("\n" + "=" * 60)
    logger.info(f"下载完成! 成功: {success_count}/{len(icons_needed)}")
    logger.info("=" * 60)
    
    # 显示下载的文件
    if success_count > 0:
        logger.info("\n已下载的图标:")
        for name, result in results.items():
            if result:
                logger.info(f"  ✓ {name}: {result['normal']}, {result['active']}")


if __name__ == '__main__':
    main()
