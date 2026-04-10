#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标结果 HTML 报告生成器
将多源爬虫结果生成可视化对比页面
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

_STYLE = """
body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto;
       padding: 20px; background: #f5f5f5; }
h1 { text-align: center; color: #333; }
.section { background: white; margin: 20px 0; padding: 20px;
           border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.title { font-size: 24px; color: #333; margin-bottom: 15px;
         border-bottom: 2px solid #3cc51f; padding-bottom: 10px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 20px; margin-top: 20px; }
.card { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 8px;
        padding: 15px; text-align: center; transition: transform .2s; }
.card:hover { transform: translateY(-5px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
.img-wrap { width: 80px; height: 80px; margin: 10px auto;
            display: flex; align-items: center; justify-content: center; }
.img-wrap img { max-width: 100%; max-height: 100%; }
.source { font-weight: bold; color: #3cc51f; margin-top: 10px; }
.name { color: #666; font-size: 12px; margin-top: 5px; }
.stats { background: #e8f5e9; padding: 15px; border-radius: 8px;
         margin-bottom: 20px; text-align: center; }
"""


def generate_comparison_html(results, keywords, output_dir):
    """生成图标对比 HTML 页面"""
    grouped = {}
    for r in results:
        kw = r.get('keyword', 'unknown')
        grouped.setdefault(kw, []).append(r)

    sections = ""
    for kw, icons in grouped.items():
        cards = ""
        for icon in icons:
            if icon.get('downloaded'):
                rel = icon['filepath'].replace('\\', '/').split('icons_comparison/')[-1]
                cards += (f'<div class="card">'
                          f'<div class="img-wrap"><img src="{rel}" alt="{icon["name"]}"></div>'
                          f'<div class="source">{icon["source"]}</div>'
                          f'<div class="name">{icon["name"]}</div></div>')
        sections += (f'<div class="section"><div class="title">🔍 {kw}</div>'
                     f'<div class="grid">{cards}</div></div>')

    html = (f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
            f'<title>图标对比</title><style>{_STYLE}</style></head><body>'
            f'<h1>🎨 图标对比结果</h1>'
            f'<div class="stats"><p>共搜索 <strong>{len(keywords)}</strong> 个关键词，'
            f'找到 <strong>{len(results)}</strong> 个图标</p></div>'
            f'{sections}</body></html>')

    html_path = os.path.join(output_dir, 'comparison.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    logger.info(f"✓ 对比页面已生成: {html_path}")
    return html_path


def save_results_json(results, output_dir, filename='icon_comparison_results.json'):
    """保存爬取结果为 JSON"""
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"结果已保存到: {filepath}")
