#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare GUI icons with a fast network-first strategy and local fallbacks."""

import logging
import os
import sys
from io import BytesIO

import requests
from PIL import Image, ImageDraw


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


ICON_SPECS = {
    "app": {"keywords": ["web", "browser"], "shape": "app"},
    "template": {"keywords": ["template", "layout"], "shape": "grid"},
    "url": {"keywords": ["link", "hyperlink"], "shape": "link"},
    "selector": {"keywords": ["filter", "cursor"], "shape": "cursor"},
    "start": {"keywords": ["play", "start"], "shape": "play"},
    "stop": {"keywords": ["stop", "pause"], "shape": "stop"},
    "folder": {"keywords": ["folder", "directory"], "shape": "folder"},
    "log": {"keywords": ["report", "document"], "shape": "log"},
    "preview": {"keywords": ["eye", "image"], "shape": "eye"},
    "advanced": {"keywords": ["shield", "security"], "shape": "shield"},
}


class GuiIconPreparer:
    def __init__(self, output_dir="assets/gui_icons", size=28, color="#7AE0FF"):
        self.output_dir = os.path.abspath(output_dir)
        self.raw_dir = os.path.join(self.output_dir, "raw")
        self.size = size
        self.color = color
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)

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

    def close(self):
        self.session.close()

    def prepare(self, icon_names=None):
        targets = icon_names or list(ICON_SPECS.keys())
        results = {}
        for name in targets:
            spec = ICON_SPECS.get(name)
            if not spec:
                logger.warning("unknown icon: %s", name)
                continue
            results[name] = self.prepare_one(name, spec)
        return results

    def prepare_one(self, icon_name, spec):
        final_path = os.path.join(self.output_dir, f"{icon_name}.png")
        if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
            logger.info("skip existing icon: %s", final_path)
            return {"type": "cached", "path": final_path}

        for keyword in spec["keywords"]:
            url = self._search_icons8_png(keyword)
            if not url:
                continue
            try:
                path = self._download_and_recolor(icon_name, url)
                if path:
                    logger.info("icons8 icon ready: %s <- %s", icon_name, keyword)
                    return {"type": "icons8", "path": path, "source_url": url}
            except Exception as exc:
                logger.info("icons8 download failed [%s]: %s", keyword, exc)

        fallback_path = self._draw_fallback(icon_name, spec["shape"])
        logger.info("fallback icon ready: %s", fallback_path)
        return {"type": "fallback", "path": fallback_path}

    def _search_icons8_png(self, keyword):
        response = self.session.get(
            "https://search.icons8.com/api/iconsets/v5/search",
            params={
                "term": keyword,
                "amount": 3,
                "offset": 0,
                "platform": "all",
            },
            timeout=10,
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

    def _download_and_recolor(self, icon_name, image_url):
        response = self.session.get(image_url, timeout=15)
        response.raise_for_status()

        raw_path = os.path.join(self.raw_dir, f"{icon_name}.png")
        with open(raw_path, "wb") as f:
            f.write(response.content)

        themed = self._recolor_icon(response.content)
        if themed is None:
            return ""

        final_path = os.path.join(self.output_dir, f"{icon_name}.png")
        themed.save(final_path, "PNG")
        return final_path

    def _recolor_icon(self, content):
        try:
            with Image.open(BytesIO(content)) as img:
                rgba = img.convert("RGBA")
        except Exception:
            return None

        alpha = rgba.getchannel("A")
        bbox = alpha.getbbox()
        if bbox is None:
            return None

        cropped = rgba.crop(bbox)
        cropped_alpha = cropped.getchannel("A")
        target = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))

        ratio = min((self.size - 4) / max(cropped.width, 1), (self.size - 4) / max(cropped.height, 1))
        resized_size = (
            max(1, int(cropped.width * ratio)),
            max(1, int(cropped.height * ratio)),
        )
        alpha_resized = cropped_alpha.resize(resized_size, Image.LANCZOS)

        layer = Image.new("RGBA", resized_size, self._hex_to_rgba(self.color))
        layer.putalpha(alpha_resized)
        offset = ((self.size - resized_size[0]) // 2, (self.size - resized_size[1]) // 2)
        target.alpha_composite(layer, offset)
        return target

    def _draw_fallback(self, icon_name, shape):
        img = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        color = self._hex_to_rgba(self.color)
        s = self.size

        if shape == "app":
            draw.rounded_rectangle((4, 5, s - 4, s - 5), radius=6, outline=color, width=2)
            draw.line((4, 10, s - 4, 10), fill=color, width=2)
            draw.ellipse((7, 7, 9, 9), fill=color)
            draw.ellipse((11, 7, 13, 9), fill=color)
        elif shape == "grid":
            for x in (6, 14):
                for y in (6, 14):
                    draw.rounded_rectangle((x, y, x + 8, y + 8), radius=2, outline=color, width=2)
        elif shape == "link":
            draw.arc((4, 8, 16, 20), start=300, end=120, fill=color, width=2)
            draw.arc((12, 8, 24, 20), start=120, end=300, fill=color, width=2)
            draw.line((10, 14, 18, 14), fill=color, width=2)
        elif shape == "cursor":
            draw.polygon(((7, 5), (20, 16), (13, 17), (17, 23), (14, 24), (10, 18), (7, 23)), fill=color)
        elif shape == "play":
            draw.polygon(((9, 6), (22, 14), (9, 22)), fill=color)
        elif shape == "stop":
            draw.rounded_rectangle((7, 7, 21, 21), radius=3, fill=color)
        elif shape == "folder":
            draw.rounded_rectangle((4, 9, s - 4, s - 6), radius=4, outline=color, width=2)
            draw.rounded_rectangle((6, 6, 15, 11), radius=3, fill=color)
        elif shape == "log":
            for y in (8, 13, 18):
                draw.rounded_rectangle((6, y, s - 6, y + 2), radius=1, fill=color)
            draw.ellipse((6, 6, 9, 9), fill=color)
        elif shape == "eye":
            draw.ellipse((4, 8, s - 4, 20), outline=color, width=2)
            draw.ellipse((11, 10, 17, 16), fill=color)
        elif shape == "shield":
            draw.polygon(((14, 4), (22, 7), (21, 16), (14, 23), (7, 16), (6, 7)), outline=color, fill=None, width=2)
            draw.line((14, 8, 14, 18), fill=color, width=2)
            draw.line((10, 12, 18, 12), fill=color, width=2)

        final_path = os.path.join(self.output_dir, f"{icon_name}.png")
        img.save(final_path, "PNG")
        return final_path

    def _hex_to_rgba(self, value):
        value = value.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def main():
    preparer = GuiIconPreparer()
    try:
        icon_names = sys.argv[1:] or None
        results = preparer.prepare(icon_names)
        success_count = sum(1 for item in results.values() if item)
        logger.info("gui icons ready: %s/%s", success_count, len(results))
    finally:
        preparer.close()


if __name__ == "__main__":
    main()
