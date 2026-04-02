#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import re
import socket
import subprocess
import time
import urllib.request

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)
UC_START_TIMEOUT_SECONDS = 45


def _check_availability():
    try:
        import undetected_chromedriver as uc  # noqa: F401
        return True
    except ImportError as e:
        logger.warning(f"undetected-chromedriver is not installed: {e}")
        return False


ADVANCED_MODE_AVAILABLE = _check_availability()


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


class AdvancedCrawler:
    def __init__(self, headless=True, user_data_dir=None):
        self.driver = None
        self.headless = headless
        self.user_data_dir = user_data_dir or os.path.abspath(
            os.path.join(os.getcwd(), "data", "browser_profile")
        )

        if not ADVANCED_MODE_AVAILABLE:
            raise ImportError(
                "advanced mode requires undetected-chromedriver\n"
                "run: pip install undetected-chromedriver"
            )

    def start(self):
        if self.driver:
            logger.info("[advanced] browser instance already exists; skip start")
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

            import undetected_chromedriver as uc

            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument("--headless=new")
            options.page_load_strategy = "eager"
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--start-maximized")
            options.add_argument("--window-size=1440,2200")
            options.add_argument("--lang=en-US")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            os.makedirs(self.user_data_dir, exist_ok=True)
            options.add_argument(f"--user-data-dir={self.user_data_dir}")

            logger.info(
                f"[advanced] chrome options ready, headless={self.headless}, page_load_strategy=eager"
            )
            logger.info("[advanced] creating Chrome instance (first run may download driver)")

            # Quick preflight: uc may need to download a matching driver.
            reach_google = _can_reach("https://googlechromelabs.github.io/", timeout=5)
            reach_github = _can_reach("https://github.com/", timeout=5)
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

            try:
                old_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(UC_START_TIMEOUT_SECONDS)
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

            elapsed = time.time() - start_ts
            logger.info(f"[advanced] browser engine started successfully, elapsed={elapsed:.2f}s")
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

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("[advanced] browser engine closed")
            except Exception as e:
                logger.error(f"[advanced] browser close failed: {e}")
            finally:
                self.driver = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()


def is_advanced_mode_available():
    try:
        import undetected_chromedriver as uc  # noqa: F401
        return True
    except ImportError:
        return False
