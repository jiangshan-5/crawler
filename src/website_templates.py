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
        'description': '输入关键词搜索并提取 Flaticon 图标信息',
        'workflow': 'keyword_search',
        'search_url_template': 'https://www.flaticon.com/free-icons/{query}',
        'input_label': '🔍 输入图标关键词（建议英文）',
        'input_hint': '例如：weather, home, social media...',
        'list_selector': '.icon--item || li:has(a[href*="/free-icon/"]) || a[href*="/free-icon/"]',
        'fields': {
            '图标预览': 'img.icon--item__img@src || img@src || img@data-src',
            '图标标题': '.icon--item__title || img@alt || @title',
            '图标链接': 'a.icon--item__link@href || a@href || @href',
        },
        'example_url': 'weather'
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

    'novel_biquuge_full_book': {
        'name': '笔趣阁整本抓取（biquuge）',
        'description': '输入书名或书籍 URL，自动搜索、解析目录并抓取整本书，保存为 txt 和 json',
        'mode': 'single',
        'workflow': 'biquuge_full_book',
        'input_label': '🔍 输入书名或书籍 URL',
        'input_hint': '直接输入书名（如：剑来）或粘贴书籍首页地址',
        'list_selector': '#list a[href] || .listmain a[href] || .box_con a[href]',
        'fields': {
            '章节标题': '.bookname h1 || h1 || title',
            '正文内容': '#content || #chaptercontent || #BookText || .read-content || .yd_text2 || .content || .showtxt || .txtnav',
            '图书信息': '#info || .info || .small',
            '封面图片': '#fmimg img@src || .cover img@src || img@src'
        },
        'example_url': '剑来'
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
