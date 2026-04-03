#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for crawler efficiency helpers."""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import advanced_crawler
import tkinter as tk
import universal_crawler_gui_modern
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


def test_cached_uc_driver_path_uses_existing_binary(monkeypatch):
    advanced_crawler._get_cached_uc_driver_path.cache_clear()
    expected = os.path.expandvars(r"%APPDATA%\undetected_chromedriver\undetected_chromedriver.exe")

    monkeypatch.setattr(
        advanced_crawler.os.path,
        'exists',
        lambda path: path == expected,
    )

    assert advanced_crawler._get_cached_uc_driver_path() == expected


def test_advanced_mode_available_when_edge_driver_is_present(monkeypatch):
    monkeypatch.setattr(advanced_crawler, 'ADVANCED_MODE_AVAILABLE', True)
    monkeypatch.setattr(advanced_crawler, 'UC_AVAILABLE', False)
    monkeypatch.setattr(advanced_crawler, 'EDGE_BROWSER_AVAILABLE', True)
    monkeypatch.setattr(advanced_crawler, 'EDGE_DRIVER_AVAILABLE', True)

    assert advanced_crawler.is_advanced_mode_available() is True


def test_advanced_crawler_reuses_warm_browser(monkeypatch):
    monkeypatch.setattr(advanced_crawler, 'ADVANCED_MODE_AVAILABLE', True)
    advanced_crawler.AdvancedCrawler.shutdown_all()

    class DummyDriver:
        def __init__(self):
            self.alive = True
            self.quit_calls = 0

        @property
        def window_handles(self):
            if not self.alive:
                raise RuntimeError('driver closed')
            return ['tab-1']

        def quit(self):
            self.quit_calls += 1
            self.alive = False

    first = advanced_crawler.AdvancedCrawler(headless=True, user_data_dir=_output_dir())
    dummy = DummyDriver()
    first.driver = dummy
    first._store_shared_driver()
    first.close()

    assert dummy.quit_calls == 0
    assert first.driver is None

    second = advanced_crawler.AdvancedCrawler(headless=True, user_data_dir=first.user_data_dir)
    assert second._try_attach_shared_driver() is True
    assert second.driver is dummy

    second.close(force=True)
    assert dummy.quit_calls == 1
    advanced_crawler.AdvancedCrawler.shutdown_all()


def test_gui_startup_prewarm_marks_ready(monkeypatch):
    class DummyAdvancedCrawler:
        def __init__(self, headless=True, user_data_dir=None, reuse_browser=True):
            self.headless = headless
            self.user_data_dir = user_data_dir
            self.reuse_browser = reuse_browser
            self.started = False

        def start(self):
            self.started = True

        def close(self):
            return None

    monkeypatch.setattr(universal_crawler_gui_modern, 'AdvancedCrawler', DummyAdvancedCrawler)
    monkeypatch.setattr(universal_crawler_gui_modern, 'is_advanced_mode_available', lambda: True)

    root = tk.Tk()
    root.withdraw()
    app = universal_crawler_gui_modern.ModernUniversalCrawlerGUI(root)
    key = (False, app.advanced_user_data_dir)

    app._prewarm_advanced_browser(key)

    assert key in app._advanced_prewarm_ready
    assert app.advanced_state_var.get() == '已预热'
    root.destroy()


def test_gui_does_not_prewarm_until_advanced_enabled(monkeypatch):
    started = []

    class DummyAdvancedCrawler:
        def __init__(self, headless=True, user_data_dir=None, reuse_browser=True):
            self.headless = headless
            self.user_data_dir = user_data_dir
            self.reuse_browser = reuse_browser

        def start(self):
            started.append((self.headless, self.user_data_dir))

        def close(self):
            return None

    monkeypatch.setattr(universal_crawler_gui_modern, 'AdvancedCrawler', DummyAdvancedCrawler)
    monkeypatch.setattr(universal_crawler_gui_modern, 'is_advanced_mode_available', lambda: True)

    root = tk.Tk()
    root.withdraw()
    app = universal_crawler_gui_modern.ModernUniversalCrawlerGUI(root)

    app._schedule_advanced_prewarm('https://www.biquuge.com/top/')

    assert started == []
    assert app._advanced_prewarm_inflight == set()
    root.destroy()


def test_fetch_page_disables_broken_advanced_runtime(monkeypatch):
    crawler = UniversalCrawlerV2(
        base_url='https://www.biquuge.com/',
        output_dir=_output_dir(),
        use_advanced_mode=True,
    )
    advanced_calls = []

    class DummyAdvancedCrawler:
        def fetch_page(self, url, wait_time=3, timeout=30):
            advanced_calls.append((url, wait_time, timeout))
            raise RuntimeError('session not created')

        def close(self, force=False):
            return None

    class DummyResponse:
        status_code = 200
        text = '<html><body>ok</body></html>'
        apparent_encoding = 'utf-8'
        url = 'https://www.biquuge.com/book'

        def raise_for_status(self):
            return None

    crawler.advanced_crawler = DummyAdvancedCrawler()
    monkeypatch.setattr(crawler.session, 'get', lambda url, timeout=10, headers=None: DummyResponse())

    first = crawler.fetch_page('https://www.biquuge.com/book', timeout=8)
    second = crawler.fetch_page('https://www.biquuge.com/book', timeout=8)

    assert first is not None
    assert second is not None
    assert len(advanced_calls) == 1
    assert crawler._advanced_runtime_disabled_reason
    crawler.close()
