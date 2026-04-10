#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch and prepare themed GUI icons using the crawler pipeline."""

import logging
import os
import sys
from io import BytesIO

import requests
from PIL import Image

try:
    from universal_crawler_v2 import UniversalCrawlerV2
except ImportError:  # pragma: no cover
    from .universal_crawler_v2 import UniversalCrawlerV2


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


ICON_REQUESTS = {
    "app": ["web", "browser"],
    "template": ["template", "layout"],
    "url": ["link", "hyperlink"],
    "selector": ["filter", "cursor"],
    "start": ["play", "start"],
    "stop": ["stop", "pause"],
    "folder": ["folder", "directory"],
    "log": ["report", "document"],
    "preview": ["image", "eye"],
    "advanced": ["shield", "security"],
}

ITEM_SELECTORS = {
    "icon_image": "img.icon--item__img@src || img@src || img@data-src",
    "icon_title": ".icon--item__title || img@alt || @title",
    "icon_link": "a.icon--item__link@href || a@href || @href",
}

LIST_SELECTOR = '.icon--item || li:has(a[href*="/free-icon/"]) || a[href*="/free-icon/"]'


class GuiIconFetcher:
    def __init__(self, output_dir="assets/gui_icons", theme_color="#7ae0ff", size=28):
        self.output_dir = os.path.abspath(output_dir)
        self.raw_dir = os.path.join(self.output_dir, "raw")
        self.profile_dir = os.path.abspath(os.path.join("data", "gui_icon_browser_profile"))
        self.theme_color = theme_color
        self.size = size
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.profile_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )
        self.flaticon_crawler = None

    def close(self):
        if self.flaticon_crawler:
            self.flaticon_crawler.close()
            self.flaticon_crawler = None
        self.session.close()

    def fetch_all(self):
        return {icon_name: self.fetch_one(icon_name, keywords) for icon_name, keywords in ICON_REQUESTS.items()}

    def fetch_selection(self, icon_names):
        results = {}
        for icon_name in icon_names:
            keywords = ICON_REQUESTS.get(icon_name)
            if not keywords:
                logger.warning("unknown icon name: %s", icon_name)
                results[icon_name] = None
                continue
            results[icon_name] = self.fetch_one(icon_name, keywords)
        return results

    def fetch_one(self, icon_name, keywords):
        logger.info("fetch icon: %s", icon_name)
        final_path = os.path.join(self.output_dir, f"{icon_name}.png")
        if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
            logger.info("  skip existing: %s", final_path)
            return {
                "keyword": "cached",
                "path": final_path,
                "image_url": "",
            }

        for keyword in keywords:
            image_url = self._search_icons8_png(keyword)
            if not image_url:
                continue

            final_path = self._download_and_prepare_with_session(self.session, image_url, icon_name)
            if final_path:
                logger.info("  icons8 success: %s -> %s", keyword, final_path)
                return {
                    "keyword": keyword,
                    "path": final_path,
                    "image_url": image_url,
                }

        logger.info("  icons8 miss, fallback to flaticon")
        for keyword in keywords:
            image_url = self._search_flaticon_png(keyword)
            if not image_url:
                continue

            final_path = self._download_and_prepare_with_session(
                self._get_flaticon_crawler().session,
                image_url,
                icon_name,
            )
            if final_path:
                logger.info("  flaticon success: %s -> %s", keyword, final_path)
                return {
                    "keyword": keyword,
                    "path": final_path,
                    "image_url": image_url,
                }

        logger.warning("icon fetch failed: %s", icon_name)
        return None

        for keyword in keywords:
            url = f"https://www.flaticon.com/free-icons/{keyword}"
            logger.info("  try keyword: %s", keyword)
            results = crawler.crawl_list_page(
                url,
                LIST_SELECTOR,
                ITEM_SELECTORS,
                max_items=2,
            )
            if not results:
                continue

            image_url = self._pick_best_image_url(results)
            if not image_url:
                continue

            final_path = self._download_and_prepare(crawler, image_url, icon_name)
            if final_path:
                logger.info("  success: %s -> %s", keyword, final_path)
                return {
                    "keyword": keyword,
                    "path": final_path,
                    "image_url": image_url,
                }

        logger.warning("icon fetch failed: %s", icon_name)
        return None

    def _pick_best_image_url(self, results):
        for row in results:
            url = (row.get("icon_image") or row.get("图标图片") or "").strip()
            if url:
                return url
        return ""

    def _download_and_prepare(self, crawler, image_url, icon_name):
        headers = {"Referer": "https://www.flaticon.com/"}
        response = crawler.session.get(image_url, timeout=20, headers=headers)
        response.raise_for_status()

        raw_path = os.path.join(self.raw_dir, f"{icon_name}.png")
        with open(raw_path, "wb") as f:
            f.write(response.content)

        themed = self._create_themed_icon(response.content)
        if themed is None:
            return None

        final_path = os.path.join(self.output_dir, f"{icon_name}.png")
        themed.save(final_path, "PNG")
        return final_path

    def _search_icons8_png(self, keyword):
        try:
            response = self.session.get(
                "https://search.icons8.com/api/iconsets/v5/search",
                params={
                    "term": keyword,
                    "amount": 3,
                    "offset": 0,
                    "platform": "all",
                },
                timeout=12,
            )
            response.raise_for_status()
            data = response.json()
            icons = data.get("icons") or []
            if not icons:
                return ""

            icon_id = icons[0].get("id")
            platform = icons[0].get("platform", "color")
            if not icon_id:
                return ""
            return f"https://img.icons8.com/{platform}/96/000000/{icon_id}.png"
        except Exception as exc:
            logger.info("  icons8 search failed [%s]: %s", keyword, exc)
            return ""

    def _get_flaticon_crawler(self):
        if self.flaticon_crawler is None:
            self.flaticon_crawler = UniversalCrawlerV2(
                base_url="https://www.flaticon.com/free-icons/web",
                output_dir=self.raw_dir,
                use_advanced_mode=False,
                requests_per_second=1.5,
                max_retries=0,
                advanced_user_data_dir=self.profile_dir,
            )
        return self.flaticon_crawler

    def _search_flaticon_png(self, keyword):
        crawler = self._get_flaticon_crawler()
        url = f"https://www.flaticon.com/free-icons/{keyword}"
        logger.info("  flaticon try: %s", keyword)
        results = crawler.crawl_list_page(
            url,
            LIST_SELECTOR,
            ITEM_SELECTORS,
            max_items=2,
        )
        for row in results:
            image_url = (row.get("icon_image") or row.get("图标图片") or "").strip()
            if image_url:
                return image_url
        return ""

    def _download_and_prepare_with_session(self, session, image_url, icon_name):
        headers = {}
        if "flaticon.com" in image_url or "cdn-icons-png.flaticon.com" in image_url:
            headers["Referer"] = "https://www.flaticon.com/"
        response = session.get(image_url, timeout=20, headers=headers or None)
        response.raise_for_status()

        raw_path = os.path.join(self.raw_dir, f"{icon_name}.png")
        with open(raw_path, "wb") as f:
            f.write(response.content)

        themed = self._create_themed_icon(response.content)
        if themed is None:
            return None

        final_path = os.path.join(self.output_dir, f"{icon_name}.png")
        themed.save(final_path, "PNG")
        return final_path

    def _create_themed_icon(self, content):
        try:
            with Image.open(BytesIO(content)) as img:
                rgba = img.convert("RGBA")
        except Exception as exc:
            logger.warning("prepare icon failed: %s", exc)
            return None

        alpha = rgba.getchannel("A")
        if alpha.getbbox() is None:
            return None

        bbox = alpha.getbbox()
        cropped = rgba.crop(bbox)
        cropped_alpha = cropped.getchannel("A")

        target = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        aspect = min((self.size - 4) / max(cropped.width, 1), (self.size - 4) / max(cropped.height, 1))
        resized_size = (
            max(1, int(cropped.width * aspect)),
            max(1, int(cropped.height * aspect)),
        )
        resized_alpha = cropped_alpha.resize(resized_size, Image.LANCZOS)

        color = self._hex_to_rgba(self.theme_color)
        icon_layer = Image.new("RGBA", resized_size, color)
        icon_layer.putalpha(resized_alpha)

        offset = ((self.size - resized_size[0]) // 2, (self.size - resized_size[1]) // 2)
        target.alpha_composite(icon_layer, offset)
        return target

    def _hex_to_rgba(self, value):
        value = value.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def main():
    fetcher = GuiIconFetcher()
    try:
        icon_names = sys.argv[1:]
        if icon_names:
            results = fetcher.fetch_selection(icon_names)
        else:
            results = fetcher.fetch_all()
        success_count = sum(1 for item in results.values() if item)
        logger.info("gui icon fetch complete: %s/%s", success_count, len(results))
    finally:
        fetcher.close()


if __name__ == "__main__":
    main()
