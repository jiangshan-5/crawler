#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for the integrated biquuge full-book workflow."""

import json
import os
import sys
import uuid

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from universal_crawler_v2 import UniversalCrawlerV2


def _output_dir():
    base = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_novel_workflow')
    path = os.path.abspath(os.path.join(base, uuid.uuid4().hex))
    os.makedirs(path, exist_ok=True)
    return path


def _soup(html):
    return BeautifulSoup(html, 'html.parser')


def test_crawl_biquuge_full_book_offline(monkeypatch):
    crawler = UniversalCrawlerV2(base_url='https://www.biquuge.com/', output_dir=_output_dir())

    monkeypatch.setattr(
        crawler,
        'search_biquuge_book',
        lambda keyword, timeout=12: {
            'query': keyword,
            'book_url': 'https://www.biquuge.com/112/112271/',
            'matched_url': 'https://www.biquuge.com/112/112271/',
            'title': 'book-alpha',
            'score': 100,
        },
    )

    entry_pages = {
        'https://www.biquuge.com/112/112271/': _soup(
            '''
            <div id="info">
              <h1>book-alpha</h1>
              <p>author: demo</p>
            </div>
            <div id="intro">A compact intro.</div>
            <a href="index_1.html">catalog</a>
            '''
        ),
        'https://www.biquuge.com/112/112271/index_1.html': _soup(
            '''
            <div class="chapterlist">
              <a href="/112/112271/1.html">chapter 1 rise</a>
              <a href="/112/112271/2.html">chapter 2 return</a>
            </div>
            '''
        ),
    }

    chapter_pages = {
        'https://www.biquuge.com/112/112271/1.html': _soup(
            '''
            <div class="bookname"><h1>chapter 1 rise</h1></div>
            <div id="content">
              line one.<br/>
              天才一秒记住本站地址，不保留。<br/>
              line two.
            </div>
            <div class="page"><a href="/112/112271/1_2.html">next page</a></div>
            '''
        ),
        'https://www.biquuge.com/112/112271/1_2.html': _soup(
            '''
            <div id="content">
              line three.
            </div>
            <div class="page"><a href="/112/112271/1_3.html">next page</a></div>
            '''
        ),
        'https://www.biquuge.com/112/112271/1_3.html': _soup(
            '''
            <div id="content">
              line four.
            </div>
            '''
        ),
        'https://www.biquuge.com/112/112271/2.html': _soup(
            '''
            <div class="bookname"><h1>chapter 2 return</h1></div>
            <div id="content">
              alpha.<br/>
              手机用户请浏览阅读，不保留。<br/>
              omega.
            </div>
            '''
        ),
    }

    def fake_fetch(url, timeout=10):
        crawler.stats['total_pages'] += 1
        soup = entry_pages.get(url)
        if soup:
            crawler.stats['success_pages'] += 1
        else:
            crawler.stats['failed_pages'] += 1
        return soup

    monkeypatch.setattr(crawler, '_fetch_tracked_page', fake_fetch)
    monkeypatch.setattr(crawler, '_fetch_tracked_page_standard', fake_fetch)
    monkeypatch.setattr(crawler, '_fetch_browser_tracked_page', lambda url, timeout=10, wait_time=0.8: None)
    monkeypatch.setattr(crawler, '_fetch_soup_with_session', lambda session, url, timeout=10, max_retries=2: chapter_pages.get(url))

    book = crawler.crawl_biquuge_full_book('book-alpha')

    assert book is not None
    assert book['_save_type'] == 'novel_book'
    assert book['book_title'] == 'book-alpha'
    assert book['chapter_count'] == 2
    assert book['chapters'][0]['chapter_title'] == 'chapter 1 rise'
    assert '天才一秒记住' not in book['chapters'][0]['content']
    assert '手机用户请浏览阅读' not in book['chapters'][1]['content']
    assert 'line three.' in book['chapters'][0]['content']
    assert 'line four.' in book['chapters'][0]['content']
    crawler.close()


def test_extract_biquuge_chapter_catalog_from_generic_list():
    crawler = UniversalCrawlerV2(base_url='https://www.biquuge.com/', output_dir=_output_dir())

    soup = _soup(
        '''
        <div class="chapterlist">
          <a href="/112/112271/9.html">chapter 9</a>
          <a href="/112/112271/10.html">chapter 10</a>
          <a href="/112/112271/index_2.html">next catalog page</a>
        </div>
        '''
    )

    catalog = crawler._extract_biquuge_chapter_catalog(soup, 'https://www.biquuge.com/112/112271/')

    assert [item['chapter_url'] for item in catalog] == [
        'https://www.biquuge.com/112/112271/9.html',
        'https://www.biquuge.com/112/112271/10.html',
    ]
    crawler.close()


def test_directory_page_urls_and_catalog_stay_within_same_book():
    crawler = UniversalCrawlerV2(base_url='https://www.biquuge.com/', output_dir=_output_dir())
    root_url = 'https://www.biquuge.com/9/9693/'
    soup = _soup(
        '''
        <div class="chapterlist">
          <a href="/9/9693/index_2.html">catalog page 2</a>
          <a href="/9/9693/1.html">chapter 1</a>
          <a href="/56/56082/">other book detail</a>
          <a href="/56/56082/index_1.html">other book catalog</a>
          <a href="/56/56082/27671.html">other book chapter</a>
        </div>
        '''
    )

    directory_pages = crawler._extract_biquuge_directory_page_urls(soup, root_url, expected_root_url=root_url)
    catalog = crawler._extract_biquuge_chapter_catalog(soup, root_url, expected_root_url=root_url)

    assert directory_pages == [
        'https://www.biquuge.com/9/9693/',
        'https://www.biquuge.com/9/9693/index_2.html',
    ]
    assert [item['chapter_url'] for item in catalog] == ['https://www.biquuge.com/9/9693/1.html']
    crawler.close()


def test_extract_biquuge_chapter_text_uses_heuristic_container():
    crawler = UniversalCrawlerV2(base_url='https://www.biquuge.com/', output_dir=_output_dir())

    soup = _soup(
        '''
        <article class="reader-body">
          <div class="toolbar"><a href="/112/112271/8.html">prev</a></div>
          <div class="reader-main">
            <p>line alpha.</p>
            <p>line beta.</p>
          </div>
        </article>
        '''
    )

    text = crawler._extract_biquuge_chapter_text(soup)

    assert 'line alpha.' in text
    assert 'line beta.' in text
    crawler.close()


def test_crawl_biquuge_full_book_blocks_mixed_roots(monkeypatch):
    crawler = UniversalCrawlerV2(base_url='https://www.biquuge.com/', output_dir=_output_dir())

    monkeypatch.setattr(
        crawler,
        'search_biquuge_book',
        lambda keyword, timeout=12: {
            'query': keyword,
            'book_url': 'https://www.biquuge.com/9/9693/',
            'matched_url': 'https://www.biquuge.com/9/9693/',
            'title': 'book-alpha',
            'score': 100,
        },
    )
    monkeypatch.setattr(crawler, '_fetch_tracked_page', lambda url, timeout=10: _soup('<div id="info"><h1>book-alpha</h1></div>'))
    monkeypatch.setattr(crawler, '_fetch_tracked_page_standard', lambda url, timeout=10: _soup('<div id="info"><h1>book-alpha</h1></div>'))
    monkeypatch.setattr(
        crawler,
        '_resolve_biquuge_directory_catalog',
        lambda book_url, timeout=12: {
            'directory_url': 'https://www.biquuge.com/9/9693/',
            'chapter_catalog': [
                {'chapter_title': 'chapter 1', 'chapter_url': 'https://www.biquuge.com/9/9693/1.html'},
                {'chapter_title': 'wrong chapter', 'chapter_url': 'https://www.biquuge.com/56/56082/27671.html'},
            ],
        },
    )
    monkeypatch.setattr(
        crawler,
        '_crawl_biquuge_chapters_parallel',
        lambda chapter_catalog, timeout=8: (
            [
                {'index': 1, 'chapter_title': 'chapter 1', 'chapter_url': 'https://www.biquuge.com/9/9693/1.html', 'content': 'alpha'},
                {'index': 2, 'chapter_title': 'wrong chapter', 'chapter_url': 'https://www.biquuge.com/56/56082/27671.html', 'content': 'beta'},
            ],
            [],
        ),
    )

    book = crawler.crawl_biquuge_full_book('book-alpha')

    assert book is None
    assert crawler.last_error_reason == 'novel_book_mixed_roots'
    crawler.close()


def test_save_novel_book_writes_text_and_json():
    crawler = UniversalCrawlerV2(base_url='https://www.biquuge.com/', output_dir=_output_dir())

    book = {
        '_save_type': 'novel_book',
        'book_title': 'book-alpha',
        'book_url': 'https://www.biquuge.com/112/112271/',
        'directory_url': 'https://www.biquuge.com/112/112271/index_1.html',
        'chapter_count': 2,
        'chapters': [
            {
                'index': 1,
                'chapter_title': 'chapter 1 rise',
                'chapter_url': 'https://www.biquuge.com/112/112271/1.html',
                'content': 'line one.\nline two.',
            },
            {
                'index': 2,
                'chapter_title': 'chapter 2 return',
                'chapter_url': 'https://www.biquuge.com/112/112271/2.html',
                'content': 'alpha.\nomega.',
            },
        ],
    }

    save_result = crawler.save_novel_book(book, filename='book_alpha_test')

    assert save_result is not None
    assert save_result['save_type'] == 'novel_book'
    txt_path = save_result['path']
    json_path = save_result['files'][1]
    assert os.path.exists(txt_path)
    assert os.path.exists(json_path)

    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()
    assert 'book-alpha' in text
    assert 'chapter 1 rise' in text

    with open(json_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    assert payload['chapter_count'] == 2
    crawler.close()


def test_save_novel_book_blocks_mixed_roots():
    crawler = UniversalCrawlerV2(base_url='https://www.biquuge.com/', output_dir=_output_dir())

    book = {
        '_save_type': 'novel_book',
        'book_title': 'book-alpha',
        'book_url': 'https://www.biquuge.com/9/9693/',
        'directory_url': 'https://www.biquuge.com/9/9693/index_1.html',
        'chapter_count': 2,
        'chapters': [
            {
                'index': 1,
                'chapter_title': 'chapter 1',
                'chapter_url': 'https://www.biquuge.com/9/9693/1.html',
                'content': 'alpha',
            },
            {
                'index': 2,
                'chapter_title': 'wrong chapter',
                'chapter_url': 'https://www.biquuge.com/56/56082/27671.html',
                'content': 'beta',
            },
        ],
    }

    save_result = crawler.save_novel_book(book, filename='mixed_root_book')

    assert save_result is None
    assert crawler.last_error_reason == 'novel_book_mixed_roots'
    crawler.close()


def test_search_biquuge_book_only_bootstraps_browser_once(monkeypatch):
    crawler = UniversalCrawlerV2(base_url='https://www.biquuge.com/', output_dir=_output_dir(), use_advanced_mode=True)
    standard_calls = []
    browser_calls = []

    monkeypatch.setattr(
        crawler,
        '_build_biquuge_search_urls',
        lambda keyword: [
            'https://www.biquuge.com/search.php?keyword=alpha',
            'https://www.biquuge.com/search.php?q=alpha',
            'https://www.biquuge.com/search.php?searchkey=alpha',
        ],
    )

    def fake_standard(url, timeout=12):
        standard_calls.append(url)
        return None

    def fake_browser(url, timeout=12, wait_time=0.6):
        browser_calls.append(url)
        return _soup('<a href="/9/9693/">book-alpha</a>')

    monkeypatch.setattr(crawler, '_fetch_tracked_page_standard', fake_standard)
    monkeypatch.setattr(crawler, '_fetch_browser_tracked_page', fake_browser)

    match = crawler.search_biquuge_book('book-alpha')

    assert match is not None
    assert match['book_url'] == 'https://www.biquuge.com/9/9693/'
    assert len(standard_calls) == 3
    assert browser_calls == ['https://www.biquuge.com/search.php?keyword=alpha']
    crawler.close()


def test_resolve_biquuge_directory_catalog_prefers_standard_fetcher(monkeypatch):
    crawler = UniversalCrawlerV2(base_url='https://www.biquuge.com/', output_dir=_output_dir(), use_advanced_mode=True)
    standard_calls = []

    def fail_browser(*args, **kwargs):
        raise AssertionError('browser fallback should not be used when standard directory fetch succeeds')

    def fake_standard(url, timeout=12):
        standard_calls.append(url)
        if url.endswith('index.html'):
            return _soup(
                '''
                <div class="chapterlist">
                  <a href="/9/9693/1.html">chapter 1</a>
                  <a href="/9/9693/2.html">chapter 2</a>
                </div>
                '''
            )
        return _soup('<div class="chapterlist"></div>')

    monkeypatch.setattr(crawler, '_fetch_tracked_page_standard', fake_standard)
    monkeypatch.setattr(crawler, '_fetch_browser_tracked_page', fail_browser)

    result = crawler._resolve_biquuge_directory_catalog('https://www.biquuge.com/9/9693/')

    assert result['chapter_catalog']
    assert standard_calls
    crawler.close()
