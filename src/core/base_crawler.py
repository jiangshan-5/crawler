import requests
import threading
import time
import logging
from urllib.parse import urlparse

from src.utils.rate_limiter import RateLimiter
from src.utils.data_validator import DataValidator
from src.core.config import RetryConfig
from src.config.site_rules import get_site_rule

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class BaseCrawler:
    """
    Base class providing core networking, session management, 
    and statistics tracking for all crawlers.
    """
    def __init__(self, requests_per_second=1, max_retries=3):
        self._closed = False
        self._stop_requested = False
        self.max_retries = max_retries
        self.rate_limiter = RateLimiter(requests_per_second)
        self.validator = DataValidator()
        self._stats_lock = threading.Lock()
        self._thread_local = threading.local()
        
        self.stats = {
            'total_pages': 0,
            'success_pages': 0,
            'failed_pages': 0,
            'retried_pages': 0,
            'total_items': 0,
            'cache_hits': 0,
        }
        
        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        self.session.trust_env = False
        adapter = requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=64, max_retries=0)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/120.0.0.0 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def _calculate_backoff(self, attempt):
        return RetryConfig.INITIAL_BACKOFF * (RetryConfig.BACKOFF_FACTOR ** attempt)

    def _increment_stats(self, **delta):
        if not delta: return
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
        except: pass
        return session

    def request_stop(self):
        self._stop_requested = True

    def is_stop_requested(self):
        return self._stop_requested

    def fetch_page(self, url, timeout=12):
        """Simple wrapper for fetching a page and returning Soup."""
        self.rate_limiter.wait()
        session = self._get_thread_session()
        return self._fetch_soup_with_session(session, url, timeout=timeout)

    def _fetch_with_retry(self, url, timeout=12):
        """Alias for fetch_page with retry - used by NovelWorkflow."""
        return self.fetch_page(url, timeout=timeout)

    def _fetch_soup_with_session(self, session, url, timeout=12, max_retries=None):
        if max_retries is None: max_retries = self.max_retries
        
        # Get site-specific rules
        rules = get_site_rule(url)
        headers = dict(session.headers)
        if rules.get("headers"):
            headers.update(rules["headers"])
        
        for attempt in range(max_retries + 1):
            if self.is_stop_requested(): return None
            try:
                response = session.get(url, timeout=timeout, headers=headers)
                
                if response.status_code in RetryConfig.RETRY_HTTP_CODES and attempt < max_retries:
                    time.sleep(self._calculate_backoff(attempt))
                    self._increment_stats(retried_pages=1)
                    continue
                
                if response.status_code in (403, 404): 
                    self._increment_stats(failed_pages=1)
                    return None
                
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for anti-bot blocks using rules
                if self.is_blocked(soup, rules):
                    logger.warning(f"Anti-bot block detected on: {url}")
                    self._increment_stats(failed_pages=1)
                    return None
                    
                self._increment_stats(success_pages=1)
                return soup
                
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(self._calculate_backoff(attempt))
                    self._increment_stats(retried_pages=1)
                    continue
                logger.error(f"fetch failed after {max_retries} retries: {url} -> {e}")
                self._increment_stats(failed_pages=1)
                return None
        return None

    def is_blocked(self, soup, rules):
        """Check if the page content contains anti-bot markers."""
        if not soup: return True
        markers = rules.get("anti_bot_markers", [])
        if not markers: return False
        
        text = str(soup).lower()
        return any(marker.lower() in text for marker in markers)

    def get_stats(self):
        with self._stats_lock:
            s = dict(self.stats)
            total = s['success_pages'] + s['failed_pages']
            s['success_rate'] = f"{(s['success_pages']/total*100):.1f}%" if total > 0 else "0%"
            return s
