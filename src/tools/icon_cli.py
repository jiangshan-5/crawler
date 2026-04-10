#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多源图标爬虫 - CLI 入口
用法: python -m src.tools.icon_cli --help
"""

import argparse
import logging
import time
from datetime import datetime
import os

from src.tools.multi_source_icon_crawler import MultiSourceIconCrawler
from src.tools.icon_report import generate_comparison_html, save_results_json

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/icon_crawler_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

ALL_SOURCES = ['flaticon', 'icons8', 'iconmonstr', 'feather', 'heroicons']


def build_parser():
    parser = argparse.ArgumentParser(
        description='多源图标爬虫 - 从多个免费图标网站爬取图标',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.tools.icon_cli
  python -m src.tools.icon_cli --sources feather heroicons --keywords home user
  python -m src.tools.icon_cli --limit 5 --output data/my_icons
"""
    )
    parser.add_argument('--sources', '-s', nargs='+',
                        choices=ALL_SOURCES + ['all'], default=['all'],
                        help='指定来源（可多选，all=全部）')
    parser.add_argument('--keywords', '-k', nargs='+',
                        default=['list', 'add', 'chart', 'settings'],
                        help='搜索关键词')
    parser.add_argument('--limit', '-l', type=int, default=3,
                        help='每个关键词下载数量（默认3）')
    parser.add_argument('--output', '-o', default='data/icons_comparison',
                        help='输出目录')
    return parser


def run(args):
    selected = ALL_SOURCES if 'all' in args.sources else args.sources
    crawler = MultiSourceIconCrawler(output_dir=args.output)
    all_results = []

    for keyword in args.keywords:
        logger.info(f"搜索关键词: {keyword}")
        icons = []

        source_map = {
            'flaticon':   lambda: crawler.search_flaticon(keyword, args.limit),
            'icons8':     lambda: crawler.search_icons8(keyword, args.limit),
            'iconmonstr': lambda: crawler.search_iconmonstr(keyword, args.limit),
            'feather':    lambda: crawler.search_feather_icons(keyword),
            'heroicons':  lambda: crawler.search_heroicons(keyword),
        }
        for src in selected:
            try:
                icons.extend(source_map[src]())
                time.sleep(1)
            except Exception as e:
                logger.error(f"{src} 出错: {e}")

        results = crawler.download_all_icons(icons)
        all_results.extend(results)

    save_results_json(all_results, args.output)

    try:
        generate_comparison_html(all_results, args.keywords, args.output)
    except Exception as e:
        logger.error(f"生成报告失败: {e}")

    success = sum(1 for r in all_results if r.get('downloaded'))
    logger.info(f"✓ 完成！成功下载 {success}/{len(all_results)} 个图标")
    logger.info(f"✓ 结果目录: {args.output}")


if __name__ == '__main__':
    run(build_parser().parse_args())
