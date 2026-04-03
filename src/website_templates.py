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

    'novel_generic': {
        'name': '通用小说网站',
        'description': '以 biquuge 为默认示例，适合大多数小说列表页，应用后通常只需要小幅微调选择器',
        'mode': 'list',
        'list_selector': 'li:has(h3 a) || li:has(h4 a) || .bookbox || .book-item || .novel-item || .book-list li || .book-img-text li || .rank-book-list li || .txt-list li',
        'fields': {
            '书名': '.book-title || h4 a || h3 a || .bookname a || .name a || a[title]',
            '作者': '.author || .book-author || .writer || .author a || .author-name || .s4',
            '分类': '.cat || .category || .book-cat || .tag || .s1',
            '简介': '.intro || .book-desc || .description || .book-intro || .detail',
            '最新章节': '.update a || .latest-chapter a || .chapter a || .lastchapter a || .s3 a',
            '封面': 'img@src || img@data-src || .book-cover img@src',
            '详情链接': 'h4 a@href || h3 a@href || .bookname a@href || .name a@href || a[title]@href || @href',
        },
        'example_url': 'https://www.biquuge.com/top/'
    },

    'novel_biquuge_list': {
        'name': '笔趣阁小说列表（biquuge）',
        'description': '适合 biquuge 的排行榜、分类页和首页小说列表',
        'mode': 'list',
        'list_selector': '.l li || .topbooks li || .rank li || li:has(.s2 a) || li:has(h3 a) || li:has(h4 a)',
        'fields': {
            '分类': '.s1 || .cat || .category',
            '书名': '.s2 a || h3 a || h4 a || .bookname a || a[title]',
            '详情链接': '.s2 a@href || h3 a@href || h4 a@href || .bookname a@href || a[title]@href',
            '最新章节': '.s3 a || .update a || .latest-chapter a',
            '作者': '.s4 || .author || .book-author',
            '更新时间': '.s5 || .update-time || .date',
        },
        'example_url': 'https://www.biquuge.com/top/'
    },

    'novel_biquuge_directory': {
        'name': '笔趣阁章节目录（biquuge）',
        'description': '适合 biquuge 的书籍目录页，提取章节标题和章节链接',
        'mode': 'list',
        'list_selector': '#list dd || .listmain dd || .box_con #list dd || dd:has(a[href$=".html"])',
        'fields': {
            '章节标题': 'a',
            '章节链接': 'a@href',
        },
        'example_url': 'https://www.biquuge.com/112/112271/index_14.html'
    },

    'novel_biquuge_chapter': {
        'name': '笔趣阁章节正文（biquuge）',
        'description': '适合 biquuge 的章节正文页，提取章节标题、正文与上下章导航',
        'mode': 'single',
        'list_selector': '',
        'fields': {
            '章节标题': '.bookname h1 || h1',
            '正文内容': '#content || .content || .showtxt || .txtnav',
            '面包屑': '.con_top || .path || .nav',
            '上一章链接': '.bottem2 a:nth-of-type(1)@href || .bottem1 a:nth-of-type(1)@href',
            '目录链接': '.bottem2 a:nth-of-type(2)@href || .bottem1 a:nth-of-type(2)@href',
            '下一章链接': '.bottem2 a:nth-of-type(3)@href || .bottem1 a:nth-of-type(3)@href',
        },
        'example_url': 'https://www.biquuge.com/112/112271/1339.html'
    },

    'novel_biquuge_full_book': {
        'name': '笔趣阁整本抓取（biquuge）',
        'description': '输入书名或书籍 URL，自动搜索、解析目录并抓取整本书，保存为 txt 和 json',
        'mode': 'single',
        'workflow': 'biquuge_full_book',
        'input_label': '书名或书籍 URL',
        'input_hint': '直接输入书名即可，例如：剑来。也支持直接粘贴 biquuge 的书籍 URL。',
        'list_selector': '',
        'fields': {},
        'example_url': '剑来'
    },

    'novel_biquuge_book': {
        'name': '笔趣阁书籍详情（biquuge）',
        'description': '适合 biquuge 的单本书详情页，提取书名、简介、封面等信息',
        'mode': 'single',
        'list_selector': '',
        'fields': {
            '书名': '#info h1 || h1',
            '基本信息': '#info || .info || .small',
            '简介': '#intro || .intro || .desc',
            '封面': '#fmimg img@src || .cover img@src || img@src',
            '目录页链接': 'a[href*="index_"]@href || .read a@href',
        },
        'example_url': 'https://www.biquuge.com/112/112271/'
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
