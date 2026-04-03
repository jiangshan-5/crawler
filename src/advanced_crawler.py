#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import atexit
import logging
import os
import re
import shutil
import socket
import subprocess
import time
import urllib.request
from functools import lru_cache

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)
UC_START_TIMEOUT_SECONDS = 45
UC_PREFLIGHT_TIMEOUT_SECONDS = 1.5


def _check_uc_availability():
    try:
        import undetected_chromedriver as uc  # noqa: F401
        return True
    except ImportError as e:
        logger.warning(f"undetected-chromedriver is not installed: {e}")
        return False


def _detect_local_edge_executable():
    paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for exe in paths:
        if os.path.exists(exe):
            return exe
    return ""


UC_AVAILABLE = _check_uc_availability()
EDGE_BROWSER_AVAILABLE = bool(_detect_local_edge_executable())
EDGE_DRIVER_AVAILABLE = False
ADVANCED_MODE_AVAILABLE = UC_AVAILABLE


def _extract_major_from_version_text(text):
    if not text:
        return None
    m = re.search(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", text)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


@lru_cache(maxsize=1)
def _detect_local_chrome_major_version():
    """Try to detect local Chrome major version on Windows."""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon") as key:
            version, _ = winreg.QueryValueEx(key, "version")
            major = _extract_major_from_version_text(version)
            if major:
                return major
    except Exception:
        pass

    paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for exe in paths:
        if not os.path.exists(exe):
            continue
        try:
            proc = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=3)
            text = (proc.stdout or "") + " " + (proc.stderr or "")
            major = _extract_major_from_version_text(text)
            if major:
                return major
        except Exception:
            continue

    return None


@lru_cache(maxsize=1)
def _detect_local_edge_major_version():
    """Try to detect local Edge major version on Windows."""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Edge\BLBeacon") as key:
            version, _ = winreg.QueryValueEx(key, "version")
            major = _extract_major_from_version_text(version)
            if major:
                return major
    except Exception:
        pass

    exe = _detect_local_edge_executable()
    if exe and os.path.exists(exe):
        try:
            proc = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=3)
            text = (proc.stdout or "") + " " + (proc.stderr or "")
            major = _extract_major_from_version_text(text)
            if major:
                return major
        except Exception:
            pass

    return None


@lru_cache(maxsize=1)
def _get_cached_uc_driver_path():
    candidates = [
        os.path.expandvars(r"%APPDATA%\undetected_chromedriver\undetected_chromedriver.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\undetected_chromedriver\undetected_chromedriver.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return ""


@lru_cache(maxsize=1)
def _get_local_edge_driver_path():
    which_path = shutil.which("msedgedriver")
    if which_path and os.path.exists(which_path):
        return which_path

    edge_exe = _detect_local_edge_executable()
    candidates = []
    if edge_exe:
        candidates.append(os.path.join(os.path.dirname(edge_exe), "msedgedriver.exe"))

    candidates.extend(
        [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedgedriver.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedgedriver.exe"),
            os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedgedriver.exe"),
        ]
    )

    for path in candidates:
        if os.path.exists(path):
            return path
    return ""


EDGE_DRIVER_AVAILABLE = bool(_get_local_edge_driver_path())
ADVANCED_MODE_AVAILABLE = UC_AVAILABLE or EDGE_DRIVER_AVAILABLE


def _extract_browser_major_from_exception(exc):
    text = str(exc or "")
    m = re.search(r"Current browser version is (\d+)\.", text)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


def _can_reach(url, timeout=5):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return bool(getattr(resp, "status", 200) < 500)
    except Exception:
        return False


def _is_flaticon_access_denied(html):
    text = (html or "").lower()
    return "access denied" in text and "support@freepik.com" in text


def _flaticon_link_count(driver):
    try:
        count = driver.execute_script(
            "return document.querySelectorAll('a[href*=\"/free-icon/\"]').length;"
        )
        return int(count or 0)
    except Exception:
        return 0


def _is_driver_alive(driver):
    if driver is None:
        return False
    try:
        driver.window_handles
        return True
    except Exception:
        return False


def _build_profile_dir(user_data_dir, headless):
    base_dir = os.path.abspath(
        user_data_dir or os.path.join(os.getcwd(), "data", "browser_profile")
    )
    leaf = os.path.basename(base_dir).lower()
    if leaf in {"headed", "headless"}:
        return base_dir
    return os.path.join(base_dir, "headless" if headless else "headed")


class AdvancedCrawler:
    _shared_pool = {}
    _atexit_registered = False

    def __init__(self, headless=True, user_data_dir=None, reuse_browser=True):
        self.driver = None
        self.headless = headless
        self.reuse_browser = reuse_browser
        self.engine_name = "auto"
        self.user_data_dir = _build_profile_dir(user_data_dir, headless)
        self._shared_key = (bool(self.headless), os.path.abspath(self.user_data_dir))
        self._pool_attached = False

        if not ADVANCED_MODE_AVAILABLE:
            raise ImportError(
                "advanced mode requires a local Edge browser or undetected-chromedriver\n"
                "run: pip install undetected-chromedriver"
            )

        self._ensure_shutdown_hook()

    @classmethod
    def _ensure_shutdown_hook(cls):
        if cls._atexit_registered:
            return
        atexit.register(cls.shutdown_all)
        cls._atexit_registered = True

    @classmethod
    def shutdown_all(cls):
        for key, entry in list(cls._shared_pool.items()):
            driver = entry.get("driver")
            try:
                if _is_driver_alive(driver):
                    driver.quit()
                    logger.info(f"[advanced] warm browser pool closed: {key}")
            except Exception as e:
                logger.warning(f"[advanced] warm browser pool close failed {key}: {e}")
        cls._shared_pool.clear()

    def _try_attach_shared_driver(self):
        if not self.reuse_browser:
            return False

        entry = self.__class__._shared_pool.get(self._shared_key)
        if not entry:
            return False

        driver = entry.get("driver")
        if not _is_driver_alive(driver):
            self.__class__._shared_pool.pop(self._shared_key, None)
            logger.info("[advanced] stale warm browser discarded")
            return False

        if entry.get("clients", 0) > 0:
            logger.info("[advanced] warm browser exists but is busy; create a fresh instance")
            return False

        entry["clients"] = 1
        entry["last_used"] = time.time()
        self.driver = driver
        self._pool_attached = True
        logger.info("[advanced] reusing warm browser instance")
        return True

    def _store_shared_driver(self):
        if not self.reuse_browser or not _is_driver_alive(self.driver):
            return

        entry = self.__class__._shared_pool.get(self._shared_key)
        if entry and entry.get("clients", 0) > 0 and entry.get("driver") is not self.driver:
            logger.info("[advanced] shared pool busy; keep current browser private")
            self._pool_attached = False
            return

        self.__class__._shared_pool[self._shared_key] = {
            "driver": self.driver,
            "clients": 1,
            "last_used": time.time(),
        }
        self._pool_attached = True

    def _release_shared_driver(self):
        if not self.reuse_browser or not self._pool_attached or self.driver is None:
            return False

        entry = self.__class__._shared_pool.get(self._shared_key)
        if not entry or entry.get("driver") is not self.driver:
            self._pool_attached = False
            return False

        if not _is_driver_alive(self.driver):
            self.__class__._shared_pool.pop(self._shared_key, None)
            self.driver = None
            self._pool_attached = False
            logger.info("[advanced] warm browser died before release; removed from pool")
            return True

        entry["clients"] = max(0, entry.get("clients", 1) - 1)
        entry["last_used"] = time.time()
        self.driver = None
        self._pool_attached = False
        logger.info("[advanced] browser released to warm pool")
        return True

    def _build_common_browser_args(self):
        args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-default-browser-check",
            "--no-first-run",
            "--start-maximized",
            "--window-size=1440,2200",
            "--lang=en-US",
            "--disable-features=IsolateOrigins,site-per-process",
        ]
        if self.headless:
            args.insert(0, "--headless=new")
        return args

    def _start_edge(self):
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.edge.service import Service as EdgeService

        edge_executable = _detect_local_edge_executable()
        if not edge_executable:
            raise RuntimeError("local Edge browser not detected")

        options = EdgeOptions()
        options.use_chromium = True
        options.page_load_strategy = "eager"
        options.binary_location = edge_executable
        os.makedirs(self.user_data_dir, exist_ok=True)
        for arg in self._build_common_browser_args():
            options.add_argument(arg)
        options.add_argument(f"--user-data-dir={self.user_data_dir}")

        edge_driver = _get_local_edge_driver_path()
        if edge_driver:
            logger.info(f"[advanced] local EdgeDriver found -> {edge_driver}")
            service = EdgeService(executable_path=edge_driver)
        else:
            raise RuntimeError(
                "local EdgeDriver not found; skip Selenium Manager slow path"
            )

        logger.info(
            f"[advanced] edge options ready, headless={self.headless}, page_load_strategy=eager"
        )
        local_major = _detect_local_edge_major_version()
        if local_major:
            logger.info(f"[advanced] detected local Edge major={local_major}")

        old_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(UC_START_TIMEOUT_SECONDS)
            self.driver = webdriver.Edge(service=service, options=options)
        finally:
            socket.setdefaulttimeout(old_timeout)

        self.engine_name = "edge"

    def _start_uc_chrome(self):
        import undetected_chromedriver as uc

        options = uc.ChromeOptions()
        options.page_load_strategy = "eager"
        os.makedirs(self.user_data_dir, exist_ok=True)
        for arg in self._build_common_browser_args():
            options.add_argument(arg)
        options.add_argument(f"--user-data-dir={self.user_data_dir}")

        logger.info(
            f"[advanced] chrome options ready, headless={self.headless}, page_load_strategy=eager"
        )
        logger.info("[advanced] creating Chrome instance (first run may download driver)")

        cached_driver = _get_cached_uc_driver_path()
        if cached_driver:
            logger.info(f"[advanced] cached driver found -> {cached_driver}; skip download preflight")
        else:
            logger.info("[advanced] no cached driver found; quick download preflight")
            reach_google = _can_reach(
                "https://googlechromelabs.github.io/",
                timeout=UC_PREFLIGHT_TIMEOUT_SECONDS,
            )
            reach_github = False
            if not reach_google:
                reach_github = _can_reach(
                    "https://github.com/",
                    timeout=UC_PREFLIGHT_TIMEOUT_SECONDS,
                )
            if not (reach_google or reach_github):
                raise RuntimeError(
                    "advanced mode cannot download/check ChromeDriver: "
                    "network to googlechromelabs/github is unreachable"
                )

        local_major = _detect_local_chrome_major_version()
        if local_major:
            logger.info(f"[advanced] detected local Chrome major={local_major}")

        kwargs = {"options": options, "use_subprocess": False}
        if local_major:
            kwargs["version_main"] = local_major

        old_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(UC_START_TIMEOUT_SECONDS)
            try:
                self.driver = uc.Chrome(**kwargs)
            except Exception as first_error:
                retry_major = _extract_browser_major_from_exception(first_error)
                if retry_major and retry_major != local_major:
                    logger.warning(
                        f"[advanced] first start failed; retry with version_main={retry_major}"
                    )
                    kwargs["version_main"] = retry_major
                    self.driver = uc.Chrome(**kwargs)
                else:
                    raise first_error
        finally:
            socket.setdefaulttimeout(old_timeout)

        self.engine_name = "chrome"

    def start(self):
        if _is_driver_alive(self.driver):
            logger.info("[advanced] browser instance already exists; skip start")
            return
        self.driver = None

        if self._try_attach_shared_driver():
            return

        start_ts = time.time()
        try:
            logger.info("[advanced] startup begin")

            # Avoid inheriting broken proxy settings.
            for key in [
                "HTTP_PROXY",
                "HTTPS_PROXY",
                "ALL_PROXY",
                "http_proxy",
                "https_proxy",
                "all_proxy",
            ]:
                os.environ.pop(key, None)
            os.environ.setdefault("NO_PROXY", "*")
            os.environ.setdefault("no_proxy", "*")
            logger.info("[advanced] proxy env cleaned")

            edge_error = None
            if EDGE_BROWSER_AVAILABLE and EDGE_DRIVER_AVAILABLE:
                try:
                    logger.info("[advanced] trying local Edge engine first")
                    self._start_edge()
                except Exception as e:
                    edge_error = e
                    self.driver = None
                    logger.warning(f"[advanced] Edge engine unavailable, fallback to Chrome: {e}")
            elif EDGE_BROWSER_AVAILABLE:
                logger.info("[advanced] local Edge detected but local EdgeDriver missing; skip Edge engine")
            else:
                logger.info("[advanced] local Edge not detected; skip Edge engine")

            if self.driver is None:
                if not UC_AVAILABLE:
                    if edge_error:
                        raise RuntimeError(f"Edge startup failed and Chrome engine unavailable: {edge_error}")
                    raise RuntimeError("no available advanced browser engine")
                self._start_uc_chrome()

            self._store_shared_driver()
            elapsed = time.time() - start_ts
            logger.info(
                f"[advanced] browser engine started successfully, engine={self.engine_name}, elapsed={elapsed:.2f}s"
            )
        except Exception as e:
            elapsed = time.time() - start_ts
            logger.error(f"[advanced] startup failed, elapsed={elapsed:.2f}s: {e}")
            raise

    def fetch_page(self, url, wait_time=3, timeout=30):
        if not self.driver:
            self.start()

        try:
            begin_ts = time.time()
            logger.info(f"[advanced] fetch start -> {url}")
            effective_timeout = max(timeout, 20) if "flaticon.com" in url else timeout
            self._safe_get(url, effective_timeout, context="navigation")

            logger.info(f"[advanced] wait JS render {wait_time}s")
            time.sleep(wait_time)

            html = self.driver.page_source
            if "flaticon.com" in url:
                self._handle_flaticon_wait(url, wait_time, timeout)
                html = self.driver.page_source
                denied = _is_flaticon_access_denied(html)
                links = _flaticon_link_count(self.driver)
                title = ""
                try:
                    title = self.driver.title or ""
                except Exception:
                    pass
                logger.info(
                    f"[advanced] flaticon diagnose: title={title!r}, free_icon_links={links}, access_denied={denied}"
                )

            soup = BeautifulSoup(html, "html.parser")
            logger.info(
                f"[advanced] fetch success, html_len={len(html)}, total_elapsed={time.time() - begin_ts:.2f}s"
            )
            return soup
        except Exception as e:
            logger.error(f"[advanced] fetch failed {url}: {e}")
            return None

    def _safe_get(self, url, timeout, context="navigation"):
        self.driver.set_page_load_timeout(timeout)
        logger.info(f"[advanced] page load timeout={timeout}s")

        nav_ts = time.time()
        try:
            self.driver.get(url)
            logger.info(f"[advanced] {context} done, elapsed={time.time() - nav_ts:.2f}s")
            return True
        except TimeoutException as e:
            logger.warning(
                f"[advanced] {context} timeout after {timeout}s; stop loading and continue: {e}"
            )
            self._stop_loading()
            logger.info(
                f"[advanced] {context} continued with partial DOM, elapsed={time.time() - nav_ts:.2f}s"
            )
            return False
        except WebDriverException as e:
            text = str(e)
            if "Timed out receiving message from renderer" in text:
                logger.warning(
                    f"[advanced] {context} renderer timeout after {timeout}s; stop loading and continue"
                )
                self._stop_loading()
                logger.info(
                    f"[advanced] {context} continued after renderer timeout, elapsed={time.time() - nav_ts:.2f}s"
                )
                return False
            raise

    def _stop_loading(self):
        try:
            self.driver.execute_script("window.stop();")
        except Exception as e:
            logger.info(f"[advanced] window.stop skipped: {e}")

    def _handle_flaticon_wait(self, url, wait_time, timeout):
        # Best-effort cookie accept and lightweight interaction.
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.35);")
            time.sleep(0.8)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
            time.sleep(0.8)
            self.driver.execute_script(
                "var b=document.querySelector('#onetrust-accept-btn-handler'); if(b){b.click();}"
            )
        except Exception:
            pass

        # Wait for either icon links or known denied text markers.
        try:
            WebDriverWait(self.driver, min(timeout, 12)).until(
                lambda d: _flaticon_link_count(d) > 0
                or "access denied" in (d.page_source or "").lower()
            )
        except Exception:
            logger.info("[advanced] flaticon wait timeout; continuing with current page source")

        html = self.driver.page_source
        if _is_flaticon_access_denied(html):
            logger.warning("[advanced] access denied detected, warmup homepage then retry once")
            try:
                self._safe_get("https://www.flaticon.com/", max(timeout, 15), context="flaticon warmup")
                time.sleep(max(2, wait_time))
                try:
                    WebDriverWait(self.driver, 4).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#onetrust-accept-btn-handler"))
                    )
                    self.driver.execute_script(
                        "var b=document.querySelector('#onetrust-accept-btn-handler'); if(b){b.click();}"
                    )
                except Exception:
                    pass
                self._safe_get(url, max(timeout, 20), context="flaticon retry")
                time.sleep(wait_time + 1)
            except Exception as e:
                logger.warning(f"[advanced] flaticon warmup retry failed: {e}")

    def close(self, force=False):
        if not self.driver:
            return

        if self.reuse_browser and not force and self._release_shared_driver():
            return

        driver = self.driver
        self.driver = None
        self._pool_attached = False
        entry = self.__class__._shared_pool.get(self._shared_key)
        if entry and entry.get("driver") is driver:
            self.__class__._shared_pool.pop(self._shared_key, None)

        try:
            driver.quit()
            logger.info(f"[advanced] browser engine closed ({self.engine_name})")
        except Exception as e:
            logger.error(f"[advanced] browser close failed: {e}")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()


def is_advanced_mode_available():
    return bool(ADVANCED_MODE_AVAILABLE)
