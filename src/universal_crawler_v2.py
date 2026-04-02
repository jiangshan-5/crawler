#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict
from urllib.parse import urlparse
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

try:
    from .advanced_crawler import AdvancedCrawler, is_advanced_mode_available
except ImportError:
    from advanced_crawler import AdvancedCrawler, is_advanced_mode_available

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RetryConfig:
    MAX_RETRIES = 3
    RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
    BACKOFF_FACTOR = 2
    INITIAL_BACKOFF = 1


class RateLimiter:
    def __init__(self, requests_per_second=1):
        self.min_delay = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def wait(self):
        now = time.time()
        delta = now - self.last_request_time
        if delta < self.min_delay:
            time.sleep(self.min_delay - delta)
        self.last_request_time = time.time()


class DataValidator:
    @staticmethod
    def validate_url(url):
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    @staticmethod
    def clean_text(text):
        if not text:
            return ""
        return " ".join(text.split()).strip()


class UniversalCrawlerV2:
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.svg', '.ico')

    def __init__(
        self,
        base_url,
        output_dir='data/crawled_data',
        use_advanced_mode=False,
        requests_per_second=1,
        max_retries=3,
        enable_cache=False,
        advanced_user_data_dir=None,
    ):
        self.base_url = base_url
        self.output_dir = output_dir
        self.use_advanced_mode = use_advanced_mode
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self.advanced_user_data_dir = advanced_user_data_dir
        self.advanced_crawler = None

        self.rate_limiter = RateLimiter(requests_per_second)
        self.validator = DataValidator()
        self._init_session()
        self._primed_domains = set()

        os.makedirs(self.output_dir, exist_ok=True)

        self.stats = {
            'total_pages': 0,
            'success_pages': 0,
            'failed_pages': 0,
            'retried_pages': 0,
            'total_items': 0,
            'cache_hits': 0,
        }
        self.last_error_reason = ''

        if self.use_advanced_mode:
            if not is_advanced_mode_available():
                logger.warning('advanced mode not available, fallback to standard mode')
                self.use_advanced_mode = False
            else:
                logger.info('advanced mode enabled')
                self.advanced_crawler = AdvancedCrawler(
                    headless=not self._prefer_headed_advanced(self.base_url),
                    user_data_dir=self.advanced_user_data_dir,
                )

    def _init_session(self):
        self.session = requests.Session()
        self.session.trust_env = False
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=0)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update(
            {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
        )

    def _calculate_backoff(self, attempt):
        return RetryConfig.INITIAL_BACKOFF * (RetryConfig.BACKOFF_FACTOR ** attempt)

    def _is_access_denied_page(self, html):
        if not html:
            return False
        text = html.lower()
        markers = [
            'access denied',
            'support@freepik.com',
            'error reference',
            'subject=access%20denied',
        ]
        return all(m in text for m in ['access denied', 'support@freepik.com']) or any(
            m in text for m in markers[2:]
        )

    def _prefer_headed_advanced(self, url):
        return bool(url and 'flaticon.com' in url)

    def _is_flaticon_url(self, url):
        return bool(url and 'flaticon.com' in url)

    def _prepare_request_headers(self, url):
        headers = {}
        if self._is_flaticon_url(url):
            headers.update(
                {
                    'Referer': 'https://www.flaticon.com/',
                    'Origin': 'https://www.flaticon.com',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Dest': 'document',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                }
            )
        return headers

    def _prime_flaticon_session(self, timeout):
        if 'flaticon.com' in self._primed_domains:
            logger.info('[standard] flaticon session already primed; skip warmup')
            return
        try:
            self.session.get('https://www.flaticon.com/', timeout=timeout, headers=self._prepare_request_headers('https://www.flaticon.com/'))
            logger.info('[standard] flaticon session primed with homepage visit')
            self._primed_domains.add('flaticon.com')
        except Exception as e:
            logger.info(f'[standard] flaticon session prime skipped: {e}')

    def _recommended_advanced_wait(self, url):
        if self._is_flaticon_url(url):
            if '/free-icons/' in url:
                return 1.2
            return 1.8
        return 3

    def _field_intent(self, field_name):
        name = (field_name or '').lower()
        if any(token in name for token in ['link', 'url', 'href', '链接', '鏈接']):
            return 'link'
        if any(token in name for token in ['title', 'name', '标题', '標題', '名称', '名稱']):
            return 'title'
        if any(
            token in name
            for token in ['img', 'image', 'thumbnail', 'avatar', '图片', '圖片', '图像', '圖像', '封面']
        ):
            return 'image'
        return 'title'

    def _iter_rows(self, data):
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        return []

    def _looks_like_image_url(self, value):
        if not isinstance(value, str) or not self.validator.validate_url(value):
            return False
        path = (urlparse(value).path or '').lower()
        return any(path.endswith(ext) for ext in self.IMAGE_EXTENSIONS)

    def _is_image_candidate(self, field_name, value):
        if not isinstance(value, str) or not self.validator.validate_url(value):
            return False
        return self._field_intent(field_name) == 'image' or self._looks_like_image_url(value)

    def _pick_record_label(self, row, index):
        for field_name, value in row.items():
            if self._field_intent(field_name) == 'title' and isinstance(value, str) and value.strip():
                return value.strip()
        for value in row.values():
            if isinstance(value, str) and value.strip() and not self.validator.validate_url(value):
                return value.strip()
        return f'image_{index:03d}'

    def _sanitize_filename(self, name):
        cleaned = re.sub(r'[^A-Za-z0-9._-]+', '_', (name or '').strip())
        cleaned = cleaned.strip('._')
        return cleaned[:80] or 'image'

    def _guess_image_extension(self, url, content_type=''):
        path = (urlparse(url).path or '').lower()
        for ext in self.IMAGE_EXTENSIONS:
            if path.endswith(ext):
                return ext

        content_type = (content_type or '').split(';', 1)[0].strip().lower()
        mapping = {
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'image/webp': '.webp',
            'image/gif': '.gif',
            'image/svg+xml': '.svg',
            'image/bmp': '.bmp',
            'image/x-icon': '.ico',
            'image/vnd.microsoft.icon': '.ico',
        }
        return mapping.get(content_type, '.png')

    def _collect_image_records(self, data):
        records = []
        for row_index, row in enumerate(self._iter_rows(data), start=1):
            label = self._pick_record_label(row, row_index)
            image_index = 0
            for field_name, value in row.items():
                if self._is_image_candidate(field_name, value):
                    image_index += 1
                    records.append(
                        {
                            'row_index': row_index,
                            'image_index': image_index,
                            'field_name': field_name,
                            'url': value.strip(),
                            'label': label,
                        }
                    )
        return records

    def should_auto_save_as_images(self, data):
        return bool(self._collect_image_records(data))

    def save_images(self, data, filename=None):
        image_records = self._collect_image_records(data)
        if not image_records:
            logger.warning('no image records detected')
            return None

        if not filename:
            filename = f"crawled_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        image_dir = os.path.join(self.output_dir, filename)
        os.makedirs(image_dir, exist_ok=True)

        saved_files = []
        max_workers = min(6, max(1, len(image_records)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(self._save_single_image, record, image_dir, file_index): record
                for file_index, record in enumerate(image_records, start=1)
            }
            for future in as_completed(future_map):
                try:
                    file_path = future.result()
                    if file_path:
                        saved_files.append(file_path)
                except Exception as e:
                    record = future_map[future]
                    logger.warning(f"image download failed [{record['url']}]: {e}")

        if not saved_files:
            logger.warning('image save completed with 0 files')
            return None

        saved_files.sort()
        logger.info(f"saved images: {len(saved_files)} -> {image_dir}")
        return {
            'save_type': 'images',
            'path': image_dir,
            'saved_count': len(saved_files),
            'files': saved_files,
        }

    def _save_single_image(self, record, image_dir, file_index):
        headers = dict(self.session.headers)
        if 'flaticon.com' in record['url'] or 'cdn-icons-png.flaticon.com' in record['url']:
            headers['Referer'] = 'https://www.flaticon.com/'

        with requests.Session() as session:
            session.trust_env = False
            session.headers.update(headers)
            response = session.get(record['url'], timeout=20)
            response.raise_for_status()
            content_type = getattr(response, 'headers', {}).get('Content-Type', '')
            if content_type and not content_type.lower().startswith('image/'):
                logger.warning(f"skip non-image response: {record['url']} ({content_type})")
                return None

            extension = self._guess_image_extension(record['url'], content_type)
            base_name = self._sanitize_filename(record['label'])
            if record['image_index'] > 1:
                base_name = f"{base_name}_{record['image_index']}"
            file_path = os.path.join(image_dir, f"{file_index:03d}_{base_name}{extension}")

            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_path

    def save_results(self, data, filename=None, preferred_format='json'):
        if self.should_auto_save_as_images(data):
            image_result = self.save_images(data, filename)
            if image_result:
                return image_result
            logger.warning('image auto-save failed, fallback to structured output')

        if preferred_format == 'csv' and isinstance(data, list):
            path = self.save_to_csv(data, filename)
            if path:
                return {'save_type': 'csv', 'path': path, 'saved_count': len(data)}
            return None

        path = self.save_to_json(data, filename)
        if not path:
            return None
        saved_count = len(data) if isinstance(data, list) else 1
        return {'save_type': 'json', 'path': path, 'saved_count': saved_count}

    def _extract_flaticon_rows_fallback(self, soup, item_selectors, base_url):
        rows = []
        seen = set()
        anchors = soup.select('a[href*="/free-icon/"]')
        for anchor in anchors:
            href = (anchor.get('href') or '').strip()
            if not href:
                continue
            full_link = urljoin('https://www.flaticon.com', href)
            if full_link in seen:
                continue
            seen.add(full_link)

            image = ''
            title = ''
            img = anchor.select_one('img')
            if img:
                image = (img.get('src') or img.get('data-src') or '').strip()
                title = (img.get('alt') or '').strip()
            if not title:
                title = (anchor.get('title') or anchor.get_text(strip=True) or '').strip()

            row = {}
            for field_name in item_selectors.keys():
                intent = self._field_intent(field_name)
                if intent == 'link':
                    row[field_name] = full_link
                elif intent == 'image':
                    row[field_name] = image
                else:
                    row[field_name] = title

            if row and any(row.values()):
                rows.append(row)
        if rows:
            logger.info(f'[flaticon] heuristic fallback extracted {len(rows)} rows')
        return rows

    def fetch_page(self, url, timeout=10):
        self.rate_limiter.wait()
        if self.use_advanced_mode and self.advanced_crawler:
            return self._fetch_with_advanced_mode(url, timeout)
        return self._fetch_with_retry(url, timeout)

    def _fetch_with_advanced_mode(self, url, timeout):
        try:
            logger.info(f'[advanced] fallback start -> {url}')
            wait_time = self._recommended_advanced_wait(url)
            logger.info(f'[advanced] wait_time={wait_time}s')
            soup = self.advanced_crawler.fetch_page(url, wait_time=wait_time, timeout=timeout)
            if soup:
                html = str(soup)
                if 'flaticon.com' in url and self._is_access_denied_page(html):
                    logger.error('[advanced] flaticon access denied page detected (IP/region/risk control)')
                    self.last_error_reason = 'flaticon_access_denied'
                    self.stats['failed_pages'] += 1
                    return None
                self.stats['success_pages'] += 1
                self.last_error_reason = ''
                logger.info('[advanced] fallback success')
                return soup

            logger.warning('[advanced] fallback returned empty content, retrying with standard mode')
            return self._fetch_with_retry(url, timeout)
        except Exception as e:
            logger.error(f'[advanced] fallback error: {e}')
            logger.warning('[advanced] retrying with standard mode after exception')
            return self._fetch_with_retry(url, timeout)

    def _fetch_with_retry(self, url, timeout):
        if self._is_flaticon_url(url):
            self._prime_flaticon_session(timeout)
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f'[standard] GET {url} (attempt {attempt + 1}/{self.max_retries + 1})')
                request_kwargs = {'timeout': timeout}
                extra_headers = self._prepare_request_headers(url)
                if extra_headers:
                    request_kwargs['headers'] = extra_headers
                response = self.session.get(url, **request_kwargs)
                logger.info(
                    f"[standard] status={response.status_code}, final_url={getattr(response, 'url', url)}, bytes={len(response.text)}"
                )

                if response.status_code == 429:
                    wait_time = self._calculate_backoff(attempt)
                    logger.warning(f'[standard] hit 429, backoff {wait_time:.1f}s')
                    time.sleep(wait_time)
                    self.stats['retried_pages'] += 1
                    continue

                if response.status_code in RetryConfig.RETRY_HTTP_CODES:
                    logger.warning(f'[standard] retriable status {response.status_code}')
                    if attempt < self.max_retries:
                        wait_time = self._calculate_backoff(attempt)
                        time.sleep(wait_time)
                        self.stats['retried_pages'] += 1
                        continue

                if response.status_code == 403 and 'flaticon.com' in url:
                    logger.warning('[standard] flaticon 403 detected, trying advanced fallback')
                    if self._is_access_denied_page(response.text):
                        logger.error('[standard] flaticon returned access denied page')
                        self.last_error_reason = 'flaticon_access_denied'
                    if self.advanced_crawler is None and is_advanced_mode_available():
                        try:
                            logger.info('[advanced] initialize fallback instance')
                            self.advanced_crawler = AdvancedCrawler(
                                headless=not self._prefer_headed_advanced(url),
                                user_data_dir=self.advanced_user_data_dir,
                            )
                            logger.info('[advanced] fallback instance ready')
                        except Exception as e:
                            logger.warning(f'[advanced] fallback init failed: {e}')

                    if self.advanced_crawler is not None:
                        logger.info('[advanced] run fallback fetch')
                        soup = self._fetch_with_advanced_mode(url, timeout)
                        if soup:
                            return soup
                        logger.warning('[advanced] fallback fetch returned empty')

                if response.status_code in [404, 403]:
                    logger.error(f'[standard] blocked or not found: {response.status_code} -> {url}')
                    self.stats['failed_pages'] += 1
                    return None

                response.raise_for_status()
                response.encoding = response.apparent_encoding
                soup = BeautifulSoup(response.text, 'html.parser')
                self.last_error_reason = ''
                self.stats['success_pages'] += 1
                return soup

            except requests.exceptions.Timeout:
                logger.warning(f'[standard] timeout (attempt {attempt + 1}/{self.max_retries + 1})')
                if attempt < self.max_retries:
                    wait_time = self._calculate_backoff(attempt)
                    time.sleep(wait_time)
                    self.stats['retried_pages'] += 1

            except requests.exceptions.ConnectionError as e:
                logger.warning(f'[standard] connection error: {e} (attempt {attempt + 1}/{self.max_retries + 1})')
                if attempt < self.max_retries:
                    wait_time = self._calculate_backoff(attempt)
                    time.sleep(wait_time)
                    self.stats['retried_pages'] += 1

            except requests.exceptions.HTTPError as e:
                logger.error(f'[standard] HTTP error: {e}')
                break

            except Exception as e:
                logger.error(f'[standard] unexpected error: {e}')
                break

        logger.error(f'[standard] exhausted retries ({self.max_retries}) for: {url}')
        self.stats['failed_pages'] += 1
        return None

    def extract_data(self, soup, selectors, validate=True):
        data = {}
        for field_name, selector in selectors.items():
            try:
                value = self._extract_field(soup, selector)
                if isinstance(value, str):
                    value = self.validator.clean_text(value)
                data[field_name] = value
            except Exception as e:
                logger.warning(f'field extract failed [{field_name}]: {e}')
                data[field_name] = ''
        return data

    def _extract_field(self, element, selector):
        candidates = [s.strip() for s in selector.split('||') if s.strip()]
        if not candidates:
            return ''

        for candidate in candidates:
            if '@' in candidate:
                css_selector, attribute = candidate.split('@', 1)
                css_selector = css_selector.strip()
                attribute = attribute.strip()
                if not attribute:
                    continue
                if css_selector:
                    target = element.select_one(css_selector)
                    if target:
                        value = target.get(attribute, '')
                        if value:
                            return value
                else:
                    value = element.get(attribute, '')
                    if value:
                        return value
            else:
                target = element.select_one(candidate)
                if target:
                    value = target.get_text(strip=True)
                    if value:
                        return value

        return ''

    def _select_items_with_fallback(self, soup, list_selector):
        candidates = [s.strip() for s in list_selector.split('||') if s.strip()]
        if not candidates:
            return []

        for candidate in candidates:
            try:
                items = soup.select(candidate)
                if items:
                    logger.info(f'use list selector: {candidate} (hit {len(items)})')
                    return items
            except Exception as e:
                logger.warning(f'invalid list selector {candidate}: {e}')
        return []

    def extract_list_data(self, soup, list_selector, item_selectors, validate=True, source_url=''):
        results = []
        try:
            items = self._select_items_with_fallback(soup, list_selector)
            logger.info(f'list items found: {len(items)}')

            if not items and self._is_flaticon_url(source_url):
                logger.warning('[flaticon] template selector hit 0, trying generic anchor selector')
                items = soup.select('a[href*="/free-icon/"]')
                logger.info(f'[flaticon] generic selector found: {len(items)}')

            for idx, item in enumerate(items):
                row = {}
                for field_name, selector in item_selectors.items():
                    try:
                        value = self._extract_field(item, selector)
                        if isinstance(value, str):
                            value = self.validator.clean_text(value)
                        row[field_name] = value
                    except Exception as e:
                        logger.warning(f'field extract failed [{field_name}] on item {idx + 1}: {e}')
                        row[field_name] = ''

                if row and any(row.values()):
                    results.append(row)
                    self.stats['total_items'] += 1

            if not results and self._is_flaticon_url(source_url):
                logger.warning('[flaticon] selector extraction empty, trying heuristic extraction')
                results = self._extract_flaticon_rows_fallback(soup, item_selectors, source_url)
                if results:
                    self.stats['total_items'] += len(results)

        except Exception as e:
            logger.error(f'list extraction failed: {e}')

        return results

    def crawl_single_page(self, url, selectors):
        self.stats['total_pages'] += 1
        soup = self.fetch_page(url)
        if not soup:
            return None
        return self.extract_data(soup, selectors)

    def crawl_list_page(self, url, list_selector, item_selectors, max_items=None):
        self.stats['total_pages'] += 1
        soup = self.fetch_page(url)
        if not soup:
            return []

        results = self.extract_list_data(soup, list_selector, item_selectors, source_url=url)
        if max_items and len(results) > max_items:
            results = results[:max_items]
        return results

    def crawl_multiple_pages(self, urls, list_selector, item_selectors, max_items=None, delay=1):
        all_results = []
        for url in urls:
            if max_items and len(all_results) >= max_items:
                break
            all_results.extend(self.crawl_list_page(url, list_selector, item_selectors))
            if delay > 0 and url != urls[-1]:
                time.sleep(delay)

        if max_items and len(all_results) > max_items:
            all_results = all_results[:max_items]
        return all_results

    def save_to_json(self, data, filename=None):
        if not filename:
            filename = f"crawled_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filepath = os.path.join(self.output_dir, f'{filename}.json')
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f'saved json: {filepath}')
            return filepath
        except Exception as e:
            logger.error(f'save json failed: {e}')
            return None

    def save_to_csv(self, data, filename=None):
        if not data:
            logger.warning('no data to save')
            return None
        if not filename:
            filename = f"crawled_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = os.path.join(self.output_dir, f'{filename}.csv')
        try:
            fieldnames = list(data[0].keys())
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            logger.info(f'saved csv: {filepath}')
            return filepath
        except Exception as e:
            logger.error(f'save csv failed: {e}')
            return None

    def get_stats(self):
        stats = self.stats.copy()
        stats['last_error_reason'] = self.last_error_reason
        if stats['total_pages'] > 0:
            stats['success_rate'] = f"{stats['success_pages'] / stats['total_pages'] * 100:.1f}%"
        else:
            stats['success_rate'] = '0%'
        return stats

    def reset_stats(self):
        self.stats = {
            'total_pages': 0,
            'success_pages': 0,
            'failed_pages': 0,
            'retried_pages': 0,
            'total_items': 0,
            'cache_hits': 0,
        }

    def close(self):
        if self.advanced_crawler:
            self.advanced_crawler.close()
            self.advanced_crawler = None
        if getattr(self, 'session', None):
            self.session.close()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


def main():
    print('UniversalCrawlerV2 ready.')


if __name__ == '__main__':
    main()
