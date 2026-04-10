#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Media Downloader — Post-processing pipeline for downloading
images, audio, and video files discovered in crawl results.

Workflow:
  1. Auto-detect which fields contain media URLs (by name hints + URL patterns)
  2. Download them concurrently into type-specific sub-folders (images/, audio/, video/)
  3. Return a summary dict for logging and dashboard display

Each media type has its own detect + download entry point, so callers can
invoke them selectively or use the unified `download_all_media()` helper.
"""

import os
import re
import logging
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Extension and field-name registries
# ─────────────────────────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.avif', '.ico'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma', '.opus'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m3u8', '.ts'}

IMAGE_FIELD_HINTS = {
    '预览图', '图片', '封面', '缩略图', '头像', '海报', 'image', 'img', 'photo',
    'thumbnail', 'cover', 'poster', 'avatar', 'preview', 'pic', 'src', '图标',
}
AUDIO_FIELD_HINTS = {
    '音乐', '音频', '歌曲', '播放', 'audio', 'music', 'song', 'mp3', 'sound',
    'track', '试听', '下载链接', 'download', 'src',
}
VIDEO_FIELD_HINTS = {
    '视频', '播放', 'video', 'mp4', 'stream', '直播', 'src', 'media',
}

# URL path patterns (fallback when field name alone is ambiguous)
IMAGE_PATH_PATTERNS = re.compile(r'/(image|img|photo|thumb|picture|preview|icon)', re.I)
AUDIO_PATH_PATTERNS = re.compile(r'/(audio|music|song|track|mp3|sound)', re.I)
VIDEO_PATH_PATTERNS = re.compile(r'/(video|stream|media|mp4|hls)', re.I)


# ─────────────────────────────────────────────────────────────────────────────
# URL classifiers
# ─────────────────────────────────────────────────────────────────────────────

def _url_media_type(value: str) -> str | None:
    """Return 'image', 'audio', 'video', or None."""
    if not isinstance(value, str) or not value.startswith('http'):
        return None
    path = urlparse(value).path.lower()
    ext = os.path.splitext(path)[-1]
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    if ext in AUDIO_EXTENSIONS:
        return 'audio'
    if ext in VIDEO_EXTENSIONS:
        return 'video'
    # Fallback: check path patterns
    if IMAGE_PATH_PATTERNS.search(path):
        return 'image'
    if AUDIO_PATH_PATTERNS.search(path):
        return 'audio'
    if VIDEO_PATH_PATTERNS.search(path):
        return 'video'
    return None


def _is_image_url(value: str) -> bool:
    return _url_media_type(value) == 'image'


def _is_audio_url(value: str) -> bool:
    return _url_media_type(value) == 'audio'


def _is_video_url(value: str) -> bool:
    return _url_media_type(value) == 'video'


# ─────────────────────────────────────────────────────────────────────────────
# Field detection
# ─────────────────────────────────────────────────────────────────────────────

def _detect_fields(records: list, hints: set, url_checker) -> list:
    """Generic field detector: find record keys whose values match url_checker."""
    if not records:
        return []
    sample = records[:5]
    found = []

    # First pass: check by field name hint
    for field in records[0].keys():
        key = field.lower().replace('_', '').replace('-', '')
        if any(h in key for h in hints):
            if any(url_checker(str(r.get(field, ''))) for r in sample):
                found.append(field)

    # Second pass: check remaining fields by URL content
    for field in records[0].keys():
        if field in found:
            continue
        if any(url_checker(str(r.get(field, ''))) for r in sample):
            found.append(field)

    return found


def detect_image_fields(records: list) -> list:
    """Return field names that contain image URLs."""
    return _detect_fields(records, IMAGE_FIELD_HINTS, _is_image_url)


def detect_audio_fields(records: list) -> list:
    """Return field names that contain audio URLs."""
    return _detect_fields(records, AUDIO_FIELD_HINTS, _is_audio_url)


def detect_video_fields(records: list) -> list:
    """Return field names that contain video URLs."""
    return _detect_fields(records, VIDEO_FIELD_HINTS, _is_video_url)


def detect_all_media_fields(records: list) -> dict:
    """
    Detect all media types in one pass.
    Returns {'image': [...], 'audio': [...], 'video': [...]}.
    """
    return {
        'image': detect_image_fields(records),
        'audio': detect_audio_fields(records),
        'video': detect_video_fields(records),
    }


# ─────────────────────────────────────────────────────────────────────────────
# File naming
# ─────────────────────────────────────────────────────────────────────────────

def _sanitize_fname(url: str, index: int, default_ext: str = '.jpg') -> str:
    """Derive a safe local filename from a URL."""
    path = urlparse(url).path
    base = os.path.basename(path) or f"file_{index}"
    # Keep only safe characters
    base = re.sub(r'[^A-Za-z0-9._\-\u4e00-\u9fff]+', '_', base)
    base = base.strip('._')
    # Ensure it has a media extension
    known = IMAGE_EXTENSIONS | AUDIO_EXTENSIONS | VIDEO_EXTENSIONS
    if not any(base.lower().endswith(ext) for ext in known):
        base += default_ext
    return f"{index:04d}_{base}"


# ─────────────────────────────────────────────────────────────────────────────
# Download engine
# ─────────────────────────────────────────────────────────────────────────────

def _download_one(session: requests.Session, url: str, dest: str, timeout: int = 30) -> bool:
    """Download a single media file. Returns True on success."""
    try:
        resp = session.get(url, timeout=timeout, stream=True)
        resp.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        logger.debug(f"Download failed {url}: {e}")
        return False


def _build_session(referer: str = '') -> requests.Session:
    """Create a configured requests session for media downloads."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'),
        'Referer': referer,
        'Accept': '*/*',
    })
    session.trust_env = False
    return session


def _download_media_batch(
    records: list,
    output_folder: str,
    media_fields: list,
    url_checker,
    default_ext: str = '.jpg',
    max_workers: int = 6,
    progress_callback=None,
) -> dict:
    """
    Core batch downloader used by all media-type helpers.

    Returns:
        {"folder": str, "total": int, "success": int, "failed": int, "fields": list}
    """
    if not media_fields:
        return {"folder": output_folder, "total": 0, "success": 0, "failed": 0, "fields": []}

    os.makedirs(output_folder, exist_ok=True)

    # Build flat task list
    tasks = []
    for record in records:
        for field in media_fields:
            url = str(record.get(field, '')).strip()
            if url_checker(url):
                fname = _sanitize_fname(url, len(tasks), default_ext)
                tasks.append((url, os.path.join(output_folder, fname)))

    if not tasks:
        return {"folder": output_folder, "total": 0, "success": 0, "failed": 0, "fields": media_fields}

    logger.info(f"[downloader] {len(tasks)} files → {output_folder}")
    session = _build_session()
    success = failed = done = 0
    total = len(tasks)
    lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_download_one, session, url, dest): (url, dest)
            for url, dest in tasks
        }
        for future in as_completed(future_map):
            ok = future.result()
            with lock:
                success += ok
                failed += (not ok)
                done += 1
            if progress_callback:
                progress_callback(done, total)

    logger.info(f"[downloader] Done: {success}/{total} succeeded, {failed} failed")
    return {
        "folder": output_folder,
        "total": total,
        "success": success,
        "failed": failed,
        "fields": media_fields,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public API: per-type downloaders
# ─────────────────────────────────────────────────────────────────────────────

def download_images(records, output_folder, image_fields=None,
                    max_workers=6, progress_callback=None):
    """Download all images from records into output_folder."""
    if image_fields is None:
        image_fields = detect_image_fields(records)
    return _download_media_batch(
        records, output_folder, image_fields, _is_image_url,
        default_ext='.jpg', max_workers=max_workers,
        progress_callback=progress_callback,
    )


def download_audio(records, output_folder, audio_fields=None,
                   max_workers=4, progress_callback=None):
    """Download all audio files from records into output_folder."""
    if audio_fields is None:
        audio_fields = detect_audio_fields(records)
    return _download_media_batch(
        records, output_folder, audio_fields, _is_audio_url,
        default_ext='.mp3', max_workers=max_workers,
        progress_callback=progress_callback,
    )


def download_video(records, output_folder, video_fields=None,
                   max_workers=3, progress_callback=None):
    """Download all video files from records into output_folder."""
    if video_fields is None:
        video_fields = detect_video_fields(records)
    return _download_media_batch(
        records, output_folder, video_fields, _is_video_url,
        default_ext='.mp4', max_workers=max_workers,
        progress_callback=progress_callback,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Unified entry point: detect + download all media types
# ─────────────────────────────────────────────────────────────────────────────

def download_all_media(
    records: list,
    base_folder: str,
    max_workers: int = 6,
    progress_callback=None,
) -> dict:
    """
    One-call convenience: detect ALL media types in records and download each
    into its own sub-folder under base_folder.

    Returns:
        {
            "image": {download result dict or None},
            "audio": {download result dict or None},
            "video": {download result dict or None},
        }
    """
    fields = detect_all_media_fields(records)
    results = {}

    for mtype, field_list, downloader, sub_dir in [
        ('image', fields['image'], download_images,  'images'),
        ('audio', fields['audio'], download_audio,   'audio'),
        ('video', fields['video'], download_video,   'video'),
    ]:
        if field_list:
            out = os.path.join(base_folder, sub_dir)
            results[mtype] = downloader(
                records, out,
                **{f"{mtype}_fields": field_list},
                max_workers=max_workers,
                progress_callback=progress_callback,
            )
        else:
            results[mtype] = None

    return results
