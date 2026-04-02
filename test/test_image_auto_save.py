#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for automatic image saving."""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from universal_crawler_v2 import UniversalCrawlerV2


def _output_dir():
    base = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_image_auto_save')
    path = os.path.abspath(os.path.join(base, uuid.uuid4().hex))
    os.makedirs(path, exist_ok=True)
    return path


class _FakeBinaryResponse:
    def __init__(self, status_code=200, content=b'', headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f'HTTP {self.status_code}')


def test_field_intent_prefers_title_over_image_for_icon_title():
    crawler = UniversalCrawlerV2(base_url='https://example.com', output_dir=_output_dir())

    assert crawler._field_intent('图标标题') == 'title'
    assert crawler._field_intent('图标图片') == 'image'
    assert crawler._field_intent('图标链接') == 'link'

    crawler.close()


def test_save_results_auto_downloads_images(monkeypatch):
    output_dir = _output_dir()
    crawler = UniversalCrawlerV2(base_url='https://example.com', output_dir=output_dir)
    data = [
        {
            '图标图片': 'https://cdn-icons-png.flaticon.com/128/1163/1163661.png',
            '图标标题': 'Cloudy',
            '图标链接': 'https://www.flaticon.com/free-icon/cloudy_1163661',
        }
    ]

    def fake_save_single_image(record, image_dir, file_index):
        file_path = os.path.join(image_dir, f"{file_index:03d}_Cloudy.png")
        with open(file_path, 'wb') as f:
            f.write(b'fake-png-bytes')
        return file_path

    monkeypatch.setattr(crawler, '_save_single_image', fake_save_single_image)

    save_result = crawler.save_results(data, filename='weather_icons', preferred_format='json')

    assert save_result is not None
    assert save_result['save_type'] == 'images'
    assert save_result['saved_count'] == 1
    assert os.path.isdir(save_result['path'])
    saved_names = os.listdir(save_result['path'])
    assert len(saved_names) == 1
    assert saved_names[0].endswith('.png')
    assert not any(name.endswith('.json') for name in os.listdir(output_dir))

    crawler.close()
