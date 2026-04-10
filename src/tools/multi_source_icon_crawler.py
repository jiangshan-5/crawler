#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多源图标爬虫 - 核心搜索与下载逻辑
支持: Flaticon, Icons8, Iconmonstr, Feather Icons, Heroicons
"""

import os
import re
import time
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MultiSourceIconCrawler:
    """多源图标爬虫 - 核心类"""

    def __init__(self, output_dir='data/icons_comparison'):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self.sources = ['flaticon', 'icons8', 'iconmonstr', 'feather', 'heroicons']
        for source in self.sources:
            os.makedirs(os.path.join(self.output_dir, source), exist_ok=True)

    def search_flaticon(self, keyword, limit=5):
        """搜索 Flaticon（只获取预览图，下载需登录）"""
        try:
            response = self.session.get('https://www.flaticon.com/search',
                                        params={'word': keyword}, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            icons = []
            for idx, img in enumerate(soup.find_all('img', class_=re.compile('icon'), limit=limit)):
                img_url = img.get('src') or img.get('data-src')
                if img_url and 'http' in img_url:
                    icons.append({'source': 'flaticon', 'url': img_url,
                                  'name': f'{keyword}_{idx+1}', 'keyword': keyword})
            logger.info(f"Flaticon: 找到 {len(icons)} 个 '{keyword}' 图标")
            return icons
        except Exception as e:
            logger.error(f"Flaticon 搜索失败: {e}")
            return []

    def search_icons8(self, keyword, limit=5):
        """搜索 Icons8 API"""
        try:
            response = self.session.get(
                'https://search.icons8.com/api/iconsets/v5/search',
                params={'term': keyword, 'amount': limit, 'offset': 0, 'platform': 'all'},
                timeout=10)
            response.raise_for_status()
            data = response.json()
            icons = []
            for idx, icon in enumerate((data.get('icons') or [])[:limit]):
                icon_id = icon.get('id', '')
                platform = icon.get('platform', 'ios')
                icons.append({'source': 'icons8',
                               'url': f'https://img.icons8.com/{platform}/40/000000/{icon_id}.png',
                               'name': f'{keyword}_{idx+1}', 'keyword': keyword, 'id': icon_id})
            logger.info(f"Icons8: 找到 {len(icons)} 个 '{keyword}' 图标")
            return icons
        except Exception as e:
            logger.error(f"Icons8 搜索失败: {e}")
            return []

    def search_iconmonstr(self, keyword, limit=5):
        """搜索 Iconmonstr（完全免费）"""
        try:
            response = self.session.get('https://iconmonstr.com/',
                                        params={'s': keyword}, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            icons = []
            for idx, link in enumerate(soup.find_all('a', href=re.compile(r'/.*-\d+/'), limit=limit)):
                icon_page = link.get('href')
                if icon_page:
                    full_url = f'https://iconmonstr.com{icon_page}'
                    icons.append({'source': 'iconmonstr', 'url': full_url,
                                  'name': f'{keyword}_{idx+1}', 'keyword': keyword,
                                  'page_url': full_url})
            logger.info(f"Iconmonstr: 找到 {len(icons)} 个 '{keyword}' 图标")
            return icons
        except Exception as e:
            logger.error(f"Iconmonstr 搜索失败: {e}")
            return []

    def search_feather_icons(self, keyword):
        """搜索 Feather Icons（开源图标集）"""
        FEATHER = {'list': 'list', 'add': 'plus', 'chart': 'bar-chart-2',
                   'settings': 'settings', 'menu': 'menu', 'home': 'home',
                   'user': 'user', 'search': 'search'}
        icon_name = FEATHER.get(keyword.lower()) or next(
            (v for k, v in FEATHER.items() if keyword.lower() in k or k in keyword.lower()), None)
        if icon_name:
            return [{'source': 'feather', 'keyword': keyword, 'name': keyword, 'icon_name': icon_name,
                     'url': f'https://unpkg.com/feather-icons/dist/icons/{icon_name}.svg'}]
        return []

    def search_heroicons(self, keyword):
        """搜索 Heroicons（Tailwind CSS 团队）"""
        HEROICONS = {'list': 'list-bullet', 'add': 'plus', 'chart': 'chart-bar',
                     'settings': 'cog', 'menu': 'bars-3', 'home': 'home',
                     'user': 'user', 'search': 'magnifying-glass'}
        icon_name = HEROICONS.get(keyword.lower()) or next(
            (v for k, v in HEROICONS.items() if keyword.lower() in k or k in keyword.lower()), None)
        if icon_name:
            base = 'https://raw.githubusercontent.com/tailwindlabs/heroicons/master/src/24/outline'
            return [{'source': 'heroicons', 'keyword': keyword, 'name': keyword,
                     'url': f'{base}/{icon_name}.svg', 'icon_name': icon_name}]
        return []

    def search_all_sources(self, keyword, limit=5):
        """从所有来源搜索图标"""
        all_icons = []
        methods = [
            ('Flaticon',    lambda: self.search_flaticon(keyword, limit)),
            ('Icons8',      lambda: self.search_icons8(keyword, limit)),
            ('Iconmonstr',  lambda: self.search_iconmonstr(keyword, limit)),
            ('Feather',     lambda: self.search_feather_icons(keyword)),
            ('Heroicons',   lambda: self.search_heroicons(keyword)),
        ]
        for name, fn in methods:
            try:
                logger.info(f"正在搜索 {name}...")
                all_icons.extend(fn())
                time.sleep(1)
            except Exception as e:
                logger.error(f"{name} 搜索出错: {e}")
        logger.info(f"总共找到 {len(all_icons)} 个图标")
        return all_icons

    def download_icon(self, icon_info):
        """下载单个图标"""
        try:
            source = icon_info['source']
            url = icon_info['url']
            name = icon_info['name']

            if source == 'iconmonstr' and 'page_url' in icon_info:
                url = self._get_iconmonstr_download_url(icon_info['page_url'])
                if not url:
                    return None

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '')
            if 'svg' in content_type or url.endswith('.svg'):
                ext, content, mode = 'svg', response.text, 'w'
            else:
                ext, content, mode = 'png', response.content, 'wb'

            filepath = os.path.join(self.output_dir, source, f'{name}.{ext}')
            with open(filepath, mode, **({'encoding': 'utf-8'} if mode == 'w' else {})) as f:
                f.write(content)
            logger.info(f"✓ 下载成功: {source}/{name}.{ext}")
            return filepath
        except Exception as e:
            logger.error(f"下载失败 {icon_info.get('name')}: {e}")
            return None

    def _get_iconmonstr_download_url(self, page_url):
        try:
            soup = BeautifulSoup(self.session.get(page_url, timeout=10).text, 'html.parser')
            link = soup.find('a', href=re.compile(r'.*\.png'))
            return link.get('href') if link else None
        except Exception as e:
            logger.error(f"获取下载链接失败: {e}")
            return None

    def download_all_icons(self, icons):
        """批量下载图标"""
        results = []
        for icon in icons:
            fp = self.download_icon(icon)
            results.append({**icon, 'filepath': fp or '', 'downloaded': bool(fp)})
            time.sleep(0.5)
        success = sum(1 for r in results if r['downloaded'])
        logger.info(f"下载完成: {success}/{len(icons)} 成功")
        return results
