#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for crawler efficiency helpers."""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from universal_crawler_v2 import UniversalCrawlerV2


def _output_dir():
    base = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_efficiency_helpers')
    path = os.path.abspath(os.path.join(base, uuid.uuid4().hex))
    os.makedirs(path, exist_ok=True)
    return path


def test_flaticon_session_prime_only_runs_once(monkeypatch):
    crawler = UniversalCrawlerV2(base_url='https://www.flaticon.com/free-icons/weather', output_dir=_output_dir())
    calls = []

    def fake_get(url, timeout=10, headers=None):
        calls.append((url, timeout, headers))

        class _Resp:
            status_code = 200
            text = ''

        return _Resp()

    monkeypatch.setattr(crawler.session, 'get', fake_get)

    crawler._prime_flaticon_session(10)
    crawler._prime_flaticon_session(10)

    assert len(calls) == 1
    crawler.close()


def test_recommended_advanced_wait_prefers_shorter_flaticon_list_pages():
    crawler = UniversalCrawlerV2(base_url='https://example.com', output_dir=_output_dir())

    assert crawler._recommended_advanced_wait('https://www.flaticon.com/free-icons/weather') == 1.2
    assert crawler._recommended_advanced_wait('https://www.flaticon.com/') == 1.8
    assert crawler._recommended_advanced_wait('https://example.com/article') == 3

    crawler.close()
