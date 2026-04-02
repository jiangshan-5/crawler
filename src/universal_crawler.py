#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backward-compatible entrypoint that delegates to UniversalCrawlerV2."""

try:
    from .universal_crawler_v2 import UniversalCrawlerV2
except ImportError:
    from universal_crawler_v2 import UniversalCrawlerV2


class UniversalCrawler(UniversalCrawlerV2):
    """Compatibility alias for legacy imports.

    Existing callers can keep `from universal_crawler import UniversalCrawler`
    while the implementation is centralized in UniversalCrawlerV2.
    """

    def __init__(self, base_url, output_dir='data/crawled_data', use_advanced_mode=False):
        super().__init__(
            base_url=base_url,
            output_dir=output_dir,
            use_advanced_mode=use_advanced_mode,
            requests_per_second=1,
            max_retries=3,
            enable_cache=False
        )


def main():
    """Keep a small runnable demo for manual checks."""
    crawler = UniversalCrawler(base_url='https://example.com', output_dir='data/example')
    print('UniversalCrawler now delegates to UniversalCrawlerV2.')
    print('Use crawler.crawl_single_page(...) / crawler.crawl_list_page(...).')
    crawler.close()


if __name__ == '__main__':
    main()
