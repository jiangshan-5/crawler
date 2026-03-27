#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多源图标爬虫 - 从多个免费图标网站爬取图标进行对比
支持的网站：
1. Flaticon (flaticon.com)
2. Icons8 (icons8.com)
3. Iconmonstr (iconmonstr.com)
4. Feather Icons (feathericons.com)
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
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/multi_icon_crawler_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class MultiSourceIconCrawler:
    """多源图标爬虫"""
    
    def __init__(self, output_dir='data/icons_comparison'):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 为每个来源创建子目录
        self.sources = ['flaticon', 'icons8', 'iconmonstr', 'feather', 'heroicons']
        for source in self.sources:
            os.makedirs(os.path.join(self.output_dir, source), exist_ok=True)
    
    def search_flaticon(self, keyword, limit=5):
        """
        搜索 Flaticon
        注意：Flaticon 需要登录才能下载，这里只获取预览图
        """
        try:
            url = f'https://www.flaticon.com/search'
            params = {'word': keyword}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找图标元素
            icons = []
            icon_elements = soup.find_all('img', class_=re.compile('icon'), limit=limit)
            
            for idx, img in enumerate(icon_elements):
                img_url = img.get('src') or img.get('data-src')
                if img_url and 'http' in img_url:
                    icons.append({
                        'source': 'flaticon',
                        'url': img_url,
                        'name': f'{keyword}_{idx+1}',
                        'keyword': keyword
                    })
            
            logger.info(f"Flaticon: 找到 {len(icons)} 个 '{keyword}' 图标")
            return icons
            
        except Exception as e:
            logger.error(f"Flaticon 搜索失败: {e}")
            return []
    
    def search_icons8(self, keyword, limit=5):
        """
        搜索 Icons8
        Icons8 提供免费的小尺寸图标
        """
        try:
            # Icons8 API endpoint
            url = f'https://search.icons8.com/api/iconsets/v5/search'
            params = {
                'term': keyword,
                'amount': limit,
                'offset': 0,
                'platform': 'all'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            icons = []
            
            if 'icons' in data:
                for idx, icon in enumerate(data['icons'][:limit]):
                    # Icons8 图标 URL 格式
                    icon_id = icon.get('id', '')
                    platform = icon.get('platform', 'ios')
                    
                    # 构建 PNG URL (40x40)
                    img_url = f'https://img.icons8.com/{platform}/40/000000/{icon_id}.png'
                    
                    icons.append({
                        'source': 'icons8',
                        'url': img_url,
                        'name': f'{keyword}_{idx+1}',
                        'keyword': keyword,
                        'id': icon_id
                    })
            
            logger.info(f"Icons8: 找到 {len(icons)} 个 '{keyword}' 图标")
            return icons
            
        except Exception as e:
            logger.error(f"Icons8 搜索失败: {e}")
            return []
    
    def search_iconmonstr(self, keyword, limit=5):
        """
        搜索 Iconmonstr
        完全免费，无需注册
        """
        try:
            url = f'https://iconmonstr.com/'
            params = {'s': keyword}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            icons = []
            # 查找图标链接
            icon_links = soup.find_all('a', href=re.compile(r'/.*-\d+/'), limit=limit)
            
            for idx, link in enumerate(icon_links[:limit]):
                icon_page = link.get('href')
                if icon_page:
                    # 构建完整 URL
                    full_url = f'https://iconmonstr.com{icon_page}'
                    
                    icons.append({
                        'source': 'iconmonstr',
                        'url': full_url,
                        'name': f'{keyword}_{idx+1}',
                        'keyword': keyword,
                        'page_url': full_url
                    })
            
            logger.info(f"Iconmonstr: 找到 {len(icons)} 个 '{keyword}' 图标")
            return icons
            
        except Exception as e:
            logger.error(f"Iconmonstr 搜索失败: {e}")
            return []
    
    def search_feather_icons(self, keyword):
        """
        搜索 Feather Icons
        开源图标集，简洁美观
        """
        try:
            # Feather Icons 是固定的图标集
            feather_icons = {
                'list': 'list',
                'add': 'plus',
                'chart': 'bar-chart-2',
                'settings': 'settings',
                'menu': 'menu',
                'home': 'home',
                'user': 'user',
                'search': 'search'
            }
            
            icon_name = feather_icons.get(keyword.lower())
            if not icon_name:
                # 尝试模糊匹配
                for key, value in feather_icons.items():
                    if keyword.lower() in key or key in keyword.lower():
                        icon_name = value
                        break
            
            if icon_name:
                # Feather Icons CDN
                svg_url = f'https://unpkg.com/feather-icons/dist/icons/{icon_name}.svg'
                
                return [{
                    'source': 'feather',
                    'url': svg_url,
                    'name': keyword,
                    'keyword': keyword,
                    'icon_name': icon_name
                }]
            
            logger.info(f"Feather Icons: 未找到 '{keyword}' 对应的图标")
            return []
            
        except Exception as e:
            logger.error(f"Feather Icons 搜索失败: {e}")
            return []
    
    def search_heroicons(self, keyword):
        """
        搜索 Heroicons
        Tailwind CSS 团队开发的开源图标
        """
        try:
            # Heroicons 常用图标映射
            hero_icons = {
                'list': 'list-bullet',
                'add': 'plus',
                'chart': 'chart-bar',
                'settings': 'cog',
                'menu': 'bars-3',
                'home': 'home',
                'user': 'user',
                'search': 'magnifying-glass'
            }
            
            icon_name = hero_icons.get(keyword.lower())
            if not icon_name:
                for key, value in hero_icons.items():
                    if keyword.lower() in key or key in keyword.lower():
                        icon_name = value
                        break
            
            if icon_name:
                # Heroicons GitHub raw URL
                svg_url = f'https://raw.githubusercontent.com/tailwindlabs/heroicons/master/src/24/outline/{icon_name}.svg'
                
                return [{
                    'source': 'heroicons',
                    'url': svg_url,
                    'name': keyword,
                    'keyword': keyword,
                    'icon_name': icon_name
                }]
            
            logger.info(f"Heroicons: 未找到 '{keyword}' 对应的图标")
            return []
            
        except Exception as e:
            logger.error(f"Heroicons 搜索失败: {e}")
            return []
    
    def download_icon(self, icon_info):
        """下载图标"""
        try:
            source = icon_info['source']
            url = icon_info['url']
            name = icon_info['name']
            
            # 如果是页面 URL，需要先获取下载链接
            if source == 'iconmonstr' and 'page_url' in icon_info:
                url = self._get_iconmonstr_download_url(icon_info['page_url'])
                if not url:
                    return None
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 确定文件扩展名
            content_type = response.headers.get('content-type', '')
            if 'svg' in content_type or url.endswith('.svg'):
                ext = 'svg'
                content = response.text
            else:
                ext = 'png'
                content = response.content
            
            # 保存文件
            filename = f'{name}.{ext}'
            filepath = os.path.join(self.output_dir, source, filename)
            
            if ext == 'svg':
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(filepath, 'wb') as f:
                    f.write(content)
            
            logger.info(f"✓ 下载成功: {source}/{filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"下载失败 {icon_info.get('name')}: {e}")
            return None
    
    def _get_iconmonstr_download_url(self, page_url):
        """获取 Iconmonstr 的下载链接"""
        try:
            response = self.session.get(page_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找 PNG 下载链接
            download_link = soup.find('a', href=re.compile(r'.*\.png'))
            if download_link:
                return download_link.get('href')
            
            return None
            
        except Exception as e:
            logger.error(f"获取下载链接失败: {e}")
            return None
    
    def search_all_sources(self, keyword, limit=5):
        """从所有来源搜索图标"""
        logger.info(f"\n{'='*60}")
        logger.info(f"搜索关键词: {keyword}")
        logger.info(f"{'='*60}\n")
        
        all_icons = []
        
        # 搜索各个来源
        sources_methods = [
            ('Flaticon', lambda: self.search_flaticon(keyword, limit)),
            ('Icons8', lambda: self.search_icons8(keyword, limit)),
            ('Iconmonstr', lambda: self.search_iconmonstr(keyword, limit)),
            ('Feather Icons', lambda: self.search_feather_icons(keyword)),
            ('Heroicons', lambda: self.search_heroicons(keyword))
        ]
        
        for source_name, search_method in sources_methods:
            try:
                logger.info(f"正在搜索 {source_name}...")
                icons = search_method()
                all_icons.extend(icons)
                time.sleep(1)  # 避免请求过快
            except Exception as e:
                logger.error(f"{source_name} 搜索出错: {e}")
        
        logger.info(f"\n总共找到 {len(all_icons)} 个图标\n")
        return all_icons
    
    def download_all_icons(self, icons):
        """下载所有图标"""
        logger.info(f"开始下载 {len(icons)} 个图标...\n")
        
        results = []
        for icon in icons:
            filepath = self.download_icon(icon)
            if filepath:
                results.append({
                    **icon,
                    'filepath': filepath,
                    'downloaded': True
                })
                time.sleep(0.5)  # 避免请求过快
            else:
                results.append({
                    **icon,
                    'downloaded': False
                })
        
        success_count = sum(1 for r in results if r.get('downloaded'))
        logger.info(f"\n下载完成: {success_count}/{len(icons)} 成功")
        
        return results
    
    def save_results(self, results, filename='icon_comparison_results.json'):
        """保存结果"""
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def generate_comparison_html(self, results, keywords):
        """生成对比页面"""
        html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图标对比</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .keyword-section {
            background: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .keyword-title {
            font-size: 24px;
            color: #333;
            margin-bottom: 15px;
            border-bottom: 2px solid #3cc51f;
            padding-bottom: 10px;
        }
        .icons-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .icon-card {
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            transition: transform 0.2s;
        }
        .icon-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .icon-image {
            width: 80px;
            height: 80px;
            margin: 10px auto;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .icon-image img {
            max-width: 100%;
            max-height: 100%;
        }
        .icon-source {
            font-weight: bold;
            color: #3cc51f;
            margin-top: 10px;
        }
        .icon-name {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }
        .stats {
            background: #e8f5e9;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>🎨 图标对比结果</h1>
    <div class="stats">
        <p>共搜索 <strong>{keyword_count}</strong> 个关键词，找到 <strong>{total_icons}</strong> 个图标</p>
    </div>
"""
        
        # 按关键词分组
        grouped = {}
        for result in results:
            keyword = result.get('keyword', 'unknown')
            if keyword not in grouped:
                grouped[keyword] = []
            grouped[keyword].append(result)
        
        # 生成每个关键词的部分
        for keyword, icons in grouped.items():
            html += f"""
    <div class="keyword-section">
        <div class="keyword-title">🔍 {keyword}</div>
        <div class="icons-grid">
"""
            for icon in icons:
                if icon.get('downloaded'):
                    filepath = icon['filepath'].replace('\\', '/')
                    rel_path = filepath.split('icons_comparison/')[-1]
                    html += f"""
            <div class="icon-card">
                <div class="icon-image">
                    <img src="{rel_path}" alt="{icon['name']}">
                </div>
                <div class="icon-source">{icon['source']}</div>
                <div class="icon-name">{icon['name']}</div>
            </div>
"""
            html += """
        </div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        # 保存 HTML
        html_path = os.path.join(self.output_dir, 'comparison.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html.format(
                keyword_count=len(keywords),
                total_icons=len(results)
            ))
        
        logger.info(f"✓ 对比页面已生成: {html_path}")
        return html_path


def main():
    """主函数"""
    import argparse
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(
        description='多源图标爬虫 - 从多个免费图标网站爬取图标',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 爬取所有来源
  python multi_source_icon_crawler.py
  
  # 只爬取 Feather Icons
  python multi_source_icon_crawler.py --sources feather
  
  # 爬取 Feather 和 Heroicons
  python multi_source_icon_crawler.py --sources feather heroicons
  
  # 自定义关键词
  python multi_source_icon_crawler.py --keywords home user search
  
  # 指定来源和关键词
  python multi_source_icon_crawler.py --sources feather --keywords menu home
  
  # 增加每个关键词的下载数量
  python multi_source_icon_crawler.py --limit 5

可用的来源:
  - flaticon    (Flaticon.com - 需要登录)
  - icons8      (Icons8.com - 部分免费)
  - iconmonstr  (Iconmonstr.com - 完全免费)
  - feather     (Feather Icons - 开源)
  - heroicons   (Heroicons - 开源)
  - all         (所有来源)
        """
    )
    
    parser.add_argument(
        '--sources', '-s',
        nargs='+',
        choices=['flaticon', 'icons8', 'iconmonstr', 'feather', 'heroicons', 'all'],
        default=['all'],
        help='指定要爬取的图标来源（可多选）'
    )
    
    parser.add_argument(
        '--keywords', '-k',
        nargs='+',
        default=['list', 'add', 'chart', 'settings'],
        help='指定要搜索的关键词（可多个）'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=3,
        help='每个关键词下载的图标数量（默认: 3）'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='data/icons_comparison',
        help='输出目录（默认: data/icons_comparison）'
    )
    
    args = parser.parse_args()
    
    # 处理 'all' 选项
    if 'all' in args.sources:
        selected_sources = ['flaticon', 'icons8', 'iconmonstr', 'feather', 'heroicons']
    else:
        selected_sources = args.sources
    
    logger.info("=" * 60)
    logger.info("多源图标爬虫启动")
    logger.info("=" * 60)
    logger.info(f"选择的来源: {', '.join(selected_sources)}")
    logger.info(f"搜索关键词: {', '.join(args.keywords)}")
    logger.info(f"每个关键词下载数量: {args.limit}")
    logger.info(f"输出目录: {args.output}")
    logger.info("=" * 60)
    
    crawler = MultiSourceIconCrawler(output_dir=args.output)
    
    all_results = []
    
    # 搜索每个关键词
    for keyword in args.keywords:
        logger.info(f"\n{'='*60}")
        logger.info(f"搜索关键词: {keyword}")
        logger.info(f"{'='*60}\n")
        
        icons = []
        
        # 根据选择的来源进行搜索
        if 'flaticon' in selected_sources:
            logger.info("正在搜索 Flaticon...")
            icons.extend(crawler.search_flaticon(keyword, args.limit))
            time.sleep(1)
        
        if 'icons8' in selected_sources:
            logger.info("正在搜索 Icons8...")
            icons.extend(crawler.search_icons8(keyword, args.limit))
            time.sleep(1)
        
        if 'iconmonstr' in selected_sources:
            logger.info("正在搜索 Iconmonstr...")
            icons.extend(crawler.search_iconmonstr(keyword, args.limit))
            time.sleep(1)
        
        if 'feather' in selected_sources:
            logger.info("正在搜索 Feather Icons...")
            icons.extend(crawler.search_feather_icons(keyword))
            time.sleep(1)
        
        if 'heroicons' in selected_sources:
            logger.info("正在搜索 Heroicons...")
            icons.extend(crawler.search_heroicons(keyword))
            time.sleep(1)
        
        logger.info(f"\n总共找到 {len(icons)} 个图标\n")
        
        # 下载图标
        results = crawler.download_all_icons(icons)
        all_results.extend(results)
    
    # 保存结果
    crawler.save_results(all_results)
    
    # 生成对比页面
    try:
        html_path = crawler.generate_comparison_html(all_results, args.keywords)
        logger.info(f"✓ 对比页面: {html_path}")
    except Exception as e:
        logger.error(f"生成对比页面失败: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ 爬取完成！")
    logger.info(f"✓ 图标保存在: {crawler.output_dir}")
    
    # 统计结果
    success_count = sum(1 for r in all_results if r.get('downloaded'))
    logger.info(f"✓ 成功下载: {success_count}/{len(all_results)}")
    
    # 按来源统计
    source_stats = {}
    for result in all_results:
        if result.get('downloaded'):
            source = result.get('source', 'unknown')
            source_stats[source] = source_stats.get(source, 0) + 1
    
    if source_stats:
        logger.info("\n按来源统计:")
        for source, count in source_stats.items():
            logger.info(f"  {source}: {count} 个")
    
    logger.info("=" * 60)
    
    if success_count > 0:
        logger.info(f"\n查看下载的图标: {crawler.output_dir}")
        logger.info("打开 comparison.html 查看所有图标并选择最优的！")
    else:
        logger.warning("\n没有成功下载任何图标，请检查网络连接或尝试其他来源")


if __name__ == '__main__':
    main()
