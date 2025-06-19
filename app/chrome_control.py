# ========================================
# app/chrome_control.py
# ========================================
"""
Spin-up (and tear-down) a *visible* Chrome instance controlled via Selenium 4,
always in English UI.

Public API
----------
launch_chrome() -> selenium.webdriver.Chrome
close_chrome(driver)
"""

from __future__ import annotations

import logging
import random
import shutil
import time
from pathlib import Path
from typing import Final, List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.remote.webdriver import WebDriver

from . import config
from .utils import human_delay

logger = logging.getLogger(__name__)

_FALLBACK_BINARIES: Final[List[Path]] = [
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium-browser"),
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_chrome_binary() -> str | None:
    if config.CHROME_EXECUTABLE:
        return config.CHROME_EXECUTABLE

    for candidate in ("google-chrome", "chromium", "chrome"):
        path = shutil.which(candidate)  # type: ignore[arg-type]
        if path:
            return path

    for p in _FALLBACK_BINARIES:
        if p.exists():
            return str(p)

    logger.warning("⚠️  Could not resolve Chrome binary – letting SeleniumManager choose.")
    return None


def _build_options() -> webdriver.ChromeOptions:
    """Return ChromeOptions with English locale + human-like tweaks."""
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")

    # Randomise window for realism (30 % of runs)
    if random.random() < 0.3:
        w = random.randrange(1100, 1600, 20)
        h = random.randrange(700, 1000, 20)
        opts.add_argument(f"--window-size={w},{h}")

    # Force English UI & Accept-Language header
    opts.add_argument("--lang=en-US")
    opts.add_experimental_option("prefs", {"intl.accept_languages": "en,en_US"})

    # Project-specific extra flags
    for flag in config.CHROME_FLAGS:
        opts.add_argument(flag)

    # Persistent user-data dir (helps skip cookie pop-ups)
    user_data_dir = Path.home() / ".cache" / "maps-scraper-chrome"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    opts.add_argument(f"--user-data-dir={user_data_dir}")

    if (binary := _resolve_chrome_binary()) is not None:
        opts.binary_location = binary

    return opts


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def launch_chrome() -> WebDriver:
    """Launch visible Chrome and return a Selenium WebDriver."""
    logger.info("🚀  Launching Chrome …")
    driver = webdriver.Chrome(service=ChromeService(), options=_build_options())

    driver.implicitly_wait(config.ELEMENT_WAIT_TIMEOUT)
    logger.debug("✓ Chrome launched (session id: %s)", driver.session_id)
    time.sleep(2)  # brief human-style pause
    return driver


def close_chrome(driver: WebDriver) -> None:
    """Gracefully shut down Chrome."""
    try:
        logger.info("✋  Closing Chrome …")
        human_delay()
        driver.quit()
        logger.debug("✓ Chrome closed.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("⚠️  Failed to close Chrome cleanly: %s", exc)
