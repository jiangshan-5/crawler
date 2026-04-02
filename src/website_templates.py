#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站模板配置
预设常见网站的爬取配置
"""

# 网站模板配置
WEBSITE_TEMPLATES = {
    'flaticon': {
        'name': 'Flaticon 图标网站',
        'description': '爬取 Flaticon 的图标信息',
        'list_selector': '.icon--item || li:has(a[href*="/free-icon/"]) || a[href*="/free-icon/"]',
        'fields': {
            '图标图片': 'img.icon--item__img@src || img@src || img@data-src',
            '图标标题': '.icon--item__title || img@alt || @title',
            '图标链接': 'a.icon--item__link@href || a@href || @href',
        },
        'example_url': 'https://www.flaticon.com/free-icons/weather'
    },
    
    'github_trending': {
        'name': 'GitHub 趋势',
        'description': '爬取 GitHub 今日趋势项目',
        'list_selector': 'article.Box-row',
        'fields': {
            '项目名': 'h2 a',
            '项目链接': 'h2 a@href',
            '描述': 'p.col-9',
            '语言': 'span[itemprop="programmingLanguage"]',
            '星标数': 'svg.octicon-star ~ span',
        },
        'example_url': 'https://github.com/trending'
    },
    
    'hackernews': {
        'name': 'Hacker News',
        'description': '爬取 Hacker News 新闻',
        'list_selector': 'tr.athing',
        'fields': {
            '标题': 'span.titleline a',
            '链接': 'span.titleline a@href',
            '来源': 'span.sitestr',
        },
        'example_url': 'https://news.ycombinator.com'
    },
    
    'producthunt': {
        'name': 'Product Hunt',
        'description': '爬取 Product Hunt 产品',
        'list_selector': 'div[data-test="post-item"]',
        'fields': {
            '产品名': 'h3',
            '描述': 'p',
            '链接': 'a@href',
        },
        'example_url': 'https://www.producthunt.com'
    },
}


def get_template(template_id):
    """获取模板配置"""
    return WEBSITE_TEMPLATES.get(template_id)


def get_all_templates():
    """获取所有模板"""
    return WEBSITE_TEMPLATES


def get_template_names():
    """获取所有模板名称"""
    return {tid: t['name'] for tid, t in WEBSITE_TEMPLATES.items()}
