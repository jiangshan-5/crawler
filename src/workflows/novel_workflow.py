import os
import re
import json
import csv
import logging
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin, quote_plus
from bs4 import BeautifulSoup
from src.config.site_rules import get_site_rule

logger = logging.getLogger(__name__)

class NovelWorkflow:
    """
    Dedicated workflow for novel extraction (Biquuge specific).
    Decoupled from the main engine to keep the code modular.
    """
    def __init__(self, engine):
        self.engine = engine  # Reference to BaseCrawler or Engine
        self.validator = engine.validator
        
        # Configuration sourced from site_rules (data-driven)
        rules = get_site_rule("https://www.biquuge.com/")
        perf = rules.get("performance", {})
        
        self.max_workers = perf.get("max_workers", 16)
        self.chapter_retry_count = perf.get("retry_count", 2)
        self.sample_chapter_count = perf.get("sample_count", 5)
        self.max_subpages_per_chapter = perf.get("max_subpages", 20)

    def _is_biquuge_url(self, url):
        return bool(url and 'biquuge.com' in url)

    def _normalize_biquuge_book_url(self, url):
        if not isinstance(url, str) or not url.strip():
            return ''
        full_url = urljoin('https://www.biquuge.com/', url.strip())
        if not self.validator.validate_url(full_url):
            return ''
        parsed = urlparse(full_url)
        path = parsed.path or ''
        # Must match /digits/digits/ pattern to be a valid book directory
        match = re.match(r'^/(\d+)/(\d+)/(?:index(?:_\d+)?\.html)?$', path)
        if not match:
            match = re.match(r'^/(\d+)/(\d+)/\d+\.html$', path)
        if not match:
            return ''  # Not a book URL (e.g. homepage '/', nav links)
        return f'{parsed.scheme}://{parsed.netloc}/{match.group(1)}/{match.group(2)}/'

    def _looks_like_biquuge_chapter_url(self, url):
        if not self._is_biquuge_url(url): return False
        path = (urlparse(url).path or '').lower()
        return bool(re.match(r'^/\d+/\d+/\d+(?:_\d+)?\.html$', path))

    def _normalize_biquuge_chapter_url(self, url):
        if not isinstance(url, str) or not url.strip(): return ''
        full_url = urljoin('https://www.biquuge.com/', url.strip())
        parsed = urlparse(full_url)
        match = re.match(r'^(?P<prefix>/\d+/\d+/)(?P<chapter>\d+)(?:_(?P<page>\d+))?\.html$', parsed.path or '')
        return f'{parsed.scheme}://{parsed.netloc}{match.group("prefix")}{match.group("chapter")}.html' if match else full_url

    def _biquuge_chapter_sort_key(self, url):
        path = (urlparse(url).path or '').lower()
        match = re.match(r'^/\d+/\d+/(\d+)(?:_(\d+))?\.html$', path)
        if match: return int(match.group(1)), int(match.group(2) or 0)
        return 999999999, 999999999

    def _fetch_tracked_page(self, url, timeout=10):
        self.engine._increment_stats(total_pages=1)
        return self.engine.fetch_page(url, timeout=timeout)

    def _fetch_tracked_page_standard(self, url, timeout=10):
        self.engine._increment_stats(total_pages=1)
        self.engine.rate_limiter.wait()
        return self.engine._fetch_with_retry(url, timeout)

    def _build_biquuge_search_urls(self, keyword):
        rules = get_site_rule("https://www.biquuge.com/")
        templates = rules.get("search_templates", [])
        
        if not templates:
            # Fallback to a safe default if rules missing
            templates = ['https://www.biquuge.com/search.php?keyword={q}']
            
        urls = []
        seen = set()
        for encoding in ('utf-8', 'gbk'):
            try: encoded = quote_plus(keyword, encoding=encoding, errors='ignore')
            except: encoded = quote_plus(keyword)
            for template in templates:
                url = template.format(q=encoded)
                if url not in seen:
                    seen.add(url); urls.append(url)
        return urls

    def _looks_like_biquuge_directory_url(self, url):
        return self._is_biquuge_url(url) and '/book/' not in url.lower() and not self._looks_like_biquuge_chapter_url(url)

    def search_book(self, keyword, timeout=12):
        query = (keyword or '').strip()
        if not query: return None

        # If the input looks like a URL, try to normalize it as a book URL
        if self.validator.validate_url(query):
            book_url = self._normalize_biquuge_book_url(query)
            if book_url:
                return {'query': query, 'book_url': book_url}
            # Fall through to keyword search if URL isn't a valid book URL

        search_urls = self._build_biquuge_search_urls(query)
        for search_url in search_urls:
            logger.info(f"[novel] trying search URL: {search_url}")
            soup = self._fetch_tracked_page_standard(search_url, timeout=timeout)
            if not soup:
                logger.warning(f"[novel] no response from {search_url}")
                continue

            matches = self._extract_biquuge_search_matches(soup, query)
            if matches:
                logger.info(f"[novel] best match: '{matches[0]['title']}' score={matches[0]['score']} url={matches[0]['book_url']}")
                return matches[0]
            logger.info(f"[novel] no matches found on {search_url}")

        logger.error(f"[novel] search exhausted all URLs, no book found for '{query}'")
        return None

    def _extract_biquuge_search_matches(self, soup, keyword):
        """
        Parse search results using .bookbox structure (confirmed via browser audit).
        Each result: .bookbox > .bookinfo > h4 > a[href, title]
        """
        matches = {}

        # Primary: structured .bookbox results (most accurate)
        for box in soup.select('.bookbox'):
            anchor = box.select_one('.bookinfo h4 a') or box.select_one('h4 a') or box.select_one('a[href]')
            if not anchor: continue
            href = (anchor.get('href') or '').strip()
            if not href: continue
            full_url = urljoin('https://www.biquuge.com/', href)
            normalized_url = self._normalize_biquuge_book_url(full_url)
            if not normalized_url: continue  # Skip non-book URLs (homepage, nav links, etc.)
            title = (anchor.get('title') or anchor.get_text(strip=True) or '').strip()
            author_el = box.select_one('.bookinfo p')
            author = author_el.get_text(strip=True) if author_el else ''
            score = self._score_biquuge_candidate(title, keyword, full_url)
            if score <= 0: continue
            if normalized_url not in matches or matches[normalized_url]['score'] < score:
                matches[normalized_url] = {
                    'book_url': normalized_url,
                    'title': title,
                    'author': author,
                    'score': score
                }

        # Fallback: generic anchor scan if no .bookbox found
        if not matches:
            for anchor in soup.select('a[href]'):
                href = (anchor.get('href') or '').strip()
                if not href: continue
                full_url = urljoin('https://www.biquuge.com/', href)
                if not self._is_biquuge_url(full_url): continue
                normalized_url = self._normalize_biquuge_book_url(full_url)
                if not normalized_url: continue  # Must be a valid /digits/digits/ book URL
                title = (anchor.get('title') or anchor.get_text(' ', strip=True) or '').strip()
                score = self._score_biquuge_candidate(title, keyword, full_url)
                if score <= 0: continue
                if normalized_url not in matches or matches[normalized_url]['score'] < score:
                    matches[normalized_url] = {
                        'book_url': normalized_url, 'title': title, 'score': score
                    }

        results = sorted(matches.values(), key=lambda x: -x['score'])
        if results:
            logger.info(f"[novel] search top candidates: {[(r['title'], r['score']) for r in results[:3]]}")
        return results

    def _score_biquuge_candidate(self, text, keyword, url):
        """
        Score a candidate title against the keyword.
        Higher is better; exact title match wins.
        """
        haystack = (text or '').strip().lower()
        # Strip common prefixes like 【武侠】【玄幻】 etc.
        haystack_clean = re.sub(r'^[\[\【][^\]\】]+[\]\】]\s*', '', haystack)
        query = (keyword or '').strip().lower()
        if not query or not haystack: return 0

        # Exact match (highest priority)
        if haystack_clean == query or haystack == query: return 200
        # Query is a substring of title (very strong)
        if query in haystack_clean or query in haystack: return 150
        # All query tokens found in title
        tokens = [t.strip() for t in re.split(r'[\s/|，,·：:]+', keyword) if t.strip()]
        if tokens and all(t.lower() in haystack for t in tokens): return 120
        # Partial token match
        matched_tokens = sum(1 for t in tokens if t.lower() in haystack)
        score = matched_tokens * 20 if matched_tokens else 0

        # URL context boost/penalty
        if self._looks_like_biquuge_directory_url(url): score += 10
        if self._looks_like_biquuge_chapter_url(url): score -= 50
        return score

    def _resolve_biquuge_directory_catalog(self, book_url, timeout=12):
        """Full implementation of biquuge directory resolution with fallback scanning."""
        logger.info(f"[novel] resolving directory for: {book_url}")
        soup = self._fetch_tracked_page(book_url, timeout=timeout)
        if not soup: return {'chapter_catalog': [], 'info': '', 'synopsis': ''}

        # Extract book metadata from the main page
        book_meta = self._extract_book_metadata(soup)

        expected_root_url = self._normalize_biquuge_book_url(book_url) or book_url
        chapters = self._extract_biquuge_chapter_catalog(soup, book_url, expected_root_url=expected_root_url)
        
        # If no chapters, it might be a multi-page directory
        if not chapters:
            for next_page in self._extract_biquuge_directory_page_urls(soup, book_url, expected_root_url=expected_root_url):
                page_soup = self._fetch_tracked_page(next_page, timeout=timeout)
                if page_soup:
                    page_chapters = self._extract_biquuge_chapter_catalog(page_soup, next_page, expected_root_url=expected_root_url)
                    chapters.extend(page_chapters)

        sorted_chapters = sorted(chapters, key=lambda x: self._biquuge_chapter_sort_key(x['chapter_url']))
        return {
            'chapter_catalog': sorted_chapters,
            'info': book_meta.get('info', ''),
            'synopsis': book_meta.get('synopsis', '')
        }

    def _extract_book_metadata(self, soup):
        """Extract book info and synopsis from the book's main page."""
        info_parts = []
        # Title
        title_el = soup.select_one('.bookinfo h1, h1.bookTitle, #info h1')
        if title_el:
            info_parts.append(title_el.get_text(strip=True))
        # Author / update info block
        info_el = soup.select_one('#info, .bookinfo .author, .bookinfo p')
        if info_el:
            info_parts.append(info_el.get_text(' ', strip=True))
        # Try broader meta fallback
        if not info_parts:
            meta = soup.select_one('.info, .book-info, [class*=bookintro], [class*=info]')
            if meta:
                info_parts.append(meta.get_text(' ', strip=True)[:300])

        # Synopsis
        synopsis = ''
        for sel in ['#intro', '.intro', '.synopsis', '[class*=intro]', '[class*=desc]']:
            el = soup.select_one(sel)
            if el:
                synopsis = el.get_text('\n', strip=True)
                break

        return {'info': ' '.join(info_parts), 'synopsis': synopsis}

    def _extract_biquuge_chapter_catalog(self, soup, page_url, expected_root_url=''):
        catalog = []
        seen = set()
        for anchor in soup.select('a[href]'):
            href = (anchor.get('href') or '').strip()
            if not href: continue
            full_url = urljoin(page_url, href)
            if not self._looks_like_biquuge_chapter_url(full_url): continue
            
            normalized = self._normalize_biquuge_chapter_url(full_url)
            if normalized in seen: continue
            seen.add(normalized)
            
            title = (anchor.get('title') or anchor.get_text(strip=True) or '').strip()
            catalog.append({'chapter_title': title, 'chapter_url': normalized})
        return catalog

    def _extract_biquuge_directory_page_urls(self, soup, book_url, expected_root_url=''):
        pages = {book_url}
        for anchor in soup.select('a[href]'):
            href = (anchor.get('href') or '').strip()
            if not href: continue
            full_url = urljoin(book_url, href)
            if self._looks_like_biquuge_directory_url(full_url):
                pages.add(full_url)
        return sorted(list(pages))

    def _extract_biquuge_chapter_payload(self, soup, chapter_url, fallback_title=''):
        # Use the engine's robust extraction for the title
        chapter_title = self.engine._extract_single_field(soup, '.bookname h1 || h1 || title') or fallback_title
        
        # Text block heuristic logic
        content = self._extract_biquuge_chapter_text(soup)
        breadcrumb = self.engine._extract_single_field(soup, '.con_top || .path || .nav')
        
        return {
            'chapter_title': self.validator.clean_text(str(chapter_title)),
            'chapter_url': chapter_url,
            'content': self._clean_biquuge_chapter_text(content),
            'breadcrumb': self.validator.clean_text(str(breadcrumb))
        }

    def _extract_biquuge_chapter_text(self, soup):
        # Specific selectors first
        raw = self.engine._extract_single_field(soup, '#content || #chaptercontent || #BookText || .read-content || .yd_text2 || .content')
        if raw: return raw
        
        # Fallback to longest block heuristic
        best_text = ''
        best_score = 0
        for sel in ['div', 'article', 'section']:
            for node in soup.select(sel):
                text = node.get_text('\n', strip=True)
                if not text: continue
                # Score based on length and link density (novel pages have few links in text)
                score = len(text) - len(node.select('a')) * 30
                if score > best_score:
                    best_score = score
                    best_text = text
        return best_text

    def _clean_biquuge_chapter_text(self, text):
        if not text: return ""
        lines = []
        for raw_line in str(text).replace('\r', '\n').split('\n'):
            line = raw_line.strip()
            if not line: continue
            # Filter ads and navigation debris
            if any(m in line.lower() for m in ['最新网址', '请收藏', '笔趣阁', 'biquuge.com', '推荐下']):
                continue
            lines.append(line)
        return '\n'.join(lines)

    def _fetch_chapter_worker(self, chapter, index, timeout=8):
        chapter_url = chapter['chapter_url']
        session = self.engine._get_thread_session()
        self.engine._increment_stats(total_pages=1)

        # -- Page 1 --
        soup = self.engine._fetch_soup_with_session(session, chapter_url, timeout=timeout)
        if not soup:
            self.engine._increment_stats(failed_pages=1)
            return index, None, chapter

        payload = self._extract_biquuge_chapter_payload(soup, chapter_url, fallback_title=chapter.get('chapter_title', ''))
        if not payload.get('content'):
            self.engine._increment_stats(failed_pages=1)
            return index, None, chapter

        # Store each sub-page separately for legacy page marker format
        pages = [payload['content']]
        visited = {chapter_url}
        current_soup = soup
        current_url = chapter_url

        # -- Multi-page: follow 下一页 links --
        for _ in range(self.max_subpages_per_chapter - 1):
            next_url = self._extract_chapter_next_page(current_soup, current_url)
            if not next_url or next_url in visited:
                break
            visited.add(next_url)
            self.engine._increment_stats(total_pages=1)
            next_soup = self.engine._fetch_soup_with_session(session, next_url, timeout=timeout)
            if not next_soup:
                break
            sub_text = self._extract_biquuge_chapter_text(next_soup)
            if sub_text:
                pages.append(self._clean_biquuge_chapter_text(sub_text))
            current_soup = next_soup
            current_url = next_url

        payload['pages'] = pages                        # list of per-page text
        payload['content'] = '\n'.join(pages)          # merged full content
        payload['page_count'] = len(pages)
        payload['index'] = index
        self.engine._increment_stats(success_pages=1)
        return index, payload, None

    def _extract_chapter_next_page(self, soup, current_url):
        """
        Detect the next SUB-PAGE of the current chapter.

        Key insight for biquuge: the site uses '下一章' as the link text for
        BOTH chapter-level navigation AND intra-chapter page navigation.
        We distinguish them by checking whether the target URL has the SAME
        chapter ID with a page-number suffix (_2, _3 ...).

        Returns the RAW (un-normalized) URL so the '_N' suffix is preserved
        in the `visited` set, allowing each sub-page to be fetched only once.
        """
        # Extract current chapter identity from URL
        parsed = urlparse(current_url)
        ch_match = re.match(
            r'^/(\d+)/(\d+)/(\d+)(?:_\d+)?\.html$', parsed.path or ''
        )
        if not ch_match:
            return None
        book_id, section_id, chapter_id = ch_match.group(1), ch_match.group(2), ch_match.group(3)

        # Both explicit "next page" AND "next chapter" (biquuge dual-purpose nav)
        trigger_texts = {'下一页', '下页', '下一章', '继续', 'next', '翻页'}

        for anchor in soup.select('a[href]'):
            text = anchor.get_text(strip=True)
            if text not in trigger_texts and text.lower() not in trigger_texts:
                continue

            href = (anchor.get('href') or '').strip()
            if not href:
                continue

            full_url = urljoin(current_url, href)
            if not self._is_biquuge_url(full_url):
                continue

            tp = urlparse(full_url)
            # Must match pattern: /book_id/section_id/chapter_id_PAGENUM.html
            m = re.match(
                r'^/(\d+)/(\d+)/(\d+)_(\d+)\.html$', tp.path or ''
            )
            if not m:
                continue

            # Must be the SAME chapter, only different page number
            if m.group(1) == book_id and m.group(2) == section_id and m.group(3) == chapter_id:
                # Return RAW url (with _N suffix) - critical for visited tracking
                return full_url

        return None

    def _crawl_chapters_parallel(self, chapter_catalog, timeout=8):
        ordered_results = [None] * len(chapter_catalog)
        failed = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {
                executor.submit(self._fetch_chapter_worker, c, i, timeout): (i, c)
                for i, c in enumerate(chapter_catalog, start=1)
            }
            for future in as_completed(future_map):
                if self.engine.is_stop_requested():
                    # Cancel remaining futures
                    for f in future_map:
                        f.cancel()
                    logger.info("[novel] Stop requested, aborting chapter downloads.")
                    break
                idx, payload, failed_chapter = future.result()
                if payload: ordered_results[idx-1] = payload
                elif failed_chapter: failed.append(failed_chapter)
        
        results = [r for r in ordered_results if r]
        self.engine._increment_stats(total_items=len(results))
        return results, failed

    def _validate_integrity(self, book_data):
        # Implementation of mixed roots detection...
        return True, {}
