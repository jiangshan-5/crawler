#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict
from urllib.parse import urlparse
from urllib.parse import quote_plus
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

try:
    try:
        from .advanced_crawler import AdvancedCrawler, is_advanced_mode_available
    except ImportError:
        from advanced_crawler import AdvancedCrawler, is_advanced_mode_available
except (ImportError, Exception) as e:
    logger.warning(f"Advanced crawler components could not be loaded: {e}")
    AdvancedCrawler = None
    def is_advanced_mode_available(): return False

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
        is_flaticon_task=False
    ):
        self._closed = False
        self._stop_requested = False
        self.base_url = base_url
        self.output_dir = output_dir
        self.use_advanced_mode = use_advanced_mode
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self.advanced_user_data_dir = advanced_user_data_dir
        self.is_flaticon_task = is_flaticon_task
        self.advanced_crawler = None
        self._advanced_runtime_disabled_reason = ''
        self._browser_bootstrap_disabled_reason = ''
        self._stats_lock = threading.Lock()
        self._thread_local = threading.local()
        self.novel_max_workers = 32
        self.novel_chapter_retry_count = 2
        self.novel_sample_chapter_count = 5
        self.novel_max_subpages_per_chapter = 20

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
                is_headed = self._prefer_headed_advanced(self.base_url) or self.is_flaticon_task
                self.advanced_crawler = AdvancedCrawler(
                    headless=not is_headed,
                    user_data_dir=self.advanced_user_data_dir,
                )

    def _init_session(self):
        self.session = requests.Session()
        self.session.trust_env = False
        adapter = requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=64, max_retries=0)
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
        # Always use headed mode for Flaticon to bypass headless detection
        if self._is_flaticon_url(url):
            return True
        # Also check if it's a keyword search intended for flaticon
        if getattr(self, "base_url", "") == "https://www.flaticon.com/":
            return True
        return False

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
                    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="120", "Chromium";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
        elif self._is_biquuge_url(url):
            headers.update(
                {
                    'Referer': self._normalize_biquuge_book_url(url) or 'https://www.biquuge.com/',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
        return headers

    def _increment_stats(self, **delta):
        if not delta:
            return
        with self._stats_lock:
            for key, value in delta.items():
                self.stats[key] = self.stats.get(key, 0) + value

    def _get_thread_session(self):
        session = getattr(self._thread_local, 'session', None)
        if session is None:
            session = requests.Session()
            session.trust_env = False
            adapter = requests.adapters.HTTPAdapter(pool_connections=8, pool_maxsize=8, max_retries=0)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            session.headers.update(dict(self.session.headers))
            self._thread_local.session = session
        try:
            session.cookies.update(self.session.cookies)
        except Exception:
            pass
        return session

    def _disable_advanced_runtime(self, reason):
        reason_text = str(reason or 'advanced runtime unavailable').strip()
        if not self._advanced_runtime_disabled_reason:
            logger.warning(f'[advanced] disable advanced mode for current crawl: {reason_text}')
        self._advanced_runtime_disabled_reason = reason_text
        try:
            if self.advanced_crawler:
                self.advanced_crawler.close(force=True)
        except Exception:
            pass
        self.advanced_crawler = None

    def _disable_browser_bootstrap(self, reason):
        reason_text = str(reason or 'browser bootstrap unavailable').strip()
        if not self._browser_bootstrap_disabled_reason:
            logger.warning(f'[novel] disable browser bootstrap for current crawl: {reason_text}')
        self._browser_bootstrap_disabled_reason = reason_text
        if not self.use_advanced_mode:
            try:
                if self.advanced_crawler:
                    self.advanced_crawler.close(force=True)
            except Exception:
                pass
            self.advanced_crawler = None

    def _ensure_advanced_crawler(self, url=''):
        if self._browser_bootstrap_disabled_reason:
            return None
        if self.advanced_crawler:
            return self.advanced_crawler
        if not is_advanced_mode_available():
            return None
        try:
            logger.info('[novel] initialize browser bootstrap engine')
            self.advanced_crawler = AdvancedCrawler(
                headless=not self._prefer_headed_advanced(url or self.base_url),
                user_data_dir=self.advanced_user_data_dir,
            )
            return self.advanced_crawler
        except Exception as e:
            logger.warning(f'[novel] browser bootstrap unavailable: {e}')
            return None

    def _sync_session_from_advanced(self, url):
        crawler = self._ensure_advanced_crawler(url)
        if crawler is None:
            return False

        try:
            soup = crawler.fetch_page(url, wait_time=0.6, timeout=12)
            if not soup:
                return False

            driver = crawler.driver
            if driver is None:
                return False

            try:
                ua = driver.execute_script("return navigator.userAgent;")
                if ua:
                    self.session.headers['User-Agent'] = ua
            except Exception:
                pass

            for cookie in driver.get_cookies() or []:
                name = cookie.get('name')
                value = cookie.get('value')
                domain = cookie.get('domain')
                path = cookie.get('path') or '/'
                if not name:
                    continue
                try:
                    self.session.cookies.set(name, value, domain=domain, path=path)
                except Exception:
                    try:
                        self.session.cookies.set(name, value)
                    except Exception:
                        pass

            logger.info('[novel] synced cookies/user-agent from browser bootstrap')
            return True
        except Exception as e:
            self._disable_browser_bootstrap(e)
            logger.warning(f'[novel] browser bootstrap sync failed: {e}')
            return False

    def _fetch_browser_tracked_page(self, url, timeout=10, wait_time=0.8):
        if self._browser_bootstrap_disabled_reason:
            return None
        crawler = self._ensure_advanced_crawler(url)
        if crawler is None:
            return None

        self._increment_stats(total_pages=1)
        try:
            soup = crawler.fetch_page(url, wait_time=wait_time, timeout=max(timeout, 12))
            if soup:
                self._increment_stats(success_pages=1)
                logger.info(f'[novel] browser bootstrap fetched: {url}')
                return soup
        except Exception as e:
            self._disable_browser_bootstrap(e)
            logger.warning(f'[novel] browser bootstrap failed {url}: {e}')

        self._increment_stats(failed_pages=1)
        return None

    def _fetch_soup_with_session(self, session, url, timeout=10, max_retries=2):
        for attempt in range(max_retries + 1):
            try:
                request_kwargs = {'timeout': timeout}
                extra_headers = self._prepare_request_headers(url)
                if extra_headers:
                    request_kwargs['headers'] = extra_headers
                response = session.get(url, **request_kwargs)
                if response.status_code in RetryConfig.RETRY_HTTP_CODES and attempt < max_retries:
                    time.sleep(min(1.2, 0.25 * (attempt + 1)))
                    continue
                if response.status_code in (403, 404):
                    return None
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return BeautifulSoup(response.text, 'html.parser')
            except requests.exceptions.RequestException:
                if attempt < max_retries:
                    time.sleep(min(1.2, 0.25 * (attempt + 1)))
                    continue
                return None

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
                # Check if stop has been requested
                if self.is_stop_requested():
                    logger.info('[crawler] stop requested, halting image downloads')
                    # Cancel remaining futures
                    for f in future_map:
                        if not f.done():
                            f.cancel()
                    break
                
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
        if isinstance(data, dict) and data.get('_save_type') == 'novel_book':
            novel_result = self.save_novel_book(data, filename)
            if novel_result:
                return novel_result
            logger.warning('novel auto-save failed, fallback to structured output')

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
        if self.use_advanced_mode and self.advanced_crawler and not self._advanced_runtime_disabled_reason:
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
            self._disable_advanced_runtime(e)
            self._disable_browser_bootstrap(e)
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
            # Check if stop has been requested
            if self.is_stop_requested():
                logger.info('[crawler] stop requested, halting crawl_multiple_pages')
                break
            
            if max_items and len(all_results) >= max_items:
                break
            all_results.extend(self.crawl_list_page(url, list_selector, item_selectors))
            if delay > 0 and url != urls[-1]:
                time.sleep(delay)

        if max_items and len(all_results) > max_items:
            all_results = all_results[:max_items]
        return all_results

    def _is_biquuge_url(self, url):
        return bool(url and 'biquuge.com' in url)

    def _normalize_biquuge_book_url(self, url):
        if not isinstance(url, str) or not url.strip():
            return ''

        full_url = urljoin('https://www.biquuge.com/', url.strip())
        if not self.validator.validate_url(full_url):
            return ''

        parsed = urlparse(full_url)
        match = re.match(r'^/(\d+)/(\d+)/(?:index(?:_\d+)?\.html)?$', parsed.path or '')
        if not match:
            match = re.match(r'^/(\d+)/(\d+)/\d+\.html$', parsed.path or '')
        if not match:
            return full_url

        return f'{parsed.scheme}://{parsed.netloc}/{match.group(1)}/{match.group(2)}/'

    def _looks_like_biquuge_chapter_url(self, url):
        if not self._is_biquuge_url(url):
            return False
        path = (urlparse(url).path or '').lower()
        return bool(re.match(r'^/\d+/\d+/\d+(?:_\d+)?\.html$', path))

    def _normalize_biquuge_chapter_url(self, url):
        if not isinstance(url, str) or not url.strip():
            return ''

        full_url = urljoin('https://www.biquuge.com/', url.strip())
        parsed = urlparse(full_url)
        match = re.match(r'^(?P<prefix>/\d+/\d+/)(?P<chapter>\d+)(?:_(?P<page>\d+))?\.html$', parsed.path or '')
        if not match:
            return full_url

        return f'{parsed.scheme}://{parsed.netloc}{match.group("prefix")}{match.group("chapter")}.html'

    def _looks_like_biquuge_directory_url(self, url):
        if not self._is_biquuge_url(url):
            return False
        path = (urlparse(url).path or '').lower()
        return bool(re.match(r'^/\d+/\d+/(?:index(?:_\d+)?\.html)?$', path))

    def _biquuge_chapter_sort_key(self, url):
        path = (urlparse(url).path or '').lower()
        match = re.match(r'^/\d+/\d+/(\d+)(?:_(\d+))?\.html$', path)
        if match:
            return int(match.group(1)), int(match.group(2) or 0)
        return 999999999, 999999999

    def _fetch_tracked_page(self, url, timeout=10):
        self.stats['total_pages'] += 1
        return self.fetch_page(url, timeout=timeout)

    def _fetch_tracked_page_standard(self, url, timeout=10):
        self._increment_stats(total_pages=1)
        self.rate_limiter.wait()
        return self._fetch_with_retry(url, timeout)

    def _build_biquuge_search_urls(self, keyword):
        templates = [
            'https://www.biquuge.com/search.php?keyword={q}',
            'https://www.biquuge.com/search.php?q={q}',
            'https://www.biquuge.com/search.php?searchkey={q}',
            'https://www.biquuge.com/modules/article/search.php?searchkey={q}',
            'https://www.biquuge.com/case.php?m=search&key={q}',
        ]

        urls = []
        seen = set()
        for encoding in ('utf-8', 'gbk'):
            try:
                encoded = quote_plus(keyword, encoding=encoding, errors='ignore')
            except TypeError:
                encoded = quote_plus(keyword)
            for template in templates:
                url = template.format(q=encoded)
                if url not in seen:
                    seen.add(url)
                    urls.append(url)
        return urls

    def _score_biquuge_candidate(self, text, keyword, url):
        haystack = (text or '').lower()
        query = (keyword or '').strip().lower()
        if not query or not haystack:
            return 0

        score = 0
        if haystack == query:
            score += 120
        elif query in haystack:
            score += 80

        for token in [part.strip().lower() for part in re.split(r'[\s/|,，]+', keyword) if part.strip()]:
            if token in haystack:
                score += 15

        if self._looks_like_biquuge_directory_url(url):
            score += 10
        if self._looks_like_biquuge_chapter_url(url):
            score -= 20
        return score

    def _extract_biquuge_search_matches(self, soup, keyword):
        matches = {}
        for anchor in soup.select('a[href]'):
            href = (anchor.get('href') or '').strip()
            if not href:
                continue

            full_url = urljoin('https://www.biquuge.com/', href)
            if not self._is_biquuge_url(full_url):
                continue

            normalized_url = self._normalize_biquuge_book_url(full_url)
            title = (anchor.get('title') or anchor.get_text(' ', strip=True) or '').strip()
            container = anchor.find_parent(['tr', 'li', 'div', 'dl', 'dd', 'dt'])
            context_text = container.get_text(' ', strip=True) if container else ''
            score = self._score_biquuge_candidate(f'{title} {context_text}', keyword, full_url)
            if score <= 0:
                continue

            current = matches.get(normalized_url)
            if current and current['score'] >= score:
                continue

            matches[normalized_url] = {
                'book_url': normalized_url,
                'matched_url': full_url,
                'title': title or self.validator.clean_text(context_text)[:80],
                'score': score,
            }

        return sorted(matches.values(), key=lambda item: (-item['score'], item['title']))

    def search_biquuge_book(self, keyword, timeout=12):
        query = (keyword or '').strip()
        if not query:
            return None

        if self.validator.validate_url(query):
            book_url = self._normalize_biquuge_book_url(query)
            return {
                'query': query,
                'book_url': book_url or query,
                'matched_url': query,
                'title': '',
                'score': 999,
            }

        search_urls = self._build_biquuge_search_urls(query)
        for search_url in search_urls:
            soup = self._fetch_tracked_page_standard(search_url, timeout=timeout)
            matches = self._extract_biquuge_search_matches(soup, query) if soup else []
            if matches:
                match = matches[0]
                match['query'] = query
                logger.info(f"[novel] search match: {query} -> {match['book_url']}")
                return match

        browser_search_url = search_urls[0] if search_urls else ''
        if browser_search_url:
            logger.info('[novel] standard search empty, try single browser bootstrap search')
            browser_soup = self._fetch_browser_tracked_page(
                browser_search_url,
                timeout=max(timeout, 12),
                wait_time=0.6,
            )
            browser_matches = self._extract_biquuge_search_matches(browser_soup, query) if browser_soup else []
            if browser_matches:
                match = browser_matches[0]
                match['query'] = query
                logger.info(f"[novel] browser search match: {query} -> {match['book_url']}")
                return match

        logger.warning(f'[novel] no biquuge search match for: {query}')
        return None

    def _extract_biquuge_book_meta(self, soup, source_url):
        book_info = self._extract_field(soup, '#info || .info || .small')
        book_title = self._extract_field(soup, '#info h1 || h1')
        intro = self._extract_field(soup, '#intro || .intro || .desc')
        cover = self._extract_field(soup, '#fmimg img@src || .cover img@src || img@src')
        directory_link = self._extract_field(
            soup,
            'a[href*="index_"]@href || .read a@href || a[href$="index.html"]@href',
        )

        return {
            'book_title': self.validator.clean_text(book_title),
            'book_info': self.validator.clean_text(book_info),
            'intro': self.validator.clean_text(intro),
            'cover': cover,
            'book_url': self._normalize_biquuge_book_url(source_url),
            'directory_url': urljoin(source_url, directory_link) if directory_link else '',
        }

    def _directory_page_sort_key(self, url):
        path = (urlparse(url).path or '').lower()
        match = re.search(r'index(?:_(\d+))?\.html$', path)
        if match:
            return int(match.group(1) or 0)
        if path.endswith('/'):
            return 0
        return 999999

    def _extract_biquuge_directory_page_urls(self, soup, source_url, expected_root_url=''):
        urls = set()
        if self._looks_like_biquuge_directory_url(source_url):
            if not expected_root_url or source_url.startswith(expected_root_url):
                urls.add(source_url)
        for anchor in soup.select('a[href]'):
            href = (anchor.get('href') or '').strip()
            if not href:
                continue
            full_url = urljoin(source_url, href)
            if self._looks_like_biquuge_directory_url(full_url):
                normalized_root = self._normalize_biquuge_book_url(full_url)
                if expected_root_url and normalized_root != expected_root_url:
                    continue
                urls.add(full_url)
        return sorted(urls, key=self._directory_page_sort_key)

    def _is_valid_biquuge_catalog_title(self, title):
        text = self.validator.clean_text(title)
        if not text:
            return False
        lowered = text.lower()
        skip_markers = [
            '上一章',
            '下一章',
            '返回目录',
            '加入书签',
            '投推荐票',
            '直达底部',
            '章节报错',
            '我要评论',
            '手机阅读',
            '返回书页',
            '目录',
            '书首页',
        ]
        if lowered in skip_markers:
            return False
        if any(marker in lowered for marker in ['copyright', 'biquuge.com']):
            return False
        return len(text) <= 120

    def _extract_biquuge_catalog_candidate_anchors(self, soup):
        selectors = [
            '#list a[href]',
            '.listmain a[href]',
            '.box_con a[href]',
            'div[id*="list"] a[href]',
            'div[class*="list"] a[href]',
            'dl a[href]',
            'ul a[href]',
            'table a[href]',
        ]
        seen = set()
        anchors = []
        for selector in selectors:
            for anchor in soup.select(selector):
                anchor_id = id(anchor)
                if anchor_id in seen:
                    continue
                seen.add(anchor_id)
                anchors.append(anchor)

        if anchors:
            return anchors
        return soup.select('a[href]')

    def _extract_biquuge_chapter_catalog(self, soup, source_url, expected_root_url=''):
        chapters = {}
        root_url = expected_root_url or self._normalize_biquuge_book_url(source_url)
        for anchor in self._extract_biquuge_catalog_candidate_anchors(soup):
            href = (anchor.get('href') or '').strip()
            title = self.validator.clean_text(anchor.get_text(' ', strip=True) or anchor.get('title', ''))
            if not href or not self._is_valid_biquuge_catalog_title(title):
                continue

            chapter_url = urljoin(source_url, href)
            if not self._looks_like_biquuge_chapter_url(chapter_url):
                continue

            canonical_url = self._normalize_biquuge_chapter_url(chapter_url)
            if root_url and not canonical_url.startswith(root_url):
                continue
            if canonical_url in chapters:
                continue

            chapters[canonical_url] = {
                'chapter_title': title,
                'chapter_url': canonical_url,
            }

        ordered_urls = sorted(chapters.keys(), key=self._biquuge_chapter_sort_key)
        return [chapters[url] for url in ordered_urls]

    def _collect_biquuge_directory_catalog(self, book_url, timeout=12, fetcher=None, source_label='standard'):
        fetcher = fetcher or self._fetch_tracked_page
        root_url = self._normalize_biquuge_book_url(book_url) or book_url
        queue = []
        seen_pages = set()
        candidates = [
            root_url,
            urljoin(root_url, 'index.html'),
            urljoin(root_url, 'index_1.html'),
        ]
        for item in candidates:
            if item and item not in queue:
                queue.append(item)

        chapters = []
        seen_chapters = set()
        directory_url = ''
        processed = 0
        idle_rounds = 0

        while queue and processed < 20:
            queue.sort(key=self._directory_page_sort_key)
            page_url = queue.pop(0)
            if page_url in seen_pages:
                continue
            seen_pages.add(page_url)
            processed += 1

            pending_before = len(queue)
            chapter_count_before = len(chapters)
            soup = fetcher(page_url, timeout=timeout)
            if not soup:
                idle_rounds += 1
                continue

            page_chapters = self._extract_biquuge_chapter_catalog(soup, page_url, expected_root_url=root_url)
            if not directory_url and page_chapters:
                directory_url = page_url

            for next_page in self._extract_biquuge_directory_page_urls(soup, page_url, expected_root_url=root_url):
                if next_page not in seen_pages and next_page not in queue:
                    queue.append(next_page)

            for chapter in page_chapters:
                chapter_url = chapter['chapter_url']
                if chapter_url in seen_chapters:
                    continue
                seen_chapters.add(chapter_url)
                chapters.append(chapter)

            if len(chapters) == chapter_count_before and len(queue) == pending_before:
                idle_rounds += 1
            else:
                idle_rounds = 0

            if not chapters and idle_rounds >= 4:
                logger.info(f'[novel] stop empty directory scan early ({source_label})')
                break

        return {
            'directory_url': directory_url or root_url,
            'chapter_catalog': sorted(chapters, key=lambda item: self._biquuge_chapter_sort_key(item['chapter_url'])),
            'directory_pages': sorted(seen_pages, key=self._directory_page_sort_key),
        }

    def _resolve_biquuge_directory_catalog(self, book_url, timeout=12):
        result = self._collect_biquuge_directory_catalog(
            book_url,
            timeout=timeout,
            fetcher=self._fetch_tracked_page_standard,
            source_label='standard',
        )
        if result.get('chapter_catalog'):
            logger.info(
                f"[novel] directory resolved via standard: pages={len(result.get('directory_pages', []))}, chapters={len(result.get('chapter_catalog', []))}"
            )
            return result

        logger.info('[novel] standard directory parse empty, retry with browser bootstrap')
        browser_result = self._collect_biquuge_directory_catalog(
            book_url,
            timeout=max(timeout, 12),
            fetcher=lambda url, timeout=timeout: self._fetch_browser_tracked_page(url, timeout=timeout, wait_time=0.8),
            source_label='browser',
        )
        if browser_result.get('chapter_catalog'):
            logger.info(
                f"[novel] directory resolved via browser: pages={len(browser_result.get('directory_pages', []))}, chapters={len(browser_result.get('chapter_catalog', []))}"
            )
            return browser_result

        return result

    def _extract_biquuge_chapter_payload(self, soup, chapter_url, fallback_title=''):
        chapter_title = self._extract_field(soup, '.bookname h1 || h1') or fallback_title
        content = self._extract_biquuge_chapter_text(soup)
        breadcrumb = self._extract_field(soup, '.con_top || .path || .nav')

        return {
            'chapter_title': self.validator.clean_text(chapter_title),
            'chapter_url': chapter_url,
            'content': self._clean_biquuge_chapter_text(content),
            'breadcrumb': self.validator.clean_text(breadcrumb),
        }

    def _extract_text_block(self, element, selector):
        candidates = [s.strip() for s in selector.split('||') if s.strip()]
        if not candidates:
            return ''

        for candidate in candidates:
            if '@' in candidate:
                continue
            target = element.select_one(candidate)
            if target:
                value = target.get_text('\n', strip=True)
                if value:
                    return value
        return ''

    def _extract_longest_text_block(self, soup, selectors):
        best_text = ''
        best_score = 0
        for selector in selectors:
            try:
                nodes = soup.select(selector)
            except Exception:
                continue
            for node in nodes:
                text = node.get_text('\n', strip=True)
                if not text:
                    continue
                score = len(text) - len(node.select('a')) * 20
                if score > best_score:
                    best_score = score
                    best_text = text
        return best_text

    def _extract_biquuge_chapter_text(self, soup):
        selector_text = self._extract_text_block(
            soup,
            '#content || #chaptercontent || #BookText || .read-content || .yd_text2 || .content || .showtxt || .txtnav || .page-content || .article-content',
        )
        cleaned_selector_text = self._clean_biquuge_chapter_text(selector_text)
        if cleaned_selector_text:
            return cleaned_selector_text

        heuristic_text = self._extract_longest_text_block(
            soup,
            [
                '#chaptercontent',
                '#content',
                '#BookText',
                '.read-content',
                '.yd_text2',
                '.txtnav',
                '.showtxt',
                '.content',
                'article',
                'section',
                'div',
            ],
        )
        return self._clean_biquuge_chapter_text(heuristic_text)

    def _is_biquuge_chapter_blocked(self, soup):
        if not soup:
            return True
        text = soup.get_text('\n', strip=True).lower()
        markers = [
            '访问频繁',
            '安全验证',
            '验证码',
            '403 forbidden',
            'access denied',
            '请稍后再试',
            '请求过于频繁',
            '系统检测到异常',
        ]
        return any(marker in text for marker in markers)

    def _diagnose_biquuge_chapter_page(self, soup, chapter_url, fallback_title=''):
        page_title = self._extract_field(soup, '.bookname h1 || h1 || title') or fallback_title
        raw_text = self._extract_text_block(
            soup,
            '#content || #chaptercontent || #BookText || .read-content || .yd_text2 || .content || .showtxt || .txtnav',
        )
        cleaned_text = self._clean_biquuge_chapter_text(raw_text)
        doc_text = self.validator.clean_text(soup.get_text('\n', strip=True))[:180] if soup else ''
        blocked = self._is_biquuge_chapter_blocked(soup)
        return (
            f"title={page_title!r}, blocked={blocked}, raw_len={len(raw_text)}, "
            f"clean_len={len(cleaned_text)}, snippet={doc_text!r}, url={chapter_url}"
        )

    def _clean_biquuge_chapter_text(self, text):
        if not text:
            return ''

        lines = []
        for raw_line in str(text).replace('\r', '\n').split('\n'):
            line = raw_line.strip()
            if not line:
                continue
            if re.match(r'^(?:第)?\s*\(?\d+\s*/\s*\d+\)?\s*页$', line):
                continue
            lower = line.lower()
            if any(
                marker in lower
                for marker in [
                    '最新网址',
                    '请收藏',
                    '手机用户请',
                    '天才一秒记住',
                    'biquuge.com',
                    '笔趣阁',
                    '推荐下',
                ]
            ):
                continue
            lines.append(line)

        return '\n'.join(lines)

    def _extract_biquuge_chapter_subpage_urls(self, soup, source_url, chapter_url=''):
        current_url = urljoin(chapter_url or source_url, source_url)
        base_url = self._normalize_biquuge_chapter_url(chapter_url or source_url)
        subpages = set()
        for anchor in soup.select('a[href]'):
            href = (anchor.get('href') or '').strip()
            if not href:
                continue
            full_url = urljoin(current_url, href)
            if not self._looks_like_biquuge_chapter_url(full_url):
                continue
            if self._normalize_biquuge_chapter_url(full_url) != base_url:
                continue
            if full_url == current_url:
                continue
            subpages.add(full_url)
        return sorted(subpages, key=self._biquuge_chapter_sort_key)

    def _fetch_biquuge_chapter_worker(self, chapter, index, timeout=8):
        chapter_url = chapter['chapter_url']
        session = self._get_thread_session()
        self._increment_stats(total_pages=1)
        soup = self._fetch_soup_with_session(session, chapter_url, timeout=timeout, max_retries=self.novel_chapter_retry_count)
        if not soup:
            if index <= 3:
                logger.warning(f"[novel] chapter fetch returned empty: index={index}, url={chapter_url}")
            self._increment_stats(failed_pages=1)
            return index, None, chapter

        if self._is_biquuge_chapter_blocked(soup):
            if index <= 3:
                logger.warning(
                    f"[novel] chapter page blocked: {self._diagnose_biquuge_chapter_page(soup, chapter_url, chapter.get('chapter_title', ''))}"
                )
            self._increment_stats(failed_pages=1)
            return index, None, chapter

        payload = self._extract_biquuge_chapter_payload(
            soup,
            chapter_url,
            fallback_title=chapter.get('chapter_title', ''),
        )
        extra_parts = []
        visited_subpages = {chapter_url}
        queued_subpages = list(
            self._extract_biquuge_chapter_subpage_urls(
                soup,
                chapter_url,
                chapter_url=chapter_url,
            )
        )
        while queued_subpages and len(visited_subpages) - 1 < self.novel_max_subpages_per_chapter:
            subpage_url = queued_subpages.pop(0)
            if subpage_url in visited_subpages:
                continue
            visited_subpages.add(subpage_url)
            self._increment_stats(total_pages=1)
            sub_soup = self._fetch_soup_with_session(session, subpage_url, timeout=timeout, max_retries=1)
            if not sub_soup:
                self._increment_stats(failed_pages=1)
                continue
            self._increment_stats(success_pages=1)
            sub_text = self._extract_biquuge_chapter_text(sub_soup)
            if sub_text and sub_text not in extra_parts and sub_text != payload.get('content', ''):
                extra_parts.append(sub_text)

            nested_subpages = self._extract_biquuge_chapter_subpage_urls(
                sub_soup,
                subpage_url,
                chapter_url=chapter_url,
            )
            for nested_url in nested_subpages:
                if nested_url not in visited_subpages and nested_url not in queued_subpages:
                    queued_subpages.append(nested_url)

        if extra_parts:
            merged = [payload.get('content', '')] if payload.get('content') else []
            merged.extend(extra_parts)
            payload['content'] = '\n'.join(part for part in merged if part)

        if not payload.get('content'):
            if index <= 3:
                logger.warning(
                    f"[novel] empty chapter content: {self._diagnose_biquuge_chapter_page(soup, chapter_url, chapter.get('chapter_title', ''))}"
                )
            self._increment_stats(failed_pages=1)
            return index, None, chapter

        payload['index'] = index
        self._increment_stats(success_pages=1)
        return index, payload, None

    def _crawl_biquuge_chapters_parallel(self, chapter_catalog, timeout=8):
        if not chapter_catalog:
            return [], []

        sample_count = min(self.novel_sample_chapter_count, len(chapter_catalog))
        sample_chapters = chapter_catalog[:sample_count]
        sample_payloads = []
        sample_failed = []
        for index, chapter in enumerate(sample_chapters, start=1):
            # Check if stop has been requested
            if self.is_stop_requested():
                logger.info('[crawler] stop requested, halting chapter sampling')
                return [], chapter_catalog
            
            _, payload, failed = self._fetch_biquuge_chapter_worker(chapter, index, timeout)
            if payload:
                sample_payloads.append(payload)
            elif failed:
                sample_failed.append(failed)

        if sample_count and not sample_payloads:
            logger.warning(
                f'[novel] first {sample_count} sample chapters all failed, try browser bootstrap sync before large parallel crawl'
            )
            bootstrap_url = sample_chapters[0]['chapter_url']
            if self._sync_session_from_advanced(bootstrap_url):
                sample_payloads = []
                sample_failed = []
                for index, chapter in enumerate(sample_chapters, start=1):
                    # Check if stop has been requested
                    if self.is_stop_requested():
                        logger.info('[crawler] stop requested, halting chapter re-sampling')
                        return [], chapter_catalog
                    
                    _, payload, failed = self._fetch_biquuge_chapter_worker(chapter, index, timeout)
                    if payload:
                        sample_payloads.append(payload)
                    elif failed:
                        sample_failed.append(failed)

        if sample_count and not sample_payloads:
            logger.warning('[novel] sample chapters still failed after bootstrap; abort remaining chapter crawl early')
            return [], chapter_catalog

        worker_count = min(self.novel_max_workers, max(12, len(chapter_catalog) // 16 + 8))
        worker_count = min(worker_count, len(chapter_catalog))
        logger.info(f'[novel] chapter workers={worker_count}')

        ordered_results = [None] * len(chapter_catalog)
        failed = list(sample_failed)
        completed = sample_count
        total = len(chapter_catalog)

        for payload in sample_payloads:
            ordered_results[payload['index'] - 1] = payload

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(self._fetch_biquuge_chapter_worker, chapter, index, timeout): (index, chapter)
                for index, chapter in enumerate(chapter_catalog[sample_count:], start=sample_count + 1)
            }
            for future in as_completed(future_map):
                # Check if stop has been requested
                if self.is_stop_requested():
                    logger.info('[crawler] stop requested, halting chapter downloads')
                    # Cancel remaining futures
                    for f in future_map:
                        if not f.done():
                            f.cancel()
                    break
                
                completed += 1
                index, chapter = future_map[future]
                try:
                    result_index, payload, failed_chapter = future.result()
                except Exception as e:
                    logger.warning(f'[novel] chapter worker crashed {index}/{total}: {e}')
                    payload = None
                    failed_chapter = chapter
                    result_index = index

                if payload:
                    ordered_results[result_index - 1] = payload
                elif failed_chapter:
                    failed.append(failed_chapter)

                if completed == 1 or completed % 25 == 0 or completed == total:
                    logger.info(f'[novel] chapter progress {completed}/{total}')

        chapters = [item for item in ordered_results if item]
        self._increment_stats(total_items=len(chapters))
        return chapters, failed

    def _validate_biquuge_book_integrity(self, book_data):
        if not isinstance(book_data, dict):
            return True, {}

        book_url = book_data.get('book_url', '')
        expected_root = self._normalize_biquuge_book_url(book_url)
        if not expected_root:
            directory_url = book_data.get('directory_url', '')
            expected_root = self._normalize_biquuge_book_url(directory_url)

        chapters = book_data.get('chapters', []) or []
        if not expected_root or not chapters:
            return True, {'expected_root': expected_root, 'chapter_roots': []}

        chapter_roots = {}
        mismatched = []
        for chapter in chapters:
            chapter_url = chapter.get('chapter_url', '')
            chapter_root = self._normalize_biquuge_book_url(chapter_url)
            if not chapter_root:
                continue
            chapter_roots[chapter_root] = chapter_roots.get(chapter_root, 0) + 1
            if chapter_root != expected_root:
                mismatched.append(
                    {
                        'chapter_title': chapter.get('chapter_title', ''),
                        'chapter_url': chapter_url,
                        'chapter_root': chapter_root,
                    }
                )

        details = {
            'expected_root': expected_root,
            'chapter_roots': chapter_roots,
            'mismatched': mismatched,
        }
        return not mismatched, details

    def crawl_biquuge_full_book(self, keyword_or_url, max_chapters=None, timeout=12):
        target = self.search_biquuge_book(keyword_or_url, timeout=timeout)
        if not target:
            self.last_error_reason = 'novel_book_not_found'
            return None

        book_url = target.get('book_url') or target.get('matched_url')
        if not book_url:
            self.last_error_reason = 'novel_book_not_found'
            return None

        detail_soup = self._fetch_tracked_page_standard(book_url, timeout=timeout)
        if not detail_soup:
            logger.info('[novel] standard detail fetch failed, retry with browser bootstrap')
            detail_soup = self._fetch_browser_tracked_page(book_url, timeout=max(timeout, 12), wait_time=0.8)
        if not detail_soup:
            self.last_error_reason = 'novel_book_page_failed'
            return None

        book_meta = self._extract_biquuge_book_meta(detail_soup, book_url)
        # Ensure we have a title for the filename
        if not book_meta.get('book_title'):
            # Fallback to target title or query
            book_meta['book_title'] = target.get('title') or (keyword_or_url if not self.validator.validate_url(keyword_or_url) else "Unknown_Book")
        
        # Strip illegal characters from title for safe naming
        book_meta['book_title'] = self._sanitize_filename(book_meta['book_title'])

        directory_seed = book_meta.get('directory_url') or book_url
        catalog = self._resolve_biquuge_directory_catalog(directory_seed, timeout=timeout)
        chapter_catalog = catalog.get('chapter_catalog') or []
        if not chapter_catalog:
            self.last_error_reason = 'novel_directory_not_found'
            logger.warning(f'[novel] no chapter catalog found for: {book_url}')
            return None

        if max_chapters and len(chapter_catalog) > max_chapters:
            chapter_catalog = chapter_catalog[:max_chapters]

        logger.info(
            f"[novel] crawl chapters begin: {book_meta.get('book_title') or keyword_or_url} "
            f"({len(chapter_catalog)} chapters, strategy=hybrid)"
        )
        chapters, failed_chapters = self._crawl_biquuge_chapters_parallel(
            chapter_catalog,
            timeout=min(max(timeout, 8), 12),
        )

        if not chapters:
            self.last_error_reason = 'novel_chapter_fetch_failed'
            return None

        result = {
            '_save_type': 'novel_book',
            'query': keyword_or_url,
            'book_title': book_meta.get('book_title') or target.get('title') or keyword_or_url,
            'book_url': book_meta.get('book_url') or book_url,
            'directory_url': catalog.get('directory_url') or directory_seed,
            'book_info': book_meta.get('book_info', ''),
            'intro': book_meta.get('intro', ''),
            'cover': book_meta.get('cover', ''),
            'chapter_count': len(chapters),
            'catalog_count': len(chapter_catalog),
            'failed_chapter_count': len(failed_chapters),
            'chapters': chapters,
        }
        integrity_ok, integrity_details = self._validate_biquuge_book_integrity(result)
        if not integrity_ok:
            self.last_error_reason = 'novel_book_mixed_roots'
            sample = integrity_details.get('mismatched', [])[:3]
            logger.error(
                f"[novel] mixed book roots detected, expected={integrity_details.get('expected_root')}, "
                f"roots={integrity_details.get('chapter_roots')}, sample={sample}"
            )
            return None

        self.last_error_reason = ''
        return result

    def save_novel_book(self, book_data, filename=None):
        if not isinstance(book_data, dict) or not book_data.get('chapters'):
            logger.warning('novel save skipped: no chapters')
            return None

        integrity_ok, integrity_details = self._validate_biquuge_book_integrity(book_data)
        if not integrity_ok:
            logger.error(
                f"[novel] save blocked due to mixed book roots, expected={integrity_details.get('expected_root')}, "
                f"roots={integrity_details.get('chapter_roots')}"
            )
            self.last_error_reason = 'novel_book_mixed_roots'
            return None

        book_title = book_data.get('book_title') or 'novel_book'
        base_name = filename or f"{self._sanitize_filename(book_title)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        book_dir = os.path.join(self.output_dir, base_name)
        os.makedirs(book_dir, exist_ok=True)

        safe_title = self._sanitize_filename(book_title)
        txt_path = os.path.join(book_dir, f'{safe_title}.txt')
        json_path = os.path.join(book_dir, f'{safe_title}.json')

        header_lines = [
            f"书名：{book_title}",
            f"来源：{book_data.get('book_url', '')}",
            f"目录页：{book_data.get('directory_url', '')}",
            f"章节数：{book_data.get('chapter_count', 0)}",
        ]
        if book_data.get('book_info'):
            header_lines.append(f"信息：{book_data.get('book_info')}")
        if book_data.get('intro'):
            header_lines.extend(['', '简介：', book_data.get('intro')])

        txt_chunks = ['\n'.join(header_lines), '\n\n' + ('=' * 40) + '\n']
        for chapter in book_data.get('chapters', []):
            txt_chunks.append(f"\n{chapter.get('index', 0):04d}. {chapter.get('chapter_title', '')}\n")
            txt_chunks.append(f"{chapter.get('content', '')}\n")

        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(''.join(txt_chunks).strip() + '\n')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(book_data, f, ensure_ascii=False, indent=2)
            logger.info(f'saved novel book: {txt_path}')
            return {
                'save_type': 'novel_book',
                'path': txt_path,
                'directory': book_dir,
                'saved_count': len(book_data.get('chapters', [])),
                'files': [txt_path, json_path],
            }
        except Exception as e:
            logger.error(f'save novel book failed: {e}')
            return None

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

    def request_stop(self):
        """Request the crawler to stop gracefully."""
        self._stop_requested = True
        logger.info('[crawler] stop requested')

    def is_stop_requested(self):
        """Check if stop has been requested."""
        return self._stop_requested

    def close(self):
        """Close all resources and cleanup."""
        if getattr(self, '_closed', False):
            return
        
        self._closed = True
        logger.info(f'[cleanup] closing crawler instance {id(self)}')
        
        # Close advanced crawler
        if self.advanced_crawler:
            try:
                self.advanced_crawler.close()
                logger.debug('[cleanup] advanced crawler closed')
            except Exception as e:
                logger.warning(f'[cleanup] failed to close advanced crawler: {e}')
            finally:
                self.advanced_crawler = None
        
        # Close main session
        if getattr(self, 'session', None):
            try:
                self.session.close()
                logger.debug('[cleanup] main session closed')
            except Exception as e:
                logger.warning(f'[cleanup] failed to close main session: {e}')
            finally:
                self.session = None
        
        # Clean up thread-local sessions
        if hasattr(self, '_thread_local'):
            try:
                if hasattr(self._thread_local, 'session'):
                    try:
                        self._thread_local.session.close()
                        logger.debug('[cleanup] thread-local session closed')
                    except Exception as e:
                        logger.warning(f'[cleanup] failed to close thread-local session: {e}')
                    delattr(self._thread_local, 'session')
            except Exception as e:
                logger.warning(f'[cleanup] failed to cleanup thread-local storage: {e}')
        
        # Clear caches and state
        try:
            self._primed_domains.clear()
            logger.debug('[cleanup] cleared primed domains cache')
        except Exception as e:
            logger.warning(f'[cleanup] failed to clear caches: {e}')
        
        logger.info(f'[cleanup] crawler instance {id(self)} closed successfully')

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            if not getattr(self, '_closed', True):
                logger.warning(f'[cleanup] crawler {id(self)} not explicitly closed, cleaning up in __del__')
                self.close()
        except Exception as e:
            logger.error(f'[cleanup] error in __del__: {e}')

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
        return False


def main():
    print('UniversalCrawlerV2 ready.')


if __name__ == '__main__':
    main()
