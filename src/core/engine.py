import os
import logging
import threading
from urllib.parse import urljoin

# Standard engineering imports (internal packages)
from src.core.base_crawler import BaseCrawler
from src.core.advanced_crawler import AdvancedCrawler, is_advanced_mode_available
from src.core.config import RetryConfig, DEFAULT_OUTPUT_DIR
from src.utils.file_storage import save_to_json, save_to_csv, sanitize_filename
from src.workflows.novel_workflow import NovelWorkflow
from src.config.site_rules import get_site_rule, get_recommended_wait
import src.utils.heuristics as heuristics

logger = logging.getLogger(__name__)

class UniversalEngine(BaseCrawler):
    """
    The main coordinator engine. 
    Inherits core networking from BaseCrawler and delegates 
    specialized tasks to workflows/modules.
    """
    def __init__(
        self,
        base_url,
        output_dir=DEFAULT_OUTPUT_DIR,
        use_advanced_mode=False,
        requests_per_second=1,
        max_retries=3,
        advanced_user_data_dir=None,
        is_flaticon_task=False,
        wait_time=3
    ):
        super().__init__(requests_per_second, max_retries)
        self.base_url = base_url
        self.output_dir = output_dir
        self.use_advanced_mode = use_advanced_mode
        self.advanced_user_data_dir = advanced_user_data_dir
        self.is_flaticon_task = is_flaticon_task
        self.wait_time = wait_time
        
        self.advanced_crawler = None
        self.last_error_reason = ''
        self._stop_event = threading.Event()   # cooperative stop flag
        
        # Initialize novel workflow module
        self.novel_workflow = NovelWorkflow(self)
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup advanced mode if requested
        if self.use_advanced_mode:
            self.rules = get_site_rule(self.base_url)
            if not is_advanced_mode_available():
                logger.warning('advanced mode requested but not available, fallback to standard')
                self.use_advanced_mode = False
            else:
                is_headed = self.rules.get("force_headed", False)
                # Use rule-based wait time if not manually overridden or default
                final_wait = self.wait_time if self.wait_time != 3 else get_recommended_wait(self.base_url, self.rules)
                
                self.advanced_crawler = AdvancedCrawler(
                    headless=not is_headed,
                    user_data_dir=self.advanced_user_data_dir,
                    wait_time=final_wait
                )

    def crawl_list_page(self, url, list_selector, item_selectors, max_items=None):
        """Standard list extraction with optional advanced mode support and heuristic fallback."""
        self._increment_stats(total_pages=1)
        rules = get_site_rule(url)
        
        if self.use_advanced_mode and self.advanced_crawler:
            soup = self.advanced_crawler.fetch_page(url)
            if not soup: return []
            items = self._select_items_with_fallback(soup, list_selector)
            
            # Smart Refresh logic for blank pages
            if not items:
                logger.info("[engine] list empty in advanced mode, trying smart refresh...")
                soup = self.advanced_crawler.fetch_page(url, force_refresh=True)
                if soup: items = self._select_items_with_fallback(soup, list_selector)
        else:
            soup = self.fetch_page(url)
            if not soup: return []
            items = self._select_items_with_fallback(soup, list_selector)
        
        results = []
        if items:
            results = self._extract_field_data(soup, items, item_selectors, url)
        
        # Heuristic Fallback if items are still empty and rule exists
        if not results and rules.get("heuristic_fallback"):
            fallback_name = rules["heuristic_fallback"]
            handler = getattr(heuristics, f"{fallback_name}_heuristic", None)
            if handler:
                logger.info(f"[engine] primary selectors failed, triggering heuristic fallback: {fallback_name}")
                results = handler(soup, item_selectors)

        if max_items and len(results) > max_items:
            results = results[:max_items]
        
        self._increment_stats(total_items=len(results), success_pages=1 if results else 0)
        return results

    def _extract_field_data(self, soup, items, item_selectors, base_url):
        """Extract all defined fields for each successfully found item."""
        rows = []
        for item in items:
            row = {}
            for field, selector in item_selectors.items():
                val = self._extract_single_field(item, selector)
                if val is not None:
                    # Normalize links
                    if field.lower() in ['url', 'link', 'href'] or self.validator.validate_url(val):
                        if not val.startswith('http'):
                            val = urljoin(base_url, val)
                    row[field] = self.validator.clean_text(str(val))
            if row: rows.append(row)
        return rows

    def _select_items_with_fallback(self, soup, list_selector):
        """Support multi-candidate list selectors separated by ||."""
        candidates = [s.strip() for s in list_selector.split('||') if s.strip()]
        for candidate in candidates:
            try:
                items = soup.select(candidate)
                if items: return items
            except Exception as e:
                logger.warning(f"Invalid list selector {candidate}: {e}")
        return []

    def _extract_single_field(self, element, selector):
        """Implementation of the robust || and @ selector logic."""
        candidates = [s.strip() for s in selector.split('||') if s.strip()]
        for candidate in candidates:
            try:
                if '@' in candidate:
                    css_selector, attribute = candidate.split('@', 1)
                    css_selector = css_selector.strip()
                    attribute = attribute.strip()
                    target = element.select_one(css_selector) if css_selector else element
                    if target:
                        val = target.get(attribute)
                        if val: return val
                else:
                    target = element.select_one(candidate)
                    if target:
                        val = target.get_text(strip=True)
                        if val: return val
            except Exception as e:
                logger.warning(f"Field extraction error for {candidate}: {e}")
        return None

    def save_results(self, data, filename=None, preferred_format='json',
                     override_dir=None, override_name=None):
        """Universal saving entry point.

        Args:
            override_dir:  If given, save into this directory instead of self.output_dir.
            override_name: If given, use this as the filename stem (no extension).
        """
        if not data: return None
        out_dir = override_dir or self.output_dir
        fname   = override_name or filename
        if preferred_format == 'csv':
            return save_to_csv(data, out_dir, fname)
        return save_to_json(data, out_dir, fname)

    def crawl_novel(self, keyword_or_url, progress_callback=None):
        """
        Full novel download pipeline:
          1. Search / validate book URL
          2. Resolve chapter catalog from directory
          3. Fetch all chapters in parallel
          4. Save as structured JSON

        Args:
            keyword_or_url:    Book title (searches biquuge) or direct book URL.
            progress_callback: Optional fn(stage: str, done: int, total: int)

        Returns:
            saved JSON file path, or None on failure.
        """
        nw = self.novel_workflow

        def _notify(stage, done=0, total=0):
            if progress_callback:
                progress_callback(stage, done, total)
            logger.info(f"[novel] {stage} ({done}/{total})")

        # ── Step 1: resolve book URL ──────────────────────────────────────
        _notify("正在搜索书籍...")
        if nw._is_biquuge_url(keyword_or_url):
            book_info = {'book_url': nw._normalize_biquuge_book_url(keyword_or_url),
                         'title': ''}
        else:
            book_info = nw.search_book(keyword_or_url)

        if not book_info or not book_info.get('book_url'):
            _notify("❌ 未找到匹配书籍，请检查书名或链接")
            return None

        book_url = book_info['book_url']
        book_title = book_info.get('title', keyword_or_url)
        _notify(f"✅ 找到书籍: {book_title or book_url}")

        # ── Step 2: resolve directory / chapter catalog ──────────────────
        _notify("正在解析目录...")
        catalog_result = nw._resolve_biquuge_directory_catalog(book_url)
        chapters = catalog_result.get('chapter_catalog', [])

        if not chapters:
            _notify("❌ 目录解析失败，未找到任何章节")
            return None

        _notify(f"✅ 目录解析完成，共 {len(chapters)} 章", len(chapters), len(chapters))

        # ── Step 3: parallel chapter fetch ───────────────────────────────
        def _dl_progress(done, total):
            _notify(f"正在下载章节 {done}/{total}...", done, total)

        # Patch nw so it calls our progress hook
        results, failed = nw._crawl_chapters_parallel(
            chapters,
            timeout=8
        )
        _notify(f"✅ 下载完成: {len(results)} 章成功, {len(failed)} 章失败",
                len(results), len(chapters))

        if not results:
            _notify("❌ 章节内容全部下载失败")
            return None

        # ── Step 4: export as TXT (legacy-compatible format) ─────────────
        # Use the original search keyword as the file/folder name (user expectation)
        safe_title = sanitize_filename(keyword_or_url)
        if not safe_title or safe_title == 'unnamed':
            safe_title = sanitize_filename(book_title or 'novel')
        from datetime import datetime
        fname_base = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create a dedicated sub-folder for this novel (like image downloads)
        novel_dir = os.path.join(self.output_dir, fname_base)
        os.makedirs(novel_dir, exist_ok=True)

        book_info_str = catalog_result.get('info', '')
        synopsis = catalog_result.get('synopsis', '')

        # Sort results back to chapter order
        order_map = {c.get('chapter_url', ''): i for i, c in enumerate(chapters)}
        sorted_results = sorted(
            results,
            key=lambda r: order_map.get(r.get('chapter_url', ''), 9999)
        )

        # --- TXT (primary output: what users actually want) ---
        txt_path = os.path.join(novel_dir, f"{safe_title}.txt")
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                # ── Header block ────────────────────────────────────────────
                f.write(f"书名：{book_title}\n")
                f.write(f"来源：{book_url}\n")
                f.write(f"目录页：{book_url}\n")
                f.write(f"章节数：{len(chapters)}\n")
                if book_info_str:
                    f.write(f"信息：{book_info_str}\n")
                f.write("\n")

                # ── Synopsis ────────────────────────────────────────────────
                if synopsis:
                    f.write("简介：\n")
                    f.write(f"简介：{synopsis}\n")
                    f.write("\n")

                # ── Chapter separator ───────────────────────────────────────
                f.write("=" * 40 + "\n\n")

                # ── Chapters ────────────────────────────────────────────────
                for num, ch in enumerate(sorted_results, start=1):
                    ch_title = ch.get('chapter_title', ch.get('title', ''))
                    pages = ch.get('pages', None)
                    content = ch.get('content', '')

                    # Build page list: either stored pages or split by content
                    if pages and isinstance(pages, list) and len(pages) > 1:
                        page_list = pages
                    else:
                        page_list = [content] if content else []

                    total_pages = len(page_list)

                    # Chapter heading: 0001. 章名-《书名》
                    heading = f"{num:04d}. {ch_title}"
                    if book_title and f"《{book_title}》" not in heading:
                        heading += f"-《{book_title}》"
                    f.write(heading + "\n")

                    for p_idx, page_text in enumerate(page_list, start=1):
                        f.write(f"第({p_idx}/{total_pages})页\n")
                        paragraphs = [ln.strip() for ln in page_text.split('\n') if ln.strip()]
                        f.write('\n'.join(paragraphs))
                        f.write('\n')
                        f.write(f"第({p_idx}/{total_pages})页\n")

                    f.write("\n")  # blank line between chapters

            _notify(f"📄 TXT 已保存: {txt_path}")
        except Exception as e:
            logger.error(f"TXT export failed: {e}")
            txt_path = None

        # --- JSON (secondary: structured backup in same folder) ---
        book_data = {
            'title': book_title,
            'book_url': book_url,
            'total_chapters': len(chapters),
            'downloaded_chapters': len(results),
            'failed_count': len(failed),
            'chapters': results
        }
        save_to_json([book_data], novel_dir, safe_title + "_raw")

        _notify(f"✅ 完成！保存目录: {novel_dir}")
        return novel_dir  # Return folder path so dashboard picks it up

    def close(self):
        """Cleanup resources."""
        if self.advanced_crawler:
            self.advanced_crawler.close()
        self._closed = True

    def request_stop(self):
        """Signal cooperative stop — running workers should check is_stop_requested()."""
        self._stop_event.set()
        self._stop_requested = True   # also set the base class flag
        logger.info("[engine] Stop requested by user.")

    def is_stop_requested(self):
        return self._stop_event.is_set()
