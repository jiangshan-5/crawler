#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站模板配置
预设常见网站的爬取配置
"""

# 网站模板配置
WEBSITE_TEMPLATES = {
    'novel_biquuge_full_book': {
        'name': '笔趣阁 (小说整本抓取)',
        'description': '输入书名或书籍 URL，自动搜索、解析目录并顺序下载全本书籍',
        'mode': 'single',
        'workflow': 'biquuge_full_book',
        'input_label': '🔍 输入书名或书籍 URL',
        'input_hint': '直接输入书名（如：剑来）或书籍链接',
        'list_selector': '#list a[href] || .listmain a[href] || .box_con a[href]',
        'fields': {
            '章节标题': '.bookname h1 || h1 || title',
            '正文内容': '#content || #chaptercontent || #BookText || .read-content || .yd_text2 || .content || .showtxt || .txtnav',
            '图书信息': '#info || .info || .small',
            '封面图片': '#fmimg img@src || .cover img@src || img@src'
        },
        'example_url': '剑来'
    },

    'flaticon': {
        'name': 'Flaticon (专业图标库)',
        'description': '全球最大的矢量图标库，支持关键词搜索与智能反爬',
        'workflow': 'keyword_search',
        'search_url_template': 'https://www.flaticon.com/free-icons/{query}',
        'input_label': '🔍 输入图标关键词（建议英文）',
        'input_hint': '例如：weather, coffee, dashboard...',
        'list_selector': '.icon--item || li:has(a[href*="/free-icon/"])',
        'fields': {
            '图标预览': 'img.icon--item__img@src || img@src || img@data-src',
            '图标标题': '.icon--item__title || img@alt || @title',
            '图标链接': 'a.icon--item__link@href || a@href',
        },
        'example_url': 'coffee'
    },

    'guomantuku': {
        'name': '国漫图库 (AI 精美原图)',
        'description': '抓取国漫图库的 AI 生成美图，建议开启高级模式以支持无限加载',
        'workflow': 'keyword_search',
        'search_url_template': 'https://guomantuku.com/?s={query}',
        'input_label': '🔍 输入角色或系列名称',
        'input_hint': '例如：云韵, 美杜莎, 遮天...',
        'list_selector': 'div.lazy-parent',
        'fields': {
            '预览图': 'img@src || img@data-src',
            '角色名称': 'h3',
            '系列详情': 'p',
        },
        'example_url': 'https://guomantuku.com/'
    },

    'music_solara': {
        'name': 'Solara 音乐聚合 (全网音源)',
        'description': '支持网易云/酷我/酷狗/QQ/百度/JOOX/咪咕等多平台音源。直接输入歌名或歌手搜索并下载MP3。',
        'workflow': 'music_api',
        'api_base': 'https://yy.bttts.com/proxy',
        'source': 'netease',
        'available_sources': ['netease', 'tencent', 'kugou', 'kuwo', 'baidu', 'joox', 'migu'],
        'input_label': '🎵 搜索歌曲、歌手',
        'input_hint': '例如：周杰伦、夜曲、晴天...',
        'list_selector': '',
        'fields': {},
        'example_url': '周杰伦'
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
