#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline unit tests for UniversalCrawlerV2 core behavior."""

import os
import sys
import uuid

from bs4 import BeautifulSoup

# Add src path for direct module import in local runs.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import universal_crawler_v2 as crawler_module
from universal_crawler_v2 import UniversalCrawlerV2


def _output_dir():
    base = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_offline')
    path = os.path.abspath(os.path.join(base, uuid.uuid4().hex))
    os.makedirs(path, exist_ok=True)
    return path


class _FakeResponse:
    def __init__(self, status_code=200, text=''):
        self.status_code = status_code
        self.text = text
        self.apparent_encoding = 'utf-8'
        self.encoding = None

    def raise_for_status(self):
        if self.status_code >= 400:
            raise crawler_module.requests.exceptions.HTTPError(
                f'HTTP {self.status_code}'
            )


class _FakeBinaryResponse:
    def __init__(self, status_code=200, content=b'', headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise crawler_module.requests.exceptions.HTTPError(
                f'HTTP {self.status_code}'
            )


def test_extract_data_supports_text_and_attribute():
    crawler = UniversalCrawlerV2(base_url='https://example.com', output_dir=_output_dir())
    soup = BeautifulSoup(
        '<html><body><h1>  Title  </h1><a href="/item/1">Go</a></body></html>',
        'html.parser'
    )
    selectors = {
        'title': 'h1',
        'link': 'a@href'
    }

    data = crawler.extract_data(soup, selectors)

    assert data['title'] == 'Title'
    assert data['link'] == '/item/1'
    crawler.close()


def test_extract_list_data_filters_all_empty_items():
    crawler = UniversalCrawlerV2(base_url='https://example.com', output_dir=_output_dir())
    soup = BeautifulSoup(
        """
        <div class="item"><span class="name"> Item A </span><a href="/a">A</a></div>
        <div class="item"><span class="name">   </span></div>
        <div class="item"><span class="name">Item C</span><a href="/c">C</a></div>
        """,
        'html.parser'
    )

    results = crawler.extract_list_data(
        soup,
        '.item',
        {'name': '.name', 'url': 'a@href'}
    )

    assert len(results) == 2
    assert results[0]['name'] == 'Item A'
    assert results[1]['url'] == '/c'
    crawler.close()


def test_fetch_with_retry_recovers_after_transient_error(monkeypatch):
    crawler = UniversalCrawlerV2(base_url='https://example.com', output_dir=_output_dir(), max_retries=2)
    sequence = [
        _FakeResponse(status_code=500, text='server error'),
        _FakeResponse(status_code=200, text='<html><title>ok</title></html>')
    ]

    def fake_get(url, timeout=10):
        return sequence.pop(0)

    monkeypatch.setattr(crawler.session, 'get', fake_get)
    monkeypatch.setattr(crawler.rate_limiter, 'wait', lambda: None)
    monkeypatch.setattr(crawler_module.time, 'sleep', lambda _: None)

    soup = crawler.fetch_page('https://example.com')

    assert soup is not None
    assert soup.title.get_text() == 'ok'
    assert crawler.stats['retried_pages'] >= 1
    assert crawler.stats['success_pages'] == 1
    crawler.close()


def test_extract_field_fallback_with_double_pipe(tmp_path=None):
    crawler = UniversalCrawlerV2(base_url='https://example.com', output_dir=_output_dir())
    soup = BeautifulSoup(
        '<html><body><a class="link" href="/ok"><img src="/img.png"/></a></body></html>',
        'html.parser'
    )
    item = soup.select_one('a.link')

    image = crawler._extract_field(item, 'img.non-exist@src || img@src')
    link = crawler._extract_field(item, 'a.non-exist@href || @href')

    assert image == '/img.png'
    assert link == '/ok'
    crawler.close()


def test_list_selector_fallback_with_double_pipe():
    crawler = UniversalCrawlerV2(base_url='https://example.com', output_dir=_output_dir())
    soup = BeautifulSoup(
        """
        <div class="container">
            <a href="/free-icon/a"><img src="/a.png"/></a>
            <a href="/free-icon/b"><img src="/b.png"/></a>
        </div>
        """,
        'html.parser'
    )

    results = crawler.extract_list_data(
        soup,
        '.icon--item || a[href*="/free-icon/"]',
        {'图标链接': '@href', '图标图片': 'img@src'}
    )

    assert len(results) == 2
    assert results[0]['图标链接'] == '/free-icon/a'
    assert results[1]['图标图片'] == '/b.png'
    crawler.close()
