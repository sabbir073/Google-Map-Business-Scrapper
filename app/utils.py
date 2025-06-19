# ========================================
# app/utils.py
# ========================================
"""
General-purpose helpers: human-style sleeps, explicit waits, safe scrolling.

Public API
----------
human_delay(min_sec=None, max_sec=None)      -> None
wait_for_element(driver, by, locator, timeout=config.ELEMENT_WAIT_TIMEOUT)
scroll_into_view(driver, element)            -> None
"""

from __future__ import annotations

import logging
import random
import time
from typing import Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Human-style delay
# ---------------------------------------------------------------------------
def human_delay(
    min_sec: float | None = None,
    max_sec: float | None = None,
) -> None:
    """
    Sleep for a random interval *within* ``(min_sec, max_sec)`` seconds.

    If omitted, falls back to the range defined in ``config.DELAY_RANGE``.
    """
    lo, hi = _resolve_range(min_sec, max_sec)
    delay = random.uniform(lo, hi)
    logger.debug("⏳  Human delay: %.2fs", delay)
    time.sleep(delay)


def _resolve_range(
    min_sec: float | None,
    max_sec: float | None,
) -> Tuple[float, float]:
    if min_sec is None or max_sec is None:
        return config.DELAY_RANGE
    if min_sec > max_sec:  # pragma: no cover
        min_sec, max_sec = max_sec, min_sec
    return min_sec, max_sec


# ---------------------------------------------------------------------------
# Element helpers
# ---------------------------------------------------------------------------
def wait_for_element(
    driver: WebDriver,
    by: By,
    locator: str,
    timeout: int = config.ELEMENT_WAIT_TIMEOUT,
):
    """
    Block until a single element *exists* in the DOM and return it.

    • *by* is a Selenium ``By`` locator strategy  
    • *locator* is the corresponding selector string
    """
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, locator)))


def scroll_into_view(driver: WebDriver, element) -> None:
    """Scroll *element* into the viewport (top-aligned)."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", element)
    human_delay(0.4, 0.8)  # tiny pause so content stabilises


__all__ = ["human_delay", "wait_for_element", "scroll_into_view"]
