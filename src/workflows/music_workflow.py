"""
Music Workflow — API-based music search & download pipeline.

Supports Solara-style music aggregators that expose a proxy API with
search, url-resolve, and download capabilities.

Architecture:
  1. Search API  → returns [{id, name, artist, album, source}, ...]
  2. URL API     → resolves song id → direct MP3 stream URL
  3. Download    → parallel download of MP3 files into audio/ subfolder
"""

import os
import json
import time
import random
import string
import logging
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus

from src.utils.file_storage import save_to_json, sanitize_filename

logger = logging.getLogger(__name__)


def _random_sig():
    """Generate a random signature token (matches Solara's client logic)."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=16))


class MusicWorkflow:
    """
    API-based music search & download workflow.

    Usage:
        mw = MusicWorkflow(api_base="https://yy.bttts.com/proxy",
                           source="netease", output_dir="data/crawled_data")
        results = mw.search("周杰伦")
        saved_dir = mw.download_all(results, keyword="周杰伦", progress_cb=...)
    """

    def __init__(self, api_base, source="netease", output_dir="data/crawled_data",
                 bitrate=320, max_workers=4, stop_check=None):
        self.api_base = api_base.rstrip("/")
        self.source = source
        self.output_dir = output_dir
        self.bitrate = bitrate
        self.max_workers = max_workers
        self._stop_check = stop_check  # callable → bool, cooperative stop
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://yy.bttts.com/",
        })

    # ── Public API ────────────────────────────────────────────────────────

    def search(self, keyword, count=30, page=1):
        """Search for songs. Returns list of dicts."""
        sig = _random_sig()
        url = (f"{self.api_base}?types=search"
               f"&source={self.source}"
               f"&name={quote_plus(keyword)}"
               f"&count={count}&pages={page}&s={sig}")

        logger.info(f"[music] search: {keyword} (source={self.source}, page={page})")
        try:
            resp = self._session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                logger.info(f"[music] found {len(data)} results")
                return data
            logger.warning(f"[music] unexpected response type: {type(data)}")
            return []
        except Exception as e:
            logger.error(f"[music] search failed: {e}")
            return []

    def resolve_url(self, song_id):
        """Resolve a song ID to a direct MP3 download URL."""
        sig = _random_sig()
        url = (f"{self.api_base}?types=url"
               f"&id={song_id}&source={self.source}"
               f"&br={self.bitrate}&s={sig}")
        try:
            resp = self._session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get("url", "")
        except Exception as e:
            logger.warning(f"[music] resolve_url({song_id}) failed: {e}")
            return ""

    def download_all(self, songs, keyword="music", progress_cb=None):
        """
        Download all songs into a unified result folder.

        Args:
            songs: list of search result dicts
            keyword: search keyword (used for folder/file naming)
            progress_cb: optional callback(msg, done, total)

        Returns:
            path to the result folder, or None on failure
        """
        if not songs:
            return None

        # Create unified result folder:  {keyword}_{timestamp}/
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_kw = sanitize_filename(keyword) or "music"
        folder_name = f"{safe_kw}_{ts}"
        result_dir = os.path.join(self.output_dir, folder_name)
        audio_dir = os.path.join(result_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        # Save JSON metadata
        save_to_json(songs, result_dir, safe_kw)

        total = len(songs)
        done = [0]
        failed = []

        def _download_one(idx, song):
            if self._stop_check and self._stop_check():
                return False

            song_id = song.get("id", "")
            name = song.get("name", f"track_{idx}")
            artists = song.get("artist", [])
            artist_str = ", ".join(artists) if isinstance(artists, list) else str(artists)

            # Resolve direct URL
            mp3_url = self.resolve_url(song_id)
            if not mp3_url:
                logger.warning(f"[music] skip #{idx}: no URL for '{name}'")
                failed.append(name)
                return False

            # Build filename: 001_歌名 - 歌手.mp3
            safe_name = sanitize_filename(f"{name} - {artist_str}") or f"track_{idx}"
            filename = f"{idx:03d}_{safe_name}.mp3"
            filepath = os.path.join(audio_dir, filename)

            try:
                resp = self._session.get(mp3_url, timeout=60, stream=True)
                resp.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if self._stop_check and self._stop_check():
                            return False
                        f.write(chunk)

                done[0] += 1
                if progress_cb:
                    progress_cb(f"⬇️ [{done[0]}/{total}] {name} - {artist_str}", done[0], total)
                return True
            except Exception as e:
                logger.warning(f"[music] download failed #{idx} '{name}': {e}")
                failed.append(name)
                return False

        # Parallel downloads
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(_download_one, i + 1, s): s
                for i, s in enumerate(songs)
            }
            for f in as_completed(futures):
                if self._stop_check and self._stop_check():
                    for remaining in futures:
                        remaining.cancel()
                    break

        logger.info(f"[music] download complete: {done[0]}/{total} succeeded, "
                    f"{len(failed)} failed")

        if failed:
            logger.info(f"[music] failed tracks: {failed}")

        return result_dir if done[0] > 0 else None
